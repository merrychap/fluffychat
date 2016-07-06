'''Module for network clients'''
#!/usr/bin/env python3

import socket
import json
import traceback
import threading
import logging

from copy import deepcopy


PORT = 9090
LOG_FILE = 'network.log'


def create_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.DEBUG)

    handler = logging.FileHandler(LOG_FILE)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(('%(asctime)s-%(levelname)s-%(message)s'))
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


logger = create_logger()


class BaseClient:
    def __init__(self, username, server_host=None):
        self.server_host = server_host
        self.recv_sock = self.create_recv_socket()
        self.host = self.get_ip_addr()
        self.connected = set()
        self.username = username

        self.current_msg = ''
        self.prev_msg = ''

        self.connected.add(self.host)

    def start(self):
        threading.Thread(target=self.handle_recv).start()
        if self.server_host is not None:
            self.connect()

    def create_send_socket(self):
        send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return send

    def create_recv_socket(self):
        recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        recv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        recv.bind(('', PORT))
        recv.listen(10)
        return recv

    def connect(self):
        logger.info('[*] Connecting to: %s' % str(self.server_host))
        data = self.create_data(host=self.host, action='connect',
                                username=self.username)
        self.send_msg(host=self.server_host, msg=data)

    def disconnect(self):
        logger.info('[*] Disconnecting: %s' % self.host)
        data = self.create_data(host=self.host, action='disconnect')
        self.send_msg(host=self.server_host, msg=data)

    def create_data(self, msg='', host='', action='', is_server=0, username=''):
        data = {
            'message': msg,
            'host': host,
            'is_server': is_server,
            'action': action,
            'username': username
        }
        return json.dumps(data)

    def send_msg(self, host, msg):
        try:
            send_sock = self.create_send_socket()
            send_sock.connect(host)
            send_sock.sendall(bytes(msg, 'utf-8'))
        except Exception as e:
            logger.error('[-] Connection failed: %s' % str(host))
            traceback.print_exc()
        finally:
            send_sock.close()

    def handle_recv(self):
        while True:
            logger.info('[*] Waiting for connection')
            conn, addr = self.recv_sock.accept()
            try:
                logger.info('[+] Connection from: %s' % str(addr))
                data = bytes()
                while True:
                    recieved_data = conn.recv(1024)
                    if not recieved_data:
                        logger.info('[-] No more data from: %s' % str(addr))
                        break
                    data += recieved_data
                logger.info('[+] Recieved: %s' % data)
                self.parse_data(data.decode('utf-8'))
            finally:
                conn.close()

    def parse_data(self, json_data):
        data = json.loads(json_data)
        # We have request for connection. Then we should send this ip to all
        # host in our network
        if data['action'] == 'connect':
            self.handle_host_action(data=data, action_type='connect',
                                   message='[+] Adding host: ')

        # The same with disconnection
        if data['action'] == 'disconnect':
            self.handle_host_action(data=data, action_type='disconnect',
                                   message='[+] Removing host: ')
        if data['message'] != '':
            self.current_msg = '%s: %s' % (data['src'], data['message'])

        if 'connected' in data:
            logger.info('[*] Updating tables of connected hosts')
            for host in data['connected']:
                self.connected.add(tuple(host))

    def handle_host_action(self, data, action_type, message):
        host = data['host']
        if host[0] == self.host[0]:
            return
        host = tuple(host)
        logger.info('[*] Updating tables of connected hosts')
        # Updating table of connected hosts for each host in network
        if data['is_server'] == '0':
            data['is_server'] = '1'
            # Update table for existent hosts
            for conn in self.connected:
                self.send_msg(host=conn, msg=data)

        if host not in self.connected:
            logger.info(message + str(host))
            if action_type == 'connect':
                self.connected.add(host)
            else:
                self.connected.remove(host)
        # Send table to connected host
        tun_data = deepcopy(data)
        tun_data['connected'] = list(self.connected)
        self.send_msg(host=host, msg=json.dumps(tun_data))

    def get_ip_addr(self):
        global PORT
        ip_lt1 = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2]
                  if not ip.startswith("127.")][:1]
        ip_lt2 = [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close())
                   for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]]
                  [0][1]]
        for ip in [ip_lt1, ip_lt2]:
            if ip:
                return (ip[0], PORT)

if __name__ == '__main__':
    client = BaseClient(server_host=('192.168.0.12', 9090), username='lalka')
    client.start()
