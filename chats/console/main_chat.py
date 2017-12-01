import os

from chats.console.base_chat import BaseChat, INDENT, BreakLoopException, lock
from chats.console.base_chat import print_information
from chats.console.room_chat import RoomChat
from chats.console.user_chat import UserChat

from opt.appearance import cprint
from opt.strings import *


class MainChat(BaseChat):
    def __init__(self, client):
        super().__init__(client)
        self.client = client

    def change_visibility(self, *args):
        self.db_helper.change_visibility()
        self.send_visibility()
        cprint(VISIBILITY_CHANGED.format(self.db_helper.get_visibility(user_id=self.client.user_id)))

    def print_users(self, *args):
        cprint('\n<white,bold>{}</>'.format(INDENT))
        for user_id in self.client.host2user_id.values():
            if (self.db_helper.get_visibility(user_id=user_id) or
            user_id == self.db_helper.get_cur_user_id()) and \
            self.is_online(user_id=user_id):
                cprint(PRINT_USER.format(self.db_helper.get_username(user_id)))
        cprint('<white,bold>{}</>\n'.format(INDENT))

    def print_rooms(self, *args):
        cprint('\n<white,bold>{}</>'.format(INDENT))
        for room in self.db_helper.get_user_rooms():
            cprint(PRINT_ROOMS.format(room[0]))
        cprint('<white,bold>{}</>\n'.format(INDENT))

    def parse_root_path(self, parse):
        new_root_path = parse.group(1)
        if not os.path.isdir(new_root_path):
            cprint(NOT_A_DIRECTORY)
        if new_root_path[-1] != '/':
            new_root_path += '/'
        self.db_helper.set_root_path(new_root_path)
        cprint(PATH_CHANGED)

    def parse_user(self, parse):
        username = parse.group(1)
        if self.db_helper.user_exists(username) and \
           self.db_helper.get_visibility(username) and \
           self.is_online(username=username):
            UserChat(username=username, client=self.client).open()
        else:
            cprint(NO_SUCH_USER)

    def parse_room(self, parse):
        room_name = parse.group(1)
        if self.db_helper.room_exists(room_name):
            RoomChat(room_name=room_name, client=self.client).open()
        else:
            cprint(NO_SUCH_ROOM)

    def parse_create_room(self, parse):
        room_name = parse.group(1)
        if self.db_helper.create_room(room_name):
            cprint(ROOM_CREATED.format(room_name))
        else:
            cprint(ROOM_ALREADY_EXISTS)

    def parse_username(self, parse):
        self.change_username(parse.group(1))

    def parse_remove_room(self, parse):
        room_name = parse.group(1)
        self.remove_room(room_name)

    def parse_add_user(self, parse):
        username = parse.group(1)
        room_name = parse.group(2)
        if not self.add_user2room(username, room_name):
            cprint(ERROR_ADD_USER)

    def parse_exit(self, parse):
        self.exit()

    def parse_help(self, parse):
        self.help()

    def run(self):
        if not self.cur_user_exists():
            self.specify_username()
            self.specify_root_path()
        else:
            cprint(HELLO_AGAIN.format(self.client.username))
            cprint(STORAGE.format(self.db_helper.get_root_path()))
        self.db_helper.specify_username(self.client)
        if not self.client.start():
            cprint(CONNECTION_ERROR)
            self.exit()
        self.init_print_users()
        self.command_mode()

    def help(self):
        cprint((
            '\n'
            '   <white,bold>* help</>:                  Show this output\n'
            '   <white,bold>* username [usrname]</>:    Change current username.\n'
            '   <white,bold>* rooms</>:                 Show available rooms.\n'
            '   <white,bold>* users</>:                 Show online users.\n'
            '   <white,bold>* user [username]</>:       Switch to the user private message mode. Enter in a private messages.\n'
            '   <white,bold>* room [room_name]</>:      Switch to the room message mode. Enter in a room.\n'
            '   <white,bold>* rmroom [roomname]</>:     Remove current user from a room. Room itself still exists.\n'
            '   <white,bold>* adduser [user] [room]</>: Add an user to a room.\n'
            '   <white,bold>* mkroom [roomname]</>:     Create new room.\n'
            '   <white,bold>* exit, q, quit</>:         Finish current chat session.\n'
            '   <white,bold>* chvis</>:                 Change your visibility in the chat.\n'
            '   <white,bold>* chpath [path]</>:         Change the directory for storing files.\n'
        ))

    def create_cmd_handlers(self):
        self.handlers = {
            (self.R_USER,        self.parse_user),
            (self.R_ROOM,        self.parse_room),
            (self.R_USERNAME,    self.parse_username),
            (self.R_CREATE_ROOM, self.parse_create_room),
            (self.R_REMOVE_ROOM, self.parse_remove_room),
            (self.R_ADD_USER,    self.parse_add_user),
            (self.R_ROOT_PATH,   self.parse_root_path),
            (self.R_EXIT,        self.parse_exit),
            (self.R_HELP,        self.parse_help),
            (self.R_USERS,       self.print_users),
            (self.R_ROOMS,       self.print_rooms),
            (self.R_VISIBILITY,  self.change_visibility)
        }

    def handle_command(self, command):
        for pattern, handler in self.handlers:
            match = pattern.match(command)
            if match:
                handler(match)
                return True
        return False


    def handle_signal(self, signal, frame):
        self.exit()

    def command_mode(self):
        cprint(START_CHAT)

        while True:
            try:
                cprint(MAIN_CHAT_PROMPT.format(self.client.username), end='')
                with lock:
                    command = input(' ')
                if command == '':
                    continue
                if not self.handle_command(command):
                    cprint(INVALID_COMMAND)
            except KeyboardInterrupt as e:
                cprint('')
