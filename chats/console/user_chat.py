import threading

from chats.console.base_chat import BaseChat, INDENT, BreakLoopException, lock
from chats.console.base_chat import print_information, parse_function

import chats.console.base_chat as bc

from opt.appearance import printc


class UserChat(BaseChat):
    def __init__(self, username, client):
        super().__init__(client)
        self.init_command_handlers()

        self.username = username
        self.user_id = self.db_helper.get_user_id(username)

        if self.user_id == self.client.user_id:
            self.self_chat = True

        self.print_mode_help('message')
        self.init_print_messages()

    def init_command_handlers(self):
        self.command_handlers = {
            '@help': self.print_help,
            '@back': self.back2main,
        }

    @parse_function
    def parse_sending_file(self, parse):
        file_location = parse.group(1)
        self.send_file(file_location, self.username)

    def handle_command(self, command):
        bc.operation_done = False
        send_file_parse = self.SEND_FILE_PATTERN.match(command)

        try:
            self.command_handlers[command]()
            bc.operation_done = True
        except KeyError:
            if send_file_parse:
                self.parse_sending_file(send_file_parse)
            else:
                if not self.send_message(username=self.username, text=command):
                    printc('<lred>[-]</lred> Connection failed')

    def open(self):
        printc()
        self.print_last_messages(self.user_id)

        while True:
            try:
                try:
                    input()
                    with lock:
                        message = self.user_input()
                    self.handle_command(message)
                except KeyboardInterrupt:
                    self.back2main()
            except BreakLoopException:
                self.self_chat = False
                break


    def create_command_descrypt(self):
        return {
            'help': 'Shows this output',
            'back': 'Returns to message mode',
            'send_file "file location"': 'Sends file to the user'
        }
