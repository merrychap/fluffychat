#!/usr/bin/env python3

import database.db_helper
import datetime
import json


class ChatDBHelper:
    def __init__(self):
        pass

    def specify_username(self, client):
        self._db = client._db
        self.username = client.username
        self._client = client

    def get_cur_user_id(self):
        return self._client.user_id

    def create_data(self, *args, **kwargs):
        return self._client.create_data(*args, **kwargs)

    def send_msg(self, *args, **kwargs):
        self._client.send_msg(*args, **kwargs)

    def get_history(self, dst, count, room=False):
        if not room:
            return self._db.get_history(self._client.user_id, dst, count)
        else:
            return self._db.get_room_history(self._client.user_id, dst, count)

    def get_username(self, user_id):
        return self._db.get_username(user_id)

    def get_user_id(self, username):
        return self._db.get_user_id(username)

    def save_message(self, user_id, message, room):
        cur_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        if room != '':
            self._db.save_room_message(src=user_id, message=message,
                                       time=cur_time, room_name=room)
        else:
            self._db.save_message(self._client.user_id, user_id, message, cur_time)

    def create_room(self, room_name):
        return self._db.try_create_room(room_name=room_name,
                                        creator_name=self.username)

    def change_username(self, new_username):
        data = self.create_data(username=self.username,
                                user_id=self._client.user_id,
                                json_format=False)
        data['new_username'] = new_username
        data_dump = json.dumps(data)
        for host in self._client._connected:
            if host != self._client._host:
                self.send_msg(host=host, msg=data_dump)
        self.username = new_username
        self._db.change_username(user_id=self._client.user_id,
                                 new_username=new_username)
        self._db.save_current_user(user_id=self._client.user_id,
                                   username=self.username)

    def user_exists(self, username):
        return self._db.user_exists(username)

    def get_root_path(self):
        return self._db.get_root_path()

    def set_root_path(self, root_path):
        self._db.set_root_path(root_path, self._client.user_id)

    def room_exists(self, room_name):
        return self._db.room_exists(room_name)

    def get_user_rooms(self):
        return self._db.get_user_rooms(self.username)

    def get_room_id(self, room_name):
        return self._db.get_room_id(room_name)

    def get_users_by_room(self, room_name, room_id=None):
        return self._db.get_users_by_room(room_name, room_id)

    def remove_room(self, room_name):
        self._db.remove_room(room_name)

    def get_room_creator(self, room_name):
        return self._db.get_room_creator(room_name)

    def change_visibility(self):
        self._db.set_visibility(self._client.user_id,
                                not self._db.get_visibility(self._client.user_id))

    def get_last_user_id(self):
        self._db.get_last_user_id()

    def get_visibility(self, username=None, user_id=None):
        if user_id is None:
            user_id = self._db.get_user_id(username)
        return self._db.get_visibility(user_id)

    def add_user2room(self, username, room_name):
        self._db.add_user2room(username=username, room_name=room_name)
