import threading

from chats.console.base_chat import parse_function, BaseChat, INDENT, operation_done
from chats.console.base_chat import BreakLoopException, lock, print_information

import chats.console.base_chat as bc

from opt.appearance import printc


class RoomChat(BaseChat):
    def __init__(self, room_name, client):
        super().__init__(client)

        self.room_name = room_name
        self.room_id = self.db_helper.get_room_id(room_name)

        self.print_mode_help('room message')
        self.init_print_messages(True)

    def init_command_handlers(self):
        self.command_handlers = {
            '@help': self.print_help,
            '@back': self.back2main,
            '@remove_room': self._remove_room
        }

    @parse_function
    def parse_add_user(self, parse):
        username = add_parse.group(1)
        if not self.add_user2room(username, self.room_name):
            printc('<lred>[-]</lred> Error while trying add user to the room')

    def _remove_room(self):
        self.remove_room(self.room_name)
        raise BreakLoopException

    def handle_command(self, command):
        bc.operation_done = False
        add_parse = self.ADD_PATTERN.match(command)
        send_file_parse = self.SEND_FILE_PATTERN.match(command)

        try:
            self.command_handlers[command]()
            bc.operation_done = True
        except KeyError:
            if add_parse:
                self.parse_add_user(add_parse)
            elif send_file_parse:
                self.parse_sending_file(send_file_parse, room=self.room_name)
            else:
                self.send_room_message(self.room_name, command)
        except BreakLoopException:
            raise BreakLoopException

    def open(self):
        self.print_last_messages(self.room_name, True)

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
                    raise BreakLoopException
            except BreakLoopException:
                break

    def create_command_descrypt(self):
        return {
            'help': 'Shows this output',
            'back': 'Returns to message mode',
            'add_user "username"': 'Adds passed user to the room',
            'remove_room "room_name"': 'Removes room from chat',
            'send_file "path to file"': 'Sends file to the room'
        }
