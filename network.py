'''Module for network clients'''
# !/usr/bin/env python3

import socket
import json
import time
import datetime
import traceback
import threading
import logging
import db_helper

from copy import deepcopy


PORT = 9090
EMPTY = ' '
logger = logging.getLogger(__name__)


class ChatClient:
    def __init__(self, server_host=None):
        self._server_host = server_host
        self._recv_sock = self._create_recv_socket()
        self._host = self._get_ip_addr()
        self._connected = set()
        self._db = db_helper.DBHelper()

        self.user_id_assigned = False

        self._db.try_create_database()
        self._init_user_data()

        self.host2user_id = dict()
        self.user_id2host = dict()

        self._connected.add(self._host)

    def start(self):
        threading.Thread(target=self._handle_recv).start()
        if self._server_host is not None:
            self._get_connected()
            while not self.user_id_assigned:
                pass
            self._handle_username()
            self._connect()
        else:
            self._handle_username()
            self.host2user_id[self._host] = self.user_id
            self.user_id2host[self.user_id] = self._host

    def _init_user_data(self):
        user = self._db.get_current_user()
        if user is not None:
            self.user_id = user[0]
            self.username = user[1]
        else:
            self.username = ''
            self.user_id = 1

    def specify_username(self, username):
        self.username = username

    def _handle_username(self):
        self._db.change_username(user_id=self.user_id,
                                 new_username=self.username)
        self._db.save_user(username=self.username, user_id=self.user_id)
        self._db.save_current_user(username=self.username, user_id=self.user_id)

        self.host2user_id[self._host] = self.user_id
        self.user_id2host[self.user_id] = self._host

    def _create_send_socket(self):
        send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return send

    def _create_recv_socket(self):
        recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        recv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        recv.bind(('', PORT))
        recv.listen(10)
        return recv

    def _get_connected(self):
        logger.info('[*] Getting connected hosts')
        data = self.create_data(host=self._host, action='_get_connected')
        self.send_msg(host=self._server_host, msg=data)

    def _connect(self):
        logger.info('[*] Connecting to: %s' % str(self._server_host))
        data = self.create_data(host=self._host, action='connect',
                                username=self.username, user_id=self.user_id)
        self.send_msg(host=self._server_host, msg=data)

    def disconnect(self):
        logger.info('[*] Disconnecting: %s' % str(self._host))
        data = self.create_data(host=self._host, action='disconnect',
                                username=self.username)
        for host in self._connected:
            self.send_msg(host=host, msg=data)

    def create_data(self, msg='', host='', action='', is_server=0,
                    username='', user_id=-1, json_format=True,
                    room_name='', room_creator = '', new_room_user = '',
                    remove_room='No'):
        data = {
            'message': msg,
            'host': host,
            'is_server': is_server,
            'action': action,
            'username': username,
            'user_id': user_id
        }
        if room_name != '':
            data['room'] = room_name
            data['room_creator'] = room_creator
            data['remove_room'] = remove_room
            if new_room_user != '':
                data['room_user'] = new_room_user
        if json_format:
            return json.dumps(data)
        return data

    def send_msg(self, host, msg):
        try:
            send_sock = self._create_send_socket()
            send_sock.connect(host)
            send_sock.sendall(bytes(msg, 'utf-8'))
        except (Exception, socket.error) as e:
            logger.error('[-] Connection failed: %s' % str(host))
            traceback.print_exc()
        finally:
            send_sock.close()

    def _handle_recv(self):
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
                self._parse_data(data.decode('utf-8'))
            finally:
                conn.close()

    def _parse_data(self, json_data):
        data = json.loads(json_data)
        # We have request for connection. Then we should send this ip to all
        # host in our network
        if data['action'] == 'connect':
            self._handle_host_action(data=data, action_type='connect',
                                    message='[+] Adding host: ')

        # The same with disconnection
        if data['action'] == 'disconnect':
            self._handle_host_action(data=data, action_type='disconnect',
                                    message='[+] Removing host: ')

        if data['action'] == '_get_connected':
            self._send_connected(host=data['host'])

        # TODO save messages in database or file
        if data['message'] != '':
            cur_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            # If action connected with room
            if 'room' in data:
                # User has deleted the room
                if data['remove_room'] != 'No':
                    self._db.remove_user_from_room(data['username'],
                                                   data['room'])
                    return

                # Else message sended in the room
                # then room must be created if not exists
                if not self._db.room_exists(data['room']):
                    self._db.try_create_room(room_name=data['room'],
                                             creator_name=data['room_creator'])
                    self._db.add_user2room(username=self.username,
                                           room_name=data['room'])
                    if 'room_user' in data:
                        self._db.add_user2room(username=data['room_user'],
                                               room_name=data['room'])
                    if data['message'] == EMPTY:
                        return
                self._db.save_room_message(src=data['user_id'],
                                           message=data['message'],
                                           time=cur_time,room_name=data['room'])
                return
            self._db.save_message(src=data['user_id'], dst=self.user_id,
                                  message=data['message'], time=cur_time)

        if 'connected' in data:
            logger.info('[+] Updating tables of connected hosts')
            self._update_connected(data)

        if 'new_username' in data:
            self._update_username(data)

    def _update_connected(self, data):
        for host_data in data['connected']:
            host = tuple(host_data[0])
            user_id = int(host_data[1])
            username = host_data[2]

            logger.info('[+] Connected host: {0}, username: {1}, user_id: {2}'
                        .format(host, username, user_id))

            self.host2user_id[host] = user_id
            self.user_id2host[user_id] = host

            self._connected.add(host)
            self._db.save_user(user_id=user_id,
                               username=username)
        self.user_id = len(self._connected)
        self.user_id_assigned = True
        logger.info('[*] Current user id: %s' % self.user_id)
        logger.info('[*] Connected hosts: %s' % str(self._connected))

    def _update_username(self, data):
        username = data['username']
        new_username = data['new_username']
        user_id = data['user_id']

        logger.info('[+] {0} changed username to {1}'
                    .format(username, new_username))
        self._db.change_username(user_id, new_username)

    def _handle_host_action(self, data, action_type, message):
        host = data['host']
        username = data['username']
        user_id = data['user_id']

        if host[0] == self._host[0]:
            return
        host = tuple(host)
        logger.info('[+] Updating tables of connected hosts')
        # Updating table of connected hosts for each host in network
        if data['is_server'] == '0':
            data['is_server'] = '1'
            # Update table for existent hosts
            for conn in self._connected:
                self.send_msg(host=conn, msg=data)

        if host not in self._connected:
            logger.info(message + str(host) + 'user id: %s' % user_id)
            if action_type == 'connect':
                self.user_id2host[user_id] = host
                self.host2user_id[host] = user_id
                self._connected.add(host)
                self._db.save_user(username=username, user_id=user_id)

        if action_type == 'disconnect':
            self._connected.remove(host)
            self.host2user_id.pop(host, None)
            self.user_id2host.pop(user_id, None)
            return

    def _send_connected(self, host):
        host = tuple(host)
        tun_data = self.create_data(json_format=False)
        tun_data['connected'] = [(host, user_id, self._db.get_username(user_id)) \
                                  for host, user_id in self.host2user_id.items()]
        logger.info('[+] Sending connected hosts to: %s' % str(host))
        self.send_msg(host=host, msg=json.dumps(tun_data))

    def _get_ip_addr(self):
        global PORT
        ip_lt1 = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2]
                  if not ip.startswith("127.")][:1]
        ip_lt2 = [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close())
                   for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]]
                  [0][1]]
        for ip in [ip_lt1, ip_lt2]:
            if ip and (ip[0].startswith('192.') or ip[0].startswith('10.')):
                return (ip[0], PORT)

    # TODO MOVE ALL CODE BELOW INTO SEPARATE MODULE!!!
    def get_history(self, dst, count, room=False):
        if not room:
            return self._db.get_history(self.user_id, dst, count)
        else:
            return self._db.get_room_history(self.user_id, dst, count)

    def get_username(self, user_id):
        return self._db.get_username(user_id)

    def get_user_id(self, username):
        return self._db.get_user_id(username)

    def save_message(self, user_id, message):
        cur_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self._db.save_message(self.user_id, user_id, message, cur_time)

    def create_room(self, room_name):
        return self._db.try_create_room(room_name=room_name,
                                        creator_name=self.username)

    def change_username(self, new_username):
        data = self.create_data(username=self.username, user_id=self.user_id,
                                json_format=False)
        data['new_username'] = new_username
        data_dump = json.dumps(data)
        for host in self._connected:
            if host != self._host:
                self.send_msg(host=host, msg=data_dump)
        self.username = new_username
        self._db.change_username(user_id=self.user_id,
                                 new_username=new_username)
        self._db.save_current_user(user_id=self.user_id, username=self.username)

    def user_exists(self, username):
        return self._db.user_exists(username)

    def room_exists(self, room_name):
        return self._db.room_exists(room_name)

    def get_user_rooms(self):
        return self._db.get_user_rooms(self.username)

    def get_room_id(self, room_name):
        return self._db.get_room_id(room_name)

    def get_users_by_room(self, room_name, room_id=None):
        return self._db.get_users_by_room(room_name, room_id)

    def remove_room(self, room_name):
        self._db.remove_room(room_name)

    def get_room_creator(self, room_name):
        return self._db.get_room_creator(room_name)

    def add_user2room(self, username, room_name):
        self._db.add_user2room(username=username, room_name=room_name)

if __name__ == '__main__':
    pass
    # client = ChatClient(('192.168.0.101', PORT))
    # client.start()
