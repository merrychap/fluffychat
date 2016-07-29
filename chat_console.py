#!/usr/bin/env python3

import re
import os
import sys
import time
import logging
import threading
import optparse
import logging.config

from network import ChatClient
from network import PORT


LOG_FILE = 'logging_config.ini'
INF = 1000
lock = threading.Lock()

class BaseChat():
    def __init__(self, client):
        self.client = client
        self.commands = self.create_command_descrypt()

    def print_help(self, commands, message=None):
        print('\n' + 30*'=')
        print(('Commands types with @ on the left side of '
               'command\nList of commands:\n'))
        for command, descr in commands.items():
            print('+ %s : %s' % (command, descr))
        print(30*'=' + '\n')

    def specify_username(self):
        username = input('[*] Please, specify your username(a-zA-Z_.):> ')
        self.client.specify_username(username)

    def send_message(self, username, text):
        user_id = self.client.get_user_id()
        message = self.client.create_data(msg=text,
                                          username=self.client.username
                                          user_id=user_id)
        host = self.client.user_id2host[user_id]
        if user_id != self.client.user_id:
            self.client.save_message(user_id, text)
        self.client.send_msg(host=host, msg=message)

    def get_last_message(self, username):
        for message in self.client.get_history(username, INF):
            if message != None and \
               self.client.get_username(message[2])[0] == username:
               return message
        return ('', 0, -1)

    def cur_user_exists(self):
        return self.client.username != ''

    def change_username(self, username):
        self.client.change_username(username)
        print('\n[+] Username changed, %s!\n' % username)

    def print_recv_message(self, username):
        last_msg = self.get_last_message(username)
        while True:
            cur_msg = self.get_last_message(username)
            if last_msg[1] != cur_msg[1] and last_msg[2] == cur_msg[2]:
                messages = self.client.get_history(username,
                                                   cur_msg[1] - last_msg[1])
                for message in messages:
                    if self.client.get_username(message[2])[0] == username:
                        print('{0} : {1}:> {2}'.format(message[3],
                                                       username, message[0]))
                last_msg = cur_msg


class MainChat(BaseChat):
    def __init__(self, client):
        self.client = client
        self.commands = self.create_command_descrypt()

    def run(self):
        if not self.cur_user_exists():
            self.specify_username()
        else:
            print('Hello again, %s!' % self.client.username)
        self.client.start()
        self.command_mode()

    def exit(self):
        self.client.disconnect()
        print ('\nBye!')
        time.sleep(1)
        os._exit(1)

    def create_command_descrypt(self):
        return {
            'help': 'Shows this output',
            'username "username"': 'Changes username',
            'groups': 'Shows available groups',
            'users': 'Shows online users',
            'user "username"': 'Switches to user message mode',
            'room "roomname"': 'Switches to room message mode',
            'exit': 'Closes chat'
        }

    def command_mode(self):
        user_pattern = re.compile(r'^@user ([a-zA-Z_.]+)$')
        username_pattern = re.compile(r'@username ([a-zA-Z_.]+)$')
        room_pattern = re.compile(r'^@room ([a-zA-Z_.])$')

        print('\nType "@help" for list of commands with description')

        while True:
            command = input('[*] Enter command:> ')

            user_parse = user_pattern.match(command)
            room_parse = room_pattern.match(command)
            username_parse = username_pattern.match(command)

            if command == '@help':
                self.print_help(commands=self.commands)
            elif command == '@users':
                print('\n' + 30*'=')
                for user_id in self.client.host2user_id.values():
                    print('+ %s' % self.client.get_username(user_id))
                print(30*'=' + '\n')
            elif command == '@exit':
                self.exit()
            elif user_parse != None:
                username = user_parse.group(1)
                UserChat(username=username, client=self.client).open()
            elif room_parse != None:
                roomname = room_parse.group(1)
            elif username_pattern != None:
                self.change_username(username_parse.group(1))


class UserChat(BaseChat):
    def __init__(self, username, client):
        super().__init__(client)
        print('\n[*] Swithes to message mode.\nType "enter" to start typing message')
        self.username = username
        threading.Thread(target=self.print_recv_message,
                         args=(username,)).start()

    def open(self):
        print()
        for message in list(self.client.get_history(self.username, 10))[::-1]:
            if message == None or message[1] == -1:
                continue
            print('{0} : {1}:> {1}'.format(message[3],
                                    self.client.get_username(message[2])[0],
                                    message[0]))

        while True:
            input()
            with lock:
                message = input('%s:> ' % self.client.username)
            if message == '@help':
                self.print_help(commands=self.commands)
            elif message == '@back':
                print('\n[*] Switches to command mode\n')
                break
            elif message == '@test':
                print(self.client.get_history(self.username, 1))
            else:
                self.send_message(self.username, message)

    def create_command_descrypt(self):
        return {
            'help': 'Shows this output',
            'back': 'Returns to message mode',
        }


class RoomChat(BaseChat):
    def __init__(self, username, roomname, client):
        self.super().__init__(client)
        self.username = username
        self.roomname = roomname

    def open(self):
        pass

    def create_command_descrypt(self):
        return {
            'help': 'Shows this output',
            'back': 'Returns to message mode',
        }


def main():
    logging.basicConfig(filename='app.log', level=logging.DEBUG)

    parser = optparse.OptionParser('usage %prog -H <connected host> ')
    parser.add_option('-H', dest='conn_host', type='string',
                      help='specify connected host')
    (options, args) = parser.parse_args()
    conn_host = options.conn_host

    # TODO check username correctness
    if conn_host is None:
        client = ChatClient()
    else:
        client = ChatClient((conn_host, PORT))

    # Create entity of chat
    chat = MainChat(client=client)
    chat.run()


if __name__ == '__main__':
    main()
