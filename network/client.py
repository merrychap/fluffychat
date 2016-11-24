'''Module for network clients'''
# !/usr/bin/env python3

from copy import deepcopy
from multiprocessing import Queue

import os
import base64
import select
import socket
import urllib
import json
import time
import datetime
import traceback
import threading
import logging

import netifaces as nf
import database.db_helper as db_helper


PORT = 9090
EMPTY = ' '
RESTART_CHAT = False
logger = logging.getLogger(__name__)

interfaces = ['eth', 'wlan', 'en', 'wl']
connection_established = False
lock = threading.Lock()

received_file_message = ('User sended you a file. Do you want to save it?'
                         '(Yes\\No)')


# Now it isn't used, but it should work in the future
# class NetworkConnectionChecker(threading.Thread):
#     '''
#     Class for updating online data of chat client depending on
#     current network connection
#     '''
#
#     def __init__(self, client):
#         self.client = client
#
#     def run(self):
#         while True:
#             try:
#                 response = urllib.urlopen('google.com', timeout=1)
#                 with lock:
#                     connection_established = True
#             except urllib.URLError as e:
#                 with lock:
#                     connection_established = False


class ChatClient:
    '''
    Class for network part of the chat
    '''

    def __init__(self, server_host=None):
        self._init_data(server_host)
        self.add_thread(self.check_connection)

    def _init_data(self, server_host):
        self.user_id2filename = dict()

        self.user_id = -1

        self._server_host = server_host
        self._recv_sock = self._create_recv_socket()
        self._host = self._get_ip_addr()
        self._connected = set()
        self._db = db_helper.DBHelper()

        self.inner_threads = []

        self.user_id_assigned = False
        self._handle_recv_data = True

        self._db.try_create_database()
        self._init_user_data()

        self.host2user_id = dict()
        self.user_id2host = dict()

        self._connected.add(self._host)

    def restart(self, server_host):
        self._init_data(server_host)
        return self.start()

    def start(self):
        self._host = self._get_host_ip()
        if self._host is None:
            return False
        print(self._host)

        self.add_thread(self._handle_recv)

        if self._server_host is not None:
            if not self._get_connected():
                return False
            while not self.user_id_assigned:
                pass
            self._handle_username()
            self._connect()
        else:
            self._handle_username()
            self.host2user_id[self._host] = self.user_id
            self.user_id2host[self.user_id] = self._host
        return True

    def disconnect(self):
        logger.info('[*] Disconnecting: %s' % str(self._host))

        self._handle_recv_data = False
        for thread in self.inner_threads:
            thread.join()

        data = self.create_data(host=self._host, action='disconnect',
                                username=self.username, user_id=self.user_id)
        for host in self._connected:
            self.send_msg(host=host, msg=data)

    def add_thread(self, target):
        thread = threading.Thread(target=target)
        self.inner_threads.append(thread)
        thread.start()

    def get_connected(self):
        return self._connected

    def _get_host_ip(self):
        ip = self._get_ip_addr()
        return ip if self._host is None else self._host

    def _init_user_data(self):
        user = self._db.get_current_user()
        if user is not None:
            self.user_id = user[0]
            self.username = user[1]
            self.root_path = user[2]
        else:
            self.user_id = -1
            self.username = ''
            self.root_path = ''
            if self._server_host is None:
                self.user_id = 1

    def specify_username(self, username):
        self.username = username

    def specify_root_path(self, root_path):
        if not os.path.isdir(root_path):
            print('\n[-] This is not a directory\n')
            return False
        self.root_path = root_path
        return True

    def _handle_root_path(self):
        self.root_path = self._db.get_root_path()

    def _handle_username(self):
        self._db.change_username(user_id=self.user_id,
                                 new_username=self.username)
        self._db.save_user(username=self.username, user_id=self.user_id)
        self._db.save_current_user(username=self.username, user_id=self.user_id,
                                   root_path=self.root_path)

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
        # recv.setblocking(0)
        return recv

    def _get_connected(self):
        logger.info('[*] Getting connected hosts')
        data = self.create_data(host=self._host, action='_get_connected',
                                visibility=False)
        return self.send_msg(host=self._server_host, msg=data)

    def _connect(self, serv_host=None):
        logger.info('[*] Connecting to: %s' % str(self._server_host))
        data = self.create_data(host=self._host, action='connect',
                                username=self.username, user_id=self.user_id)
        self.send_msg(host=self._server_host, msg=data)

    def create_file_data(self, file_location, filename, username='', user_id=-1,
                         json_format=True):
        if user_id == -1:
            user_id = self._db.get_user_id(username)
        try:
            with open(file_location, 'rb') as _file:
                file_data = base64.b64encode(_file.read())
                data = {
                    'file': True,
                    'filename': filename,
                    'file_data': file_data.decode('utf-8'),
                    'username': username,
                    'user_id': user_id
                }
                return json.dumps(data) if json_format else data
        except FileNotFoundError as e:
            return None

    def create_data(self, msg='', host='', action='', is_server=0,
                    username='', user_id=-1, json_format=True,
                    room_name='', room_creator = '', new_room_user = '',
                    remove_room='No', users_in_room=[], visibility=True):
        data = {
            'message': msg,
            'host': host,
            'is_server': is_server,
            'action': action,
            'username': username,
            'user_id': user_id,
        }

        if visibility:
            data['visible'] = self._db.get_visibility(user_id)

        if room_name != '':
            data['room'] = room_name
            data['room_creator'] = room_creator
            data['remove_room'] = remove_room
            if new_room_user != '':
                data['room_user'] = new_room_user
            if users_in_room != []:
                data['users_in_room'] = users_in_room
        return json.dumps(data) if json_format else data

    def send_msg(self, host, msg):
        try:
            send_sock = self._create_send_socket()
            send_sock.connect(host)
            send_sock.sendall(bytes(msg, 'utf-8'))
            return True
        except (Exception, socket.error) as e:
            logger.error('[-] Connection failed: %s' % str(host))
            return False
        finally:
            send_sock.close()

    def _handle_recv(self):
        inputs = [self._recv_sock]
        outputs = []
        message_queues = {}

        while self._handle_recv_data:
            # TODO ADD TIMEOUT TO THE SELECT SECTION
            # THIS
            # IS
            # IMPORTANT
            try:
                readable, writable, exceptional = select.select(inputs, outputs,
                                                                inputs)
            except (Exception, select.error):
                if not self._handle_recv_data:
                    break
            for sock in readable:
                if sock is self._recv_sock:
                    # A "readable" server socket is ready to accept a connection
                    conn, addr = self._recv_sock.accept()
                    conn.setblocking(0)
                    inputs.append(conn)
                    # Give the connection a queue for data we want to send
                    message_queues[conn] = b''
                    logger.info('[+] Connection from: %s' % str(addr))
                else:
                    data = sock.recv(1024)
                    if data:
                        # A readable client socket has data
                        message_queues[sock] += data
                        # Add output channel for response
                        if sock not in outputs:
                            outputs.append(sock)
                    else:
                        # Interpret empty result as closed connection
                        if sock in outputs:
                            outputs.remove(sock)
                        inputs.remove(sock)
                        sock.close()
                        message_queues[sock] = message_queues[sock].decode('utf-8')
                        logger.info('[+] Recieved: %s' % message_queues[sock])
                        self._parse_data(message_queues[sock])
                        del message_queues[sock]
        print('Handling thread is ended')

    def _update_visibility(self, data):
        self._db.set_visibility(data['user_id'], 1 if not ('visible' in data)\
                                else data['visible'])

    def _save_file(self, filename, _file):
        with open(self.root_path + filename, 'wb') as new_file:
            new_file.write(base64.b64decode(_file))

    def remove_file(self, user_id):
        os.remove(self.root_path + self.user_id2filename[user_id])
        del self.user_id2filename[user_id]

    def _handle_file_receiving(self, data, cur_time):
        global received_file_message

        self._save_file(data['filename'], data['file_data'])
        self._db.save_message(src=data['user_id'], dst=self.user_id,
                              message=received_file_message, time=cur_time)
        self.user_id2filename[data['user_id']] = data['filename']

    def _parse_data(self, json_data, conn=None):
        data = json.loads(json_data)
        cur_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        # If this data is associated with file then handle only
        # in this case
        if 'file' in data:
            self._handle_file_receiving(data, cur_time)
            return

        # Updates visibility of connected user
        self._update_visibility(data)

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
                    for user in data['users_in_room']:
                        self._db.add_user2room(username=self._db.get_username(user),
                                               room_name=data['room'])
                    if data['message'] == EMPTY:
                        return

                if 'room_user' in data:
                    self._db.add_user2room(username=data['room_user'],
                                           room_name=data['room'])
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
            visibility = host_data[3]

            logger.info('[+] Connected host: {0}, username: {1}, user_id: {2}'
                        .format(host, username, user_id))

            self.host2user_id[host] = user_id
            self.user_id2host[user_id] = host

            self._connected.add(host)
            self._db.save_user(user_id=user_id,
                               username=username,
                               visibility=visibility)
        # print(self.user_id)
        if self.user_id == -1:
            self.user_id = self._db.get_last_user_id() + 1
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

        if action_type == 'disconnect':
            try:
                self._connected.remove(host)
                self.host2user_id.pop(host, None)
                self.user_id2host.pop(user_id, None)
            except KeyError:
                pass
            finally:
                return

        logger.info('[+] Updating tables of connected hosts')
        # Updating table of connected hosts for each host in network
        if data['is_server'] == 0:
            data['is_server'] = 1
            # Update table for existent hosts
            for conn in self._connected:
                self.send_msg(host=conn, msg=json.dumps(data))

        if host not in self._connected:
            logger.info(message + str(host) + 'user id: %s' % user_id)
            if action_type == 'connect':
                self.user_id2host[user_id] = host
                self.host2user_id[host] = user_id
                self._connected.add(host)
                self._db.save_user(username=username, user_id=user_id)

    def _send_connected(self, host):
        host = tuple(host)
        tun_data = self.create_data(json_format=False, visibility=False)
        _connected = []
        for _host, user_id in self.host2user_id.items():
            _connected.append((_host, user_id, self._db.get_username(user_id),
                               self._db.get_visibility(user_id)))
        tun_data['connected'] = _connected
        logger.info('[+] Sending connected hosts to: %s' % str(host))
        self.send_msg(host=host, msg=json.dumps(tun_data))

    def is_connection_established(self):
        return self._get_ip_addr() is not None

    def _get_ip_addr(self):
        for gl_if in nf.interfaces():
            for lc_if in interfaces:
                if gl_if.startswith(lc_if):
                    try:
                        return (nf.ifaddresses(gl_if)[2][0]['addr'], PORT)
                    except KeyError:
                        pass

    def try2connect(self):
        '''
        It iterates through all known hosts and tryies
        to establish connection with one of them
        '''

        online_hosts = self.get_connected()
        self.disconnect()
        for host in online_hosts:
            if self.restart(host):
                return True
        return False

    def check_connection(self):
        '''
        This method contains logic of updating connection
        between online hosts in the chat.

        If connection was lost then this class tryies to establish
        connection with some host in the chat. And if this impossible
        then it stops chat client and run it again.
        '''
        global RESTART_CHAT

        while self._handle_recv_data:
            if not self.is_connection_established():
                if not self.try2connect():
                    RESTART_CHAT = True
                else:
                    RESTART_CHAT = False

if __name__ == '__main__':
    pass
    # client = ChatClient(('192.168.0.101', PORT))
    # client.start()
