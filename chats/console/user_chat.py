import threading

from chats.console.base_chat import BaseChat, INDENT, BreakLoopException, lock


class UserChat(BaseChat):
    def __init__(self, username, client):
        super().__init__(client)

        self.username = username
        self.user_id = self.db_helper.get_user_id(username)

        self.print_mode_help('message')
        self.init_print_messages()

    def handle_command(self, command):
        if command == '@help':
            self.print_help(commands=self.commands)
        elif command == '@back':
            self.stop_printing = True
            print('\n[*] Switched to command mode\n' + INDENT + '\n')
            raise BreakLoopException
        elif command == '@test':
            print(self.db_helper.get_history(self.username, 1))
        else:
            self.send_message(username=self.username, text=command)

    def open(self):
        print()
        self.print_last_messages(self.user_id)

        while True:
            input()
            try:
                with lock:
                    message = input('%s:> ' % self.client.username)
                self.handle_command(message)
            except (BreakLoopException, KeyboardInterrupt):
                break


    def create_command_descrypt(self):
        return {
            'help': 'Shows this output',
            'back': 'Returns to message mode',
        }

    def init_command_handlers(self):
        pass
