import threading

from chats.console.base_chat import BaseChat, INDENT
from chats.console.base_chat import operation_done
from chats.console.base_chat import BreakLoopException, lock, print_information

from opt.appearance import cprint
from opt.strings import *


class RoomChat(BaseChat):
    def __init__(self, room_name, client):
        super().__init__(client)

        self.room_name = room_name
        self.room_id = self.db_helper.get_room_id(room_name)

        self.print_mode_help('room message')
        self.init_print_messages(True)

    def create_cmd_handlers(self):
        self.handlers = {
            (self.R_HELP,      self.help),
            (self.R_BACK,      self.back2main),
            (self.R_IN_RMROOM, self._remove_room)
        }

    def parse_add_user(self, parse):
        username = add_parse.group(1)
        if not self.add_user2room(username, self.room_name):
            cprint(ERROR_ADD_USER)

    def _remove_room(self):
        self.remove_room(self.room_name)
        raise BreakLoopException

    def handle_command(self, command):
        for pattern, handler in self.handlers:
            match = pattern.match(command)
            if match:
                handler(match)
                return True
        
        add_parse = self.R_ADD_USER.match(command)
        send_file_parse = self.R_SEND_FILE.match(command)

        if add_parse:
            self.parse_add_user(add_parse)
        elif send_file_parse:
            self.parse_sending_file(send_file_parse, room=self.room_name)
        else:
            self.send_room_message(self.room_name, command)

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

    def help(self):
        cprint((
            '\n'
            '   <white,bold>* help</>:              Show this help\n'
            '   <white,bold>* back</>:              Change the current username.\n'
            '   <white,bold>* adduser [usrname]</>: Send a file.\n'
            '   <white,bold>* rmroom</>:            Remove current room.\n'
            '   <white,bold>* file [filepath]</>:   Send a file.\n'
        ))
