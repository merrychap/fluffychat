from chats.console.base_chat import BaseChat, INDENT, BreakLoopException, lock
from chats.console.room_chat import RoomChat
from chats.console.user_chat import UserChat


class MainChat(BaseChat):
    def __init__(self, client):
        super().__init__(client)
        self.client = client
        self.commands = self.create_command_descrypt()

    def run(self):
        if not self.cur_user_exists():
            self.specify_username()
        else:
            print('Hello again, %s!' % self.client.username)
        self.db_helper.specify_username(self.client)
        self.client.start()
        self.command_mode()

    def create_command_descrypt(self):
        return {
            'help': 'Shows this output',
            'username "username"': 'Changes current username. ',
            'rooms': 'Shows available rooms.',
            'users': 'Shows online users.',
            'user "username"': 'Switches to user message mode. ',
            'room "room_name"': 'Switches to room message mode. ',
            'remove_room "roomname"': 'Removes created room.',
            'add_user': '"username" "room_name"',
            'create_room "roomname"': 'Creates new room. ',
            'exit': 'Closes chat.'
        }

    def handle_command(self, command):
        user_parse = self.USER_PATTERN.match(command)
        room_parse = self.ROOM_PATTERN.match(command)
        username_parse = self.USERNAME_PATTERN.match(command)
        create_room_parse = self.CREATE_ROOM_PATTERN.match(command)
        remove_room_parse = self.REMOVE_ROOM_PATTERN.match(command)
        add_user_parse = self.ADD_USER_PATTERN.match(command)

        if command == '@help':
            self.print_help(commands=self.commands)
        elif command == '@users':
            print('\n' + INDENT)
            for user_id in self.client.host2user_id.values():
                print('+ %s' % self.db_helper.get_username(user_id))
            print(INDENT + '\n')
        elif command == '@rooms':
            print('\n' + INDENT)
            for room in self.db_helper.get_user_rooms():
                print('+ %s' % room)
            print(INDENT + '\n')
        elif command == '@exit':
            self.exit()
        elif user_parse != None:
            username = user_parse.group(1)
            if self.db_helper.user_exists(username):
                UserChat(username=username, client=self.client).open()
            else:
                print('[-] No such user in the chat\n')
        elif room_parse != None:
            room_name = room_parse.group(1)
            if self.db_helper.room_exists(room_name):
                RoomChat(room_name=room_name, client=self.client).open()
            else:
                print('[-] No such room in the chat\n')
        elif create_room_parse != None:
            room_name = create_room_parse.group(1)
            if self.db_helper.create_room(room_name):
                print('\n[+] You\'ve created room "{0}"\n'
                      .format(room_name))
            else:
                print('\n[-] Room with this name already exists\n')
        elif username_parse != None:
            self.change_username(username_parse.group(1))
        elif remove_room_parse != None:
            room_name = remove_room_parse.group(1)
            self.remove_room(room_name)
        elif add_user_parse != None:
            username = add_user_parse.group(1)
            room_name = add_user_parse.group(2)
            if not self.add_user2room(username, room_name):
                return
        else:
            print('[-] Invalid command\n')

    def handle_signal(signal, frame):
        self.exit()

    def command_mode(self):
        print('\nType "@help" for list of commands with description')

        while True:
            try:
                command = input('[*] Enter command:> ')
                self.handle_command(command)
            except KeyboardInterrupt as e:
                self.exit()
