''' Module for network functionality '''

# !/usr/bin/env python3

import os
import base64
import select
import socket
import json
import datetime
import traceback
import threading
import logging

import netifaces as nf
import database.db_helper as db_helper

from opt.appearance import printc

from .encryption import Encryptor


EMPTY = ' '
RESTART_CHAT = False
logger = logging.getLogger(__name__)

interfaces = ['eth', 'wlan', 'en', 'wl']
connection_established = False
lock = threading.Lock()

file_received = set()
received_file_message = ('User sended you a file. Do you want to save it?'
                         '(Yes\\No)')


class ChatClient:
    '''
    Class for network part of the chat
    '''

    def __init__(self, r_port, dis_enc=False, server_host=None):
        self.r_port = r_port
        self._recv_sock = self._create_recv_socket()
        self.encryptor = Encryptor(self)
        self._dis_enc = dis_enc
        self.host2user_id = dict()
        self.user_id2host = dict()

        self._init_data(server_host)

    def _init_data(self, server_host):
        self.user_id2filename = dict()

        self.user_id = -1

        self._server_host = server_host
        self._host = self._get_ip_addr()
        self._connected = set()
        self._db = db_helper.DBHelper()

        self.inner_threads = {}

        self.user_id_assigned = False
        self._handle_recv_data = True

        self._db.try_create_database()
        self._init_user_data()

        self._connected.add(self._host)

    def restart(self, server_host):
        self._init_data(server_host)
        return self.start()

    def start(self):
        self._host = self._get_host_ip()
        if self._host is None:
            return False
        printc(self._host)

        self.add_thread(self._handle_recv)
        self.add_thread(self.check_connection)

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

        # Add self public key in keys dictionary
        self.encryptor.add_pubkey(self.user_id, None, _self=True)

        return True

    def disconnect(self, exit=False):
        logger.info('[*] Disconnecting: %s' % str(self._host))

        self._handle_recv_data = False
        for name, thread in self.inner_threads.items():
            try:
                if not exit and name == self.check_connection.__name__:
                    continue
                thread.join()
            except (KeyboardInterrupt):
                pass
        data = self.create_data(host=self._host, action='disconnect',
                                username=self.username, user_id=self.user_id)
        for host in self._connected:
            self.send_msg(host=host, msg=data)
        if exit:
            self._recv_sock.close()

    def add_thread(self, target):
        thread = threading.Thread(target=target)
        self.inner_threads[target.__name__] = thread
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
            printc('\n<lred>[-]</lred> This is not a directory\n')
            return False
        root_path = os.path.join(root_path, '')
        self.root_path = root_path
        return True

    def _handle_root_path(self):
        self.root_path = self._db.get_root_path()

    def _handle_username(self):
        self._db.change_username(user_id=self.user_id,
                                 new_username=self.username)
        self._db.save_user(username=self.username, user_id=self.user_id)
        self._db.save_current_user(username=self.username,
                                   user_id=self.user_id,
                                   root_path=self.root_path)

        self.host2user_id[self._host] = self.user_id
        self.user_id2host[self.user_id] = self._host

    def _create_send_socket(self):
        send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        send.settimeout(3)
        return send

    def _create_recv_socket(self):
        recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        recv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        recv.bind(('', self.r_port))
        recv.listen(10)
        recv.setblocking(0)
        return recv

    def _get_connected(self):
        logger.info('[*] Getting connected hosts')
        data = self.create_data(host=self._host, action='_get_connected',
                                visibility=False)
        return self.send_msg(host=self._server_host, msg=data,
                             pubkey_exchange=True)

    def _connect(self, serv_host=None):
        logger.info('[*] Connecting to: %s' % str(self._server_host))
        data = self.create_data(host=self._host, action='connect',
                                username=self.username, user_id=self.user_id)
        self.send_msg(host=self._server_host, msg=data, pubkey_exchange=True)

    def create_file_data(self, file_location, filename, username='',
                         user_id=-1, room_name='', json_format=True):
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
                if room_name != '':
                    data['room'] = room_name
                return json.dumps(data) if json_format else data
        except FileNotFoundError as e:
            return None

    def create_data(self, msg='', host='', action='', is_server=0,
                    username='', user_id=-1, json_format=True,
                    room_name='', room_creator='', new_room_user='',
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
            try:
                data['visible'] = self._db.get_visibility(user_id)
            except TypeError:
                data['visible'] = True

        if room_name != '':
            data['room'] = room_name
            data['room_creator'] = room_creator
            data['remove_room'] = remove_room
            if new_room_user != '':
                data['room_user'] = new_room_user
            if users_in_room != []:
                data['users_in_room'] = users_in_room
        return json.dumps(data) if json_format else data

    def _pubkey_wrapper(self, msg):
        try:
            data = json.loads(msg)
        except TypeError as e:
            data = msg
        data['pubkey'] = self.encryptor.pubkey.exportKey().decode('utf-8')
        data['sender_id'] = self.user_id
        data['dis_enc'] = self._dis_enc
        return json.dumps(data)

    def send_msg(self, host, msg, pubkey_exchange=False, ping=False):
        '''
        Send message to a host in the chat. First of all happens
        message encryption and then message sends. If encryption is
        disabled then encryptor function encrypt returns msg itself

        Args:
            host (tuple) Tuple of IP and port of a host
            msg (str) Message that is sended
            pubkey_exchange (bool) If this message is public keys exchanging
            ping (bool) True if this is ping message else False

        Return:
            bool True if transfer was successful else False
        '''

        try:
            send_sock = self._create_send_socket()
            send_sock.connect(host)

            if pubkey_exchange:
                n_msg = self._pubkey_wrapper(msg)
            else:
                user_id = self.host2user_id[host]
                # If we ping current machine
                if ping and user_id == self.user_id:
                    return True
                n_msg = self.encryptor.encrypt(user_id, self._host, msg)
            logger.info('[*] Sending: %s' % msg)
            send_sock.sendall(bytes(n_msg, 'utf-8'))
            return True
        except (Exception, socket.error) as e:
            # TODO Plaintext is too large
            logger.error('[-] Connection failed: %s' % str(host))
            return False
        finally:
            send_sock.close()
            del send_sock

    def _handle_recv(self):
        '''
        Non-blocking handling of received data
        '''

        inputs = [self._recv_sock]
        outputs = []
        message_queues = {}

        while self._handle_recv_data:
            readable, writable, exceptional = select.select(inputs, outputs,
                                                            inputs, 2)
            for sock in readable:
                if sock is self._recv_sock:
                    # A "readable" server socket is ready to
                    # accept a connection
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
                        message_queues[sock] = message_queues[sock].decode(
                                                                    'utf-8')
                        logger.info('[+] Recieved: %s' % message_queues[sock])

                        self._handle_received_data(message_queues[sock])
                        del message_queues[sock]

    def _handle_received_data(self, json_data):
        if json_data == '':
            return
        data = json.loads(json_data)
        if ('pubkey' in data) or ('signature' not in data):
            msg = data
        else:
            msg = self.encryptor.decrypt(data['signature'],
                                         base64.b64decode(data['encrypted_msg']),
                                         tuple(data['host']))
            msg = json.loads(msg) if msg is not None else None
        if msg:
            self._parse_data(msg)

    def _update_visibility(self, data):
        self._db.set_visibility(data['user_id'], 1 if not ('visible' in data)
                                else data['visible'])

    def _save_file(self, filename, _file):
        ''' Save file on the current machine '''

        with open(os.path.join(self.root_path, filename), 'wb') as new_file:
            new_file.write(base64.b64decode(_file))

    def remove_file(self, user_id):
        '''
        Remove file from queue of waiting for handling files
        '''

        os.remove(self.root_path + self.user_id2filename[user_id])
        del self.user_id2filename[user_id]

    def _handle_file_receiving(self, data, cur_time):
        global received_file_message

        self._save_file(data['filename'], data['file_data'])
        if 'room' in data:
            self._db.save_room_message(src=data['user_id'],
                                       message=received_file_message,
                                       time=cur_time, room_name=data['room'])
        else:
            self._db.save_message(src=data['user_id'], dst=self.user_id,
                                  message=received_file_message, time=cur_time)
        self.user_id2filename[data['user_id']] = data['filename']
        file_received.add(data['user_id'])

    def _parse_data(self, data, conn=None):
        '''
        Parse json data that was received from a host. Here all kind of
        data are processed with appropriate handlers

        Args:
            json_data (Json Object) Received data in json format
            conn Apparently this is useless argument
        '''

        if data == '':
            return
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

        if data['message'] != '':
            # If action connected with room
            if 'room' in data:
                self._handle_room_data(data, cur_time)
                return
            self._db.save_message(src=data['user_id'], dst=self.user_id,
                                  message=data['message'], time=cur_time)
        if 'connected' in data:
            logger.info('[+] Updating tables of connected hosts')
            self._update_connected(data)

        if 'new_username' in data:
            self._update_username(data)

    def _handle_room_data(self, data, cur_time):
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
        if data['user_id'] == self.user_id and data['message'] == EMPTY:
            return
        self._db.save_room_message(src=data['user_id'],
                                   message=data['message'],
                                   time=cur_time, room_name=data['room'])

    def _update_connected(self, data):
        for host_data in data['connected']:
            host = tuple(host_data[0])
            user_id = int(host_data[1])
            username, vis, pubkey, dis_enc = (host_data[_] for _ in range(2, 6))

            logger.info('[+] Connected host: {0}, username: {1}, user_id: {2}'
                        .format(host, username, user_id))

            self.host2user_id[host] = user_id
            self.user_id2host[user_id] = host

            self.encryptor.add_pubkey(user_id, pubkey, dis_enc=dis_enc)

            self._connected.add(host)
            self._db.save_user(user_id=user_id,
                               username=username,
                               visibility=vis)
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

        # if host[0] == self._host[0]:
        #     return
        
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
            self.encryptor.add_pubkey(data['sender_id'], data['pubkey'])
            # Update table for existent hosts
            for conn in self._connected:
                self.send_msg(host=conn, msg=json.dumps(data))

        # if host not in self._connected:
        publickey = data['pubkey']
        sender_id = data['sender_id']
        dis_enc   = data['dis_enc']

        logger.info(message + str(host) + \
                    '; user id: {}; public key:{}'.format(user_id,
                                                          publickey))
        if action_type == 'connect':
            self._process_connect_type(user_id, host, username,
                                       publickey, sender_id, dis_enc)

    def _process_connect_type(self, user_id, host, username, publickey,
                              sender_id, dis_enc):
        self.user_id2host[user_id] = host
        self.host2user_id[host] = user_id

        self.encryptor.add_pubkey(sender_id, publickey, dis_enc=dis_enc)
        self._connected.add(host)
        self._db.save_user(username=username, user_id=user_id)

    def _send_connected(self, host):
        host = tuple(host)
        tun_data = self.create_data(json_format=False, visibility=False)
        _connected = []
        for _host, user_id in self.host2user_id.items():
            dis_enc = True if user_id in self.encryptor._dis_enc else False
            _connected.append((_host, user_id, self._db.get_username(user_id),
                               self._db.get_visibility(user_id),
                               self.encryptor.get_pubkey(user_id), dis_enc))
        tun_data['connected'] = _connected
        logger.info('[+] Sending connected hosts to: %s' % str(host))
        self.send_msg(host=host, msg=json.dumps(tun_data),
                      pubkey_exchange=True)

    def is_connection_established(self):
        return self._get_ip_addr() is not None

    def _get_ip_addr(self):
        os_name = os.name
        for gl_if in nf.interfaces():
            for lc_if in interfaces:
                if (gl_if.startswith(lc_if) and os_name != 'nt') or \
                   os_name == 'nt':
                    try:
                        return (nf.ifaddresses(gl_if)[2][0]['addr'],
                                self.r_port)
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
            if host != self._host and self.restart(host):
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
