import threading

from chats.console.base_chat import BaseChat, INDENT, BreakLoopException, lock
from chats.console.base_chat import print_information

from opt.appearance import cprint
from opt.strings import *


class UserChat(BaseChat):
    def __init__(self, username, client):
        super().__init__(client)
        self.create_cmd_handlers()

        self.username = username
        self.user_id = self.db_helper.get_user_id(username)

        if self.user_id == self.client.user_id:
            self.self_chat = True

        self.print_mode_help('private message')
        self.init_print_messages()

    def create_cmd_handlers(self):
        self.handlers = {
            (self.R_BACK,      self.back2main),
            (self.R_HELP,      self.help),
        }

    def handle_command(self, command):
        for pattern, handler in self.handlers:
            match = pattern.match(command)
            if match:
                handler(match)
        send_file = self.R_SEND_FILE.match(command)
        if send_file:
            self.parse_sending_file(send_file, username=self.username)
        else:
            if not self.send_message(username=self.username, text=command):
                cprint(ERROR_WHILE_SENDING)

    def open(self):
        self.print_last_messages(self.user_id)

        while True:
            try:
                try:
                    with lock:
                        message = self.user_input()
                    self.handle_command(message)
                except KeyboardInterrupt:
                    self.back2main()
            except BreakLoopException:
                self.self_chat = False
                break

    def help(self, *args):
        cprint((
            'User help'
        ))
