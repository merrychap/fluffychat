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


class Client:
    def __init__(self, server_ip=None, *args, **kwargs):
        self.server_ip = server_ip
        self.recv_sock = self.create_recv_socket()
        self.ip = self.get_ip_addr()
        self.connected = set()

        self.current_msg = ''
        self.prev_msg = ''

        self.connected.add(self.ip)

    def start(self):
        threading.Thread(target=self.handle_recv).start()
        if self.server_ip is not None:
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
        logger.info('[*] Connecting to: %s' % str(self.server_ip))
        data = self.create_data(conn_hosts=[self.ip])
        self.send_msg(host=self.server_ip, msg=data)

    def disconnect(self):
        logger.info('[*] Disconnecting: %s' % self.ip)
        data = self.create_data(dconn_hosts=[self.ip])
        self.send_msg(host=self.server_ip, msg=data)

    def create_data(self, msg='', conn_hosts=[], dconn_hosts=[], is_server=0,
                    src='', dst=''):
        data = {
            'message': msg,
            'conn_hosts': conn_hosts,
            'is_server': is_server,
            'dconn_hosts': dconn_hosts,
            'src': src,
            'dst': dst
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
        if data['conn_hosts'] is not None:
            self.handle_conn_hosts(data=data, action_type='conn_hosts',
                                   message='[+] Adding host: ')

        # The same with disconnection
        if data['dconn_hosts'] is not None:
            self.handle_conn_hosts(data=data, action_type='dconn_hosts',
                                   message='[+] Removing host: ')
        if data['message'] != '':
            self.current_msg = '%s: %s' % (data['src'], data['message'])

        if 'connected' in data:
            logger.info('[*] Updating tables of connected hosts')
            for host in data['connected']:
                self.connected.add(tuple(host))

    def handle_conn_hosts(self, data, action_type, message):
        for host in data[action_type]:
            if host[0] == self.ip[0]:
                continue
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
                if action_type == 'conn_hosts':
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
    client = Client(('192.168.0.102', PORT))
    client.start()
