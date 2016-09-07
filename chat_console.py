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

INDENT = 38 * '='

class BaseChat():
    def __init__(self, client):
        self.client = client
        self.commands = self.create_command_descrypt()
        self.stop_printing = True

    def print_help(self, commands, message=None):
        print('\n' + INDENT)
        print(('Type commands with @ on the left side of command.'
               '\nList of commands:\n'))
        for command, descr in commands.items():
            print('+ %s : %s' % (command, descr))
        print(INDENT + '\n')

    def print_mode_help(self, mode):
        print(('\n[*] Switched to %s mode\n'
               'Type "enter" to start typing message\n'
               'You can type @help for list of available '
               'commands\n' + INDENT + '\n') % mode)

    def specify_username(self):
        username = input('[*] Please, specify your username(a-zA-Z_.):> ')
        self.client.specify_username(username)

    def send_room_message(self, room_name, text):
        '''
        Sends message to the certain room

        Args:
            room_name (str) Passed name of the room
        '''

        room_id = self.client.get_room_id(room_name)
        for user in self.client.get_users_by_room(room_name, room_id):
            self.send_message(user_id=user, room=room_name, text=text)


    def send_message(self, room="", user_id=None,
                     username=None, text=None):
        '''
        Sends message to destination host

        Args:
            username (str) Username of user that should recieve message
            text (str) Text of message
            message (data) Formated data of message
        '''

        if (user_id is None and username is None):
           logger.info('[-] Invalid data for sending message')
           return
        # Destination user id
        if user_id is None:
            user_id = self.client.get_user_id(username)
        message = self.client.create_data(msg=text,
                                          username=self.client.username,
                                          user_id=self.client.user_id,
                                          room=room)
        # Destination host
        host = self.client.user_id2host[user_id]
        if user_id != self.client.user_id:
            self.client.save_message(user_id, text)
        self.client.send_msg(host=host, msg=message)

    def get_last_message(self, user_id=None, room_name=''):
        # Invalid arguments
        if (user_id is None and room_name == '') or \
           (user_id is not None and room_name != ''):
            return
        dst = user_id if user_id is not None else room_name
        for message in self.client.get_history(dst, 1, room_name != ''):
            return message
            # if message != None and message[2] == user_id:
            #    return message
        return ('', 0, -1)

    def cur_user_exists(self):
        return self.client.username != ''

    def change_username(self, username):
        self.client.change_username(username)
        print('\n[+] Username changed, %s!\n' % username)

    def print_last_messages(self, dst, room=False):
        for message in list(self.client.get_history(dst, 10, room))[::-1]:
            if message == None or message[1] == -1:
                continue
            print('{0} : {1}:> {2}'.format(message[3],
                                    self.client.get_username(message[2]),
                                    message[0]))
    def print_recv_room_message(self, room_id):
        pass

    def print_recv_message(self, user_id=None, room_name=''):
        dst = user_id if user_id is not None else room_name


        last_msg = self.get_last_message(user_id=user_id, room_name=room_name)
        while not self.stop_printing:
            cur_msg = self.get_last_message(user_id=user_id, room_name=room_name)
            if last_msg[1] != cur_msg[1]:
                messages = self.client.get_history(dst,
                                                   cur_msg[1] - last_msg[1],
                                                   room_name != '')
                for message in messages:
                    if message[2] != self.client.user_id:
                        print('{0} : {1}:> {2}'
                              .format(message[3],
                                      self.client.get_username(message[2]),
                                      message[0]))
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
            'username "username"': 'Changes current username. ',
            'rooms': 'Shows available rooms.',
            'users': 'Shows online users.',
            'user "username"': 'Switches to user message mode. ',
            'room "roomname"': 'Switches to room message mode. ',
            'remove_room "roomname"': 'Removes created room.',
            'create_room "roomname"': 'Creates new room. ',
            'exit': 'Closes chat.'
        }

    def command_mode(self):
        user_pattern = re.compile(r'^@user "([a-zA-Z_.]+)"$')
        username_pattern = re.compile(r'@username "([a-zA-Z_.]+)"$')
        room_pattern = re.compile(r'^@room "([a-zA-Z_.]+)"$')
        create_room_pattern = re.compile(r'^@create_room "([a-zA-Z_.]+)"$')

        print('\nType "@help" for list of commands with description')

        while True:
            command = input('[*] Enter command:> ')

            user_parse = user_pattern.match(command)
            room_parse = room_pattern.match(command)
            username_parse = username_pattern.match(command)
            create_room_parse = create_room_pattern.match(command)

            if command == '@help':
                self.print_help(commands=self.commands)
            elif command == '@users':
                print('\n' + INDENT)
                for user_id in self.client.host2user_id.values():
                    print('+ %s' % self.client.get_username(user_id))
                print(INDENT + '\n')
            elif command == '@rooms':
                print('\n' + INDENT)
                for room in self.client.get_user_rooms():
                    print('+ %s' % room)
                print(INDENT + '\n')
            elif command == '@exit':
                self.exit()
            elif user_parse != None:
                username = user_parse.group(1)
                if self.client.user_exists(username):
                    UserChat(username=username, client=self.client).open()
                else:
                    print('[-] No such user in the chat\n')
            elif room_parse != None:
                room_name = room_parse.group(1)
                if self.client.room_exists(room_name):
                    RoomChat(room_name=room_name, client=self.client).open()
                else:
                    print('[-] No such room in the chat\n')
            elif create_room_parse != None:
                room_name = create_room_parse.group(1)
                self.client.create_room(room_name)
                print('\n[+] You\'ve created room "{0}"\n'.format(room_name) )
            elif username_parse != None:
                self.change_username(username_parse.group(1))
            else:
                print('[-] Invalid command\n')


