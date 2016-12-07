import threading
import sys
import re
import json
import network.client as nc

from functools import wraps

from database.chat_dbhelper import ChatDBHelper
from opt.appearance import printc


EMPTY = ' '
INDENT = 38 * '='
INF = 1000

lock = threading.Lock()
operation_done = True


def print_information(printer):
    @wraps(printer)
    def wrapper(self):
        global operation_done

        printc('\n' + INDENT)
        printer(self)
        printc(INDENT + '\n')
        operation_done = True
    return wrapper


def parse_function(handler):
    @wraps(handler)
    def wrapper(self, parse, *args, **kwargs):
        global operation_done

        if parse:
            handler(self, parse, *args, **kwargs)
            operation_done = True
    return wrapper


class BreakLoopException(Exception):
    pass


class BaseChat:
    USER_PATTERN = re.compile(r'^@user "([a-zA-Z_.]+)"$')
    USERNAME_PATTERN = re.compile(r'@username "([a-zA-Z_.]+)"$')
    ROOM_PATTERN = re.compile(r'^@room "([a-zA-Z_.]+)"$')
    CREATE_ROOM_PATTERN = re.compile(r'^@create_room "([a-zA-Z_.]+)"$')
    REMOVE_ROOM_PATTERN = re.compile(r'^@remove_room "([a-zA-Z_]+)"$')
    ADD_USER_PATTERN = re.compile(r'^@add_user "([a-zA-Z_]+)" "([a-zA-Z_]+)"$')
    ADD_PATTERN = re.compile(r'^@add_user "([a-zA-Z_]+)"$')
    ROOT_PATH_PATTERN = re.compile(r'^@change_root_path "([a-zA-Z0-9/\\_.]+)"$')
    SEND_FILE_PATTERN = re.compile(r'^@send_file "([a-zA-Z0-0/\\_.]+)"$')

    def __init__(self, client):
        operation_done = True

        self.db_helper = ChatDBHelper()
        self.db_helper.specify_username(client)

        self.client = client
        self.commands = self.create_command_descrypt()
        self.stop_printing = True

        self.inner_threads = []
        self.init_command_handlers()

        self.self_chat = False

    def init_command_handlers():
        pass

    def back2main(self):
        self.stop_printing = True
        printc('\n<lpurple>[*]</lpurple> Switched to <blue>command mode</blue>\n' + INDENT + '\n')
        raise BreakLoopException

    @parse_function
    def parse_sending_file(self, parse, username='', room=''):
        file_location = parse.group(1)
        self.send_file(file_location, username, room)

    @print_information
    def print_help(self, message=None):
        printc(('Type commands with <lpurple>@</lpurple> on the left side of command.'
               '\nList of commands:\n'))
        for command, descr in self.commands.items():
            printc('<lyellow>+</lyellow> <lpurple>%s</lpurple> : %s' % (command, descr))

    def print_mode_help(self, mode):
        printc(('\n<lpurple>[*]</lpurple> Switched to <blue>%s mode</blue>\n'
               'Type "enter" to start typing message\n'
               'You can type <lpurple>@help</lpurple> for list of available '
               'commands\n' + INDENT + '\n') % mode)

    def specify_username(self):
        printc('<lpurple>[*]</lpurple> Please, specify your '
               '<lblue>username</lblue>(a-zA-Z_.):> ', end='')
        username = input()
        self.client.specify_username(username)

    def specify_root_path(self):
        while True:
            printc('<lpurple>[*]</lpurple> Specify your '
                   '<lyellow>root path</lyellow> for storing files:> ', end='')
            root_path = input()
            if self.client.specify_root_path(root_path):
                break

    def _get_users(self, room_name, room_id):
        users = []
        for user in self.db_helper.get_users_by_room(room_name, room_id):
            users.append(user)
        return users

    def send_room_message(self, room_name, text, room_user = '',
                          remove_room='No'):
        '''
        Sends message to the certain room

        Args:
            room_name (str) Passed name of the room
        '''

        room_id = self.db_helper.get_room_id(room_name)
        users = self._get_users(room_name, room_id)
        # if text.replace(' ', '') != '':
        #     self.db_helper.save_message(self.client.user_id, text, room_name)
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
        filename = file_location.replace('/', ' ').replace('\\', ' ').split()[-1]
        message = self.client.create_file_data(file_location, filename,
                                               user_id=self.client.user_id,
                                               room_name=room)
        if message is None:
            printc('<lred>[-]</lred> Maybe that file doesn\'t exist')
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
            return self.client.send_msg(host=host, msg=json.dumps(''))
        except KeyError:
            return False

    def send_message(self, room="", user_id=None, username=None,
                     text=None, remove_room='No', room_user = '',
                     room_creator='', users_in_room=[]):
        '''
        Sends message to destination host

        Args:
            username (str) Username of user that should recieve message
            text (str) Text of message
            message (data) Formated data of message
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
        message = self.client.create_data(msg=text,
                                          username=self.client.username,
                                          user_id=self.client.user_id,
                                          room_name=room, remove_room=remove_room,
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
        printc('\n<lpurple>[+]</lpurple> Username changed, <lblue>%s</lblue>!\n' % username)

    def print_entered_users(self):
        last_users = set(self.client.host2user_id.values())
        while not self.stop_printing_users:
            cur_users = set(self.client.host2user_id.values())
            if last_users != cur_users:
                try:
                    for new_user in cur_users.difference(last_users):
                        printc('\n<lpurple>[*]</lpurple> User <lblue>%s</lblue>'
                               ' come in the chat' % self.db_helper.get_username(new_user))
                    for rem_user in last_users.difference(cur_users):
                        printc('\n<lpurple>[*]</lpurple> User <lblue>%s</lblue>'
                               ' go out of the chat' % self.db_helper.get_username(rem_user))
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
            if message == None or message[1] == -1:
                continue
            printc('<yellow>{0}</yellow>: <lblue>{1}</lblue><red>:></red> {2}'
                   .format(message[3], self.db_helper.get_username(message[2]),
                           message[0]))

    def user_input(self):
        printc('<lblue>%s</lblue><red>:></red> ' % \
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
                        printc('<yellow>{0}</yellow>: '
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
        printc('\n<lgreen>[+]</lgreen> Room <lred>{0}</lred> was deleted\n'.format(room_name))

    def add_user2room(self, username, room_name):
        if not self.db_helper.user_exists(username):
            printc('<lred>[-]</lred> No such user in the chat\n')
            return False
        self.db_helper.add_user2room(username=username,
                                     room_name=room_name)
        # Invites user to the room by sending
        # empty message
        self.send_room_message(room_name, EMPTY,
                               room_user=username)
        printc('\n<lgreen>[+]</lgreen> You have invited <lblue>{0}</lblue>'
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
        printc('\n<yellow>Bye!</yellow>')
        sys.exit()
