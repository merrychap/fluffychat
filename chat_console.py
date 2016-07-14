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


LOG_FILE = 'logging_config.ini'
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
        message = self.client.create_data(msg=text, username=username)
        host = self.client.host2username[username]
        self.client.send_msg(host=host, msg=message)

    def print_recv_message(self, username):
        last_msg_id = self.client.get_history(username, 1)[0][1]
        while True:
            cur_msg_id = self.client.get_history(username, 1)[0][1]
            if last_msg_id != cur_msg_id:
                messages = self.client.get_history(username,
                                                   cur_msg_id - last_msg_id)
                for message in messages:
                    print('{0}:> {1}'.format(username, message[0]))
                last_msg_id = cur_msg_id


class MainChat(BaseChat):
    def __init__(self, client):
        self.client = client
        self.commands = self.create_command_descrypt()

    def run(self):
        self.specify_username()
        self.client.start()
        self.command_mode()

    def exit(self):
        print ('\nBye!')
        os._exit(1)

    def create_command_descrypt(self):
        return {
            'help': 'Shows this output',
            'groups': 'Shows available groups',
            'users': 'Shows online users',
            'user "username"': 'Switches to user message mode',
            'room "roomname"': 'Switches to room message mode',
            'exit': 'Closes chat'
        }

    def command_mode(self):
        user_pattern = re.compile(r'^@user ([a-zA-Z_.]+)$')
        room_pattern = re.compile(r'^@room ([a-zA-Z_.])$')

        print('\nType "@help" for list of commands with description')

        while True:
            command = input('[*] Enter command:> ')

            user_parse = user_pattern.match(command)
            room_parse = room_pattern.match(command)

            if command == '@help':
                self.print_help(commands=self.commands)
            elif command == '@users':
                print('\n' + 30*'=')
                for user in self.client.host2username.keys():
                    print('+ %s' % user)
                print(30*'=' + '\n')
            elif command == '@exit':
                self.exit()
            elif user_parse != None:
                username = user_parse.group(1)
                UserChat(username=username, client=self.client).open()
            elif room_parse != None:
                roomname = room_parse.group(1)


class UserChat(BaseChat):
    def __init__(self, username, client):
        super().__init__(client)
        print('\n[*] Swithes to message mode.\nType "enter" to start typing message')
        self.username = username
        threading.Thread(target=self.print_recv_message,
                         args=(username,)).start()

    def open(self):
        while True:
            input()
            with lock:
                message = input('%s:> ' % self.username)
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

    parser = optparse.OptionParser('usage %prog -H <connected host> ' +
                                   '-p <connected port>')
    parser.add_option('-H', dest='conn_host', type='string',
                      help='specify connected host')
    parser.add_option('-p', dest='conn_port', type=int,
                      help='specify connected port')
    (options, args) = parser.parse_args()
    conn_host = options.conn_host
    conn_port = options.conn_port

    if (conn_host is None and conn_port is not None) or \
       (conn_host is not None and conn_port is None):
        print(parser.usage)
        exit(0)
    # TODO check username correctness
    if conn_host is None:
        client = ChatClient()
    else:
        client = ChatClient((conn_host, conn_port))

    # Create entity of chat
    chat = MainChat(client=client)
    chat.run()


if __name__ == '__main__':
    main()
