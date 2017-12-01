import threading
import sys
import re
import json
import network.client as nc

from abc import abstractmethod

from functools import wraps

from database.chat_dbhelper import ChatDBHelper
from opt.appearance import cprint


EMPTY = ' '
INDENT = 38 * '='
INF = 1000

lock = threading.Lock()
operation_done = True


def print_information(printer):
    @wraps(printer)
    def wrapper(self):
        global operation_done

        cprint('\n' + INDENT)
        printer(self)
        cprint(INDENT + '\n')
        operation_done = True
    return wrapper


class BreakLoopException(Exception):
    pass


class BaseChat:
    R_USER        = re.compile(r'^user ([a-zA-Z_.]+)$')
    R_USERNAME    = re.compile(r'^username ([a-zA-Z_.]+)$')
    R_ROOM        = re.compile(r'^room ([a-zA-Z_.]+)$')
    R_CREATE_ROOM = re.compile(r'^mkroom ([a-zA-Z_.]+)$')
    R_REMOVE_ROOM = re.compile(r'^rmroom ([a-zA-Z_]+)$')
    R_ADD_USER    = re.compile(r'^add_user ([a-zA-Z_]+) ([a-zA-Z_]+)$')
    R_ROOT_PATH   = re.compile(r'^chpath ([a-zA-Z0-9/\\_.]+)$')
    R_VISIBILITY  = re.compile(r'^chvis$')
    R_SEND_FILE   = re.compile(r'^send_file (.*)$')
    R_EXIT        = re.compile(r'^exit$|^q$|^quit$')
    R_HELP        = re.compile(r'^help$')
    R_USERS       = re.compile(r'^users$')
    R_ROOMS       = re.compile(r'^rooms$')

    def __init__(self, client):
        operation_done = True

        self.db_helper = ChatDBHelper()
        self.db_helper.specify_username(client)

        self.client        = client
        self.stop_printing = True

        self.inner_threads = []
        self.create_cmd_handlers()

        self.self_chat = False

        self.user_id   = ''
        self.room_name = ''

    @abstractmethod
    def create_cmd_handlers(self):
        pass

    @abstractmethod
    def help(self, message=None):
        pass

    def back2main(self):
        self.stop_printing = True
        cprint('\n<lpurple>[*]</lpurple> Switched to the <blue>command mode'
               '</blue>\n' + INDENT + '\n')
        raise BreakLoopException

    def parse_sending_file(self, parse, username='', room=''):
        file_location = parse.group(1)
        self.send_file(file_location, username, room)

    def print_mode_help(self, mode):
        cprint(('\n<lpurple>[*]</lpurple> Switched to the <blue>%s mode</blue>\n'
                'Type "enter" to start typing message\n'
                'You can type <lpurple>@help</lpurple> for the list of available '
                'commands\n' + INDENT + '\n') % mode)

    def specify_username(self):
        cprint('\n<magenta,bold>[*]</> Please, specify your '
               '<blue>username</> (a-zA-Z_.):>', end='')
        username = input(' ')
        self.client.specify_username(username)

    def specify_root_path(self):
        while True:
            cprint('<magenta,bold>[*]</> Specify your '
                   '<yellow,bold>base path</> for storing files:> ', end='')
            root_path = input(' ')
            if self.client.specify_root_path(root_path):
                break

    def _get_users(self, room_name, room_id):
        users = []
        for user in self.db_helper.get_users_by_room(room_name, room_id):
            users.append(user)
        return users

    def send_room_message(self, room_name, text, room_user='',
                          remove_room='No'):
        '''
        Sends message to the certain room

        Args:
            room_name (str) Passed name of a room
        '''

        room_id = self.db_helper.get_room_id(room_name)
        users = self._get_users(room_name, room_id)
        for user in users:
            if remove_room == 'Yes' and user == self.client.user_id:
                continue
            self.send_message(user_id=user, room=room_name, text=text,
                              remove_room=remove_room, room_user=room_user,
                              users_in_room=users)

    def handle_received_file(self, user_id, msg):
        if msg != 'Yes':
            self.client.remove_file(user_id)

    def send_file(self, file_location, username, room=''):
        if username != '':
            user_id = self.db_helper.get_user_id(username)
        filename = file_location.replace('/', ' ').replace('\\', ' ') \
                                .split()[-1]
        message = self.client.create_file_data(file_location, filename,
                                               user_id=self.client.user_id,
                                               room_name=room)
        if message is None:
            cprint('<lred>[-]</lred> Maybe that file doesn\'t exist')
            return

        if room != '':
            room_id = self.db_helper.get_room_id(room)
            for user_id in self._get_users(room, room_id):
                self._send_message(user_id, message, room)
        else:
            self._send_message(user_id, message)

    def is_online(self, username=None, user_id=None):
        if user_id is None:
            user_id = self.db_helper.get_user_id(username)
        try:
            host = self.client.user_id2host[user_id]
            return self.client.send_msg(host=host, msg=json.dumps(''),
                                        ping=True)
        except KeyError:
            return False

    def send_message(self, room="", user_id=None, username=None,
                     text=None, remove_room='No', room_user='',
                     room_creator='', users_in_room=[]):
        '''
        Sends message to destination host

        Args:
            room (str) Name of a room
            user_id (int) Id of a user
            username (str) Username of a user that should recieve message
            text (str) Text of a message
            text (data) Formated data of a message
            remove_room (str) "No" if don't need to remove room else "Yes"
        '''

        if (user_id is None and username is None):
            logger.info('[-] Invalid data for sending message')
            return False
        # Destination user id
        if user_id is None:
            user_id = self.db_helper.get_user_id(username)

        # if user sended to us a file and now we wanted to save it or not
        if user_id in nc.file_received:
            self.handle_received_file(user_id, text)
            nc.file_received.remove(user_id)
            return True

        if not self.db_helper.get_visibility(user_id=user_id):
            return False

        if room != '':
            room_creator = self.db_helper.get_room_creator(room)
        if room == '':
            self.db_helper.save_message(user_id, text, room)
        message = self.client.create_data(msg=text, room_name=room,
                                          username=self.client.username,
                                          user_id=self.client.user_id,
                                          remove_room=remove_room,
                                          room_creator=room_creator,
                                          new_room_user=room_user,
                                          users_in_room=users_in_room)
        return self._send_message(user_id, message, room, text)

    def _send_message(self, user_id, message, room='', text=''):
        # Destination host
        try:
            host = self.client.user_id2host[user_id]
            return self.client.send_msg(host=host, msg=message)
        except KeyError:
            pass

    def send_visibility(self):
        for host in self.client.host2user_id.keys():
            self.client._send_connected(host)

    def get_last_message(self, dst, room=False):
        for message in self.db_helper.get_history(dst, 1, room):
            return message
        return ('', 0, -1)

    def cur_user_exists(self):
        return self.client.username != ''

    def change_username(self, username):
        self.db_helper.change_username(username)
        cprint('\n<lpurple>[+]</lpurple> Username changed, <lblue>%s'
               '</lblue>!\n' % username)

    def print_entered_users(self):
        last_users = set(self.client.host2user_id.values())
        while not self.stop_printing_users:
            cur_users = set(self.client.host2user_id.values())
            if last_users != cur_users:
                try:
                    for new_user in cur_users.difference(last_users):
                        cprint('\n<lpurple>[*]</lpurple> User <lblue>%s'
                               '</lblue> has joined.' %
                               self.db_helper.get_username(new_user))
                    for rem_user in last_users.difference(cur_users):
                        cprint('\n<lpurple>[*]</lpurple> User <lblue>%s'
                               '</lblue> has leaved.' %
                               self.db_helper.get_username(rem_user))
                    last_users = cur_users
                except TypeError:
                    pass

    def init_print_users(self):
        self.stop_printing_users = False
        printer = threading.Thread(target=self.print_entered_users,
                                   daemon=True)
        self.inner_threads.append(printer)
        printer.start()

    def print_last_messages(self, dst, room=False):
        for message in list(self.db_helper.get_history(dst, 10, room))[::-1]:
            if message is None or message[1] == -1:
                continue
            cprint('<yellow>{0}</yellow>: <lblue>{1}</lblue><red>:></red> {2}'
                   .format(message[3], self.db_helper.get_username(message[2]),
                           message[0]))

    def user_input(self):
        cprint('<lblue>%s</lblue><red>:></red> ' %
               self.client.username, end='')
        return input()

    def init_print_messages(self, room=False):
        self.stop_printing = False
        if hasattr(self, 'user_id'):
            dst = self.user_id
        elif hasattr(self, 'room_name'):
            dst = self.room_name
        printer = threading.Thread(target=self.print_recv_message,
                                   args=(dst, room),
                                   daemon=True)
        self.inner_threads.append(printer)
        printer.start()

    def print_recv_message(self, dst, room=False):
        last_msg = self.get_last_message(dst, room)
        while not self.stop_printing:
            cur_msg = self.get_last_message(dst, room)
            if last_msg[1] != cur_msg[1]:
                messages = self.db_helper.get_history(dst,
                                                      cur_msg[1] - last_msg[1],
                                                      room)
                for message in messages:
                    if self.self_chat or message[2] != self.client.user_id:
                        cprint('<yellow>{0}</yellow>: '
                               '<lblue>{1}</lblue><red>:></red> {2}'
                               .format(message[3],
                                       self.db_helper.get_username(message[2]),
                                       message[0]))
                last_msg = cur_msg

    def remove_room(self, room_name):
        self.stop_printing = True
        self.send_room_message(room_name, "Room was deleted",
                               remove_room='Yes')
        self.db_helper.remove_room(room_name)
        cprint('\n<lgreen>[+]</lgreen> Room <lred>{0}</lred> was '
               'deleted\n'.format(room_name))

    def add_user2room(self, username, room_name):
        if not self.db_helper.user_exists(username):
            cprint('<lred>[-]</lred> No such user in the chat\n')
            return False
        self.db_helper.add_user2room(username=username,
                                     room_name=room_name)
        # Invites user to the room by sending
        # empty message
        self.send_room_message(room_name, EMPTY,
                               room_user=username)
        cprint('\n<lgreen>[+]</lgreen> You have invited <lblue>{0}</lblue>'
               ' to the <lred>{1}</lred> room\n'
               .format(username, room_name))
        return True

    def exit(self):
        global operation_done
        operation_done = True

        try:
            self.client.disconnect(exit=True)
        except TypeError as e:
            pass
        self.stop_printing = True
        self.stop_printing_users = True
        for thread in self.inner_threads:
            thread.join()
        cprint('\n<yellow,bold>Bye!</>')
        sys.exit()
