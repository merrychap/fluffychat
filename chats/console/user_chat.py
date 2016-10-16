import threading

from chats.console.base_chat import BaseChat, INDENT, BreakLoopException, lock
from chats.console.base_chat import print_information, parse_function, operation_done


class UserChat(BaseChat):
    def __init__(self, username, client):
        super().__init__(client)
        self.init_command_handlers()

        self.username = username
        self.user_id = self.db_helper.get_user_id(username)

        self.print_mode_help('message')
        self.init_print_messages()

    def init_command_handlers(self):
        self.command_handlers = {
            '@help': self.print_help,
            '@back': self.back2main,
        }

    def handle_command(self, command):
        try:
            self.command_handlers[command]()
        except KeyError:
            self.send_message(username=self.username, text=command)

    def open(self):
        print()
        self.print_last_messages(self.user_id)

        while True:
            try:
                try:
                    input('')
                    with lock:
                        message = input('%s:> ' % self.client.username)
                    self.handle_command(message)
                except KeyboardInterrupt:
                    self.back2main()
            except BreakLoopException:
                break


    def create_command_descrypt(self):
        return {
            'help': 'Shows this output',
            'back': 'Returns to message mode',
        }
