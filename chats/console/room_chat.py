import threading

from chats.console.base_chat import parse_function, BaseChat, INDENT, operation_done
from chats.console.base_chat import BreakLoopException, lock, print_information

import chats.console.base_chat as bc


class RoomChat(BaseChat):
    def __init__(self, room_name, client):
        super().__init__(client)

        self.room_name = room_name
        self.room_id = self.db_helper.get_room_id(room_name)

        self.print_mode_help('room message')

    def init_command_handlers(self):
        self.command_handlers = {
            '@help': self.print_help,
            '@back': self.back2main,
            '@remove_room': _remove_room
        }

    @parse_function
    def parse_add_user(self, parse):
        username = add_parse.group(1)
        if not self.add_user2room(username, self.room_name):
            print('[-] Error while trying add user to the room')

    def _remove_room(self):
        self.remove_room(self.room_name)
        raise BreakLoopException

    def handle_command(self, command):
        bc.operation_done = False
        add_parse = self.ADD_PATTERN.match(command)

        try:
            self.command_handlers[command]()
            bc.operation_done = True
        except KeyError:
            self.parse_add_user(add_parse)
        finally:
            if not bc.operation_done:
                self.send_room_message(self.room_name, command)

    def open(self):
        print()
        self.print_last_messages(self.room_name, True)

        while True:
            try:
                try:
                    input('')
                    with lock:
                        message = input('%s:> ' % self.client.username)
                    self.handle_command(message)
                except KeyboardInterrupt:
                    self.back2main
            except BreakLoopException:
                break

    def create_command_descrypt(self):
        return {
            'help': 'Shows this output',
            'back': 'Returns to message mode',
            'add_user "username"': 'Adds passed user to the room',
            'remove_room "room_name"': 'Removes room from chat'
        }