class UserChat(BaseChat):
    def __init__(self, username, client):
        super().__init__(client)

        self.username = username
        self.user_id = client.get_user_id(username)

        self.print_mode_help('message')

        self.stop_printing = False
        threading.Thread(target=self.print_recv_message,
                         args=(self.user_id,)).start()

    def open(self):
        print()
        self.print_last_messages(self.user_id)

        while True:
            input()
            with lock:
                message = input('%s:> ' % self.client.username)
            if message == '@help':
                self.print_help(commands=self.commands)
            elif message == '@back':
                self.stop_printing = True
                print('\n[*] Switched to command mode\n' + INDENT + '\n')
                break
            elif message == '@test':
                print(self.client.get_history(self.username, 1))
            else:
                self.send_message(username=self.username, text=message)

    def create_command_descrypt(self):
        return {
            'help': 'Shows this output',
            'back': 'Returns to message mode',
        }


class RoomChat(BaseChat):
    def __init__(self, room_name, client):
        super().__init__(client)

        self.room_name = room_name
        self.room_id = self.client.get_room_id(room_name)

        self.print_mode_help('room message')

        self.stop_printing = False
        threading.Thread(target=self.print_recv_message,
                         args=(None,self.room_name,)).start()

    def open(self):
        print()
        self.print_last_messages(self.room_name, True)

        add_patter = re.compile(r'^@add_user "([a-zA-Z_])+"$')

        while True:
            input()
            with lock:
                message = input('%s:> ' % self.client.username)
            add_parse = add_patter.match(message)
            if message == '@help':
                self.print_help(commands=self.commands)
            elif message == '@back':
                self.stop_printing = True
                print('\n[*] Switched to command mode\n' + INDENT + '\n')
                break
            elif add_parse != None:
                username = add_parse.group(1)
                if not self.client.user_exists(username):
                    print('[-] No such user in the chat\n')
                    continue
                self.client.add_user2room(username=username,
                                          room_name=self.room_name)
                print('[+] You have invited "{0}" to "{1}" room'.
                      format(username, self.room_name))
            else:
                self.send_room_message(self.room_name, message)

    def create_command_descrypt(self):
        return {
            'help': 'Shows this output',
            'back': 'Returns to message mode',
            'add_user "username"': 'Adds passed user to the room'
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
