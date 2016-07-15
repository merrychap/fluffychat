'''Module for network clients'''
# !/usr/bin/env python3

import socket
import json
import time
import traceback
import threading
import logging
import db_helper

from copy import deepcopy


PORT = 9090
logger = logging.getLogger(__name__)


class ChatClient:
    def __init__(self, server_host=None):
        self._server_host = server_host
        self._recv_sock = self.create_recv_socket()
        self._host = self.get_ip_addr()
        self._connected = set()
        self._db = db_helper.DBHelper()

        self.username = ''
        self.host2username = dict()
        self.username2host = dict()

        self._db.try_create_database()

        self._connected.add(self._host)

    def start(self):
        threading.Thread(target=self.handle_recv).start()
        if self._server_host is not None:
            self.connect()

    def specify_username(self, username):
        self.username = username
        self._db.save_user(self.username)
        self.host2username[self._host] = self.username
        self.username2host[self.username] = self._host

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
        logger.info('[*] Connecting to: %s' % str(self._server_host))
        data = self.create_data(host=self._host, action='connect',
                                username=self.username)
        self.send_msg(host=self._server_host, msg=data)

    def disconnect(self):
        logger.info('[*] Disconnecting: %s' % str(self._host))
        data = self.create_data(host=self._host, action='disconnect',
                                username=self.username)
        self.send_msg(host=next(iter(self._connected)), msg=data)

    def create_data(self, msg='', host='', action='', is_server=0,
                    username=''):
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
        except (Exception, socket.error) as e:
            logger.error('[-] Connection failed: %s' % str(host))
            traceback.print_exc()
        finally:
            send_sock.close()

    def handle_recv(self):
        while True:
            logger.info('[*] Waiting for connection')
            conn, addr = self._recv_sock.accept()
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
        # TODO save messages in database or file
        if data['message'] != '':
            self._db.save_message(src=data['username'], dst=self.username,
                                  message=data['message'])

        if 'connected' in data:
            logger.info('[*] Updating tables of connected hosts')
            for host_data in data['connected']:
                host = tuple(host_data[0])
                self.host2username[host] = str(host_data[1])
                self.username2host[str(host_data[1])] = host

                self._connected.add(host)
                self._db.save_user(self.host2username[host])

    def handle_host_action(self, data, action_type, message):
        host = data['host']
        username = data['username']
        if host[0] == self._host[0]:
            return
        host = tuple(host)
        logger.info('[*] Updating tables of connected hosts')
        # Updating table of connected hosts for each host in network
        if data['is_server'] == '0':
            data['is_server'] = '1'
            # Update table for existent hosts
            for conn in self._connected:
                self.send_msg(host=conn, msg=data)

        if host not in self._connected:
            logger.info(message + str(host))
            if action_type == 'connect':
                self.username2host[data['username']] = host
                self.host2username[host] = data['username']
                self._connected.add(host)
                self._db.save_user(data['username'])

        if action_type == 'disconnect':
            self._connected.remove(host)
            self.host2username.pop(host, None)
            self.username2host.pop(username, None)
            return
        # Send table to connected host
        tun_data = deepcopy(data)
        tun_data['connected'] = [(host, name) for host, name in
                                 self.host2username.items()]
        self.send_msg(host=host, msg=json.dumps(tun_data))

    def get_ip_addr(self):
        global PORT
        ip_lt1 = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2]
                  if not ip.startswith("127.")][:1]
        ip_lt2 = [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close())
                   for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]]
                  [0][1]]
        for ip in [ip_lt1, ip_lt2]:
            if ip and ip[0].startswith('192.'):
                return (ip[0], PORT)

    def get_history(self, username, count):
        return self._db.get_history(self.username, username, count)

    def get_username(self, user_id):
        return self._db.get_username(user_id)

    def save_message(self, username, message):
        self._db.save_message(self.username, username, message)
