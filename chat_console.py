#!/usr/bin/env python3

import sys
import optparse
import re
import time

from network import Client


class Chat():
    def __init__(self, client, *args, **kwargs):
        self.client = client
        self.commands = self.create_command_descrpt()
        self.message_commands = self.create_message_command_descrypt()
        self.name = 'anonymous'

    def run(self):
        print('[*] Type "help" for list of commands with description')
        self.client.start()
        while True:
            command = input('[*] Enter command:> ')
            self.parse_command(command)
        pass

    def send_message(self, username, text):
        message = self.client.create_data(msg=text, src=username)
        self.client.send_msg(host=(username, 9090), msg=message)
        time.sleep(1)
        print(self.client.current_msg)

    def recv_message(self):
        pass

    def parse_command(self, command):
        if command == 'help':
            self.print_help(commands=self.commands, message=('\nList of '
                            'available commands'))
        elif command == 'message':
            print(('\n[*] Switched to message mode. Type "@help" for list of '
                   'available commands\n'))
            self.message_mode()
        elif command == 'exit':
            self.exit()

    def exit(self):
        exit(0)

    def print_help(self, commands, message=None):
        if message is not None:
            print(message)
        for command, descr in commands.items():
            print('+ %s : %s' % (command, descr))
        print()

    def create_command_descrpt(self):
        commands = {
            'help': 'Shows this output.',
            'message': ('Switches to message typing mode.'),
            'exit': 'Closes chat.'

        }
        return commands

    def create_message_command_descrypt(self):
        commands = {
            'help': 'Shows this output',
            'groups': 'Shows available groups',
            'users': 'Shows online users',
            'username "message"': 'Sends message to @username',
            'username': 'Switches to user message mode',
            'groupname': 'Switches to group message mode',
            'back': 'Switches to command mode'
        }
        return commands

    def message_mode(self):
        while True:
            message = input('[*] Enter message:> ')
            user_parse = re.match(r'^@[a-zA-Z_]+$', message)
            group_parse = re.match(r'^test$', message)
            test_parse = re.match(r'^@(\d{0,3}.\d{0,3}.\d{0,3}.\d{0,3}) (.+)$', message)

            if message == '@back':
                print('\n[*] Switched to command mode\n')
                break
            elif message == '@help':
                self.print_help(commands=self.message_commands, message=(
                                '\nCommands types with @ on the left side of'
                                'command\nList of message mode commands:\n'))
            elif user_parse != None:
                pass
            elif group_parse != None:
                pass
            elif test_parse != None:
                username = str(test_parse.group(1))
                text = str(test_parse.group(2))
                self.send_message(username=username , text=text)


def main():
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

    if conn_host is None:
        client = Client()
    else:
        client = Client((conn_host, conn_port))

    # Create entity of chat
    chat = Chat(client=client)
    chat.run()


if __name__ == '__main__':
    main()
