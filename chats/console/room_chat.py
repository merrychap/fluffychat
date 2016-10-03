import threading

from chats.console.base_chat import BaseChat, INDENT, BreakLoopException, lock


class RoomChat(BaseChat):
    def __init__(self, room_name, client):
        super().__init__(client)

        self.room_name = room_name
        self.room_id = self.db_helper.get_room_id(room_name)

        self.print_mode_help('room message')
        self.init_command_handlers()

    def handle_command(self, command):
        add_parse = self.ADD_PATTERN.match(command)

        if command == '@help':
            self.print_help(commands=self.commands)
        elif command == '@back':
            self.stop_printing = True
            print('\n[*] Switched to command mode\n' + INDENT + '\n')
            raise BreakLoopException
        elif add_parse != None:
            username = add_parse.group(1)
            if not self.add_user2room(username, self.room_name):
                return
        elif command == '@remove_room':
            self.remove_room(self.room_name)
            raise BreakLoopException
        else:
            self.send_room_message(self.room_name, command)


    def open(self):
        print()
        self.print_last_messages(self.room_name, True)

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
            'add_user "username"': 'Adds passed user to the room',
            'remove_room "room_name"': 'Removes room from chat'
        }
