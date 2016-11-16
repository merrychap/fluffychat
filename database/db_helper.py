'''
Module for local database management

This module provides managing of user and
its messages.
'''

# !/usr/bin/env python3

import sqlite3 as sql
import sys
import time
import traceback
import logging


logger = logging.getLogger(__name__)
DATABASE = 'database.db'

TABLE_CURRENT_USER = 'current_user'
TABLE_USERS = 'users'
TABLE_ROOMS = 'rooms'
TABLE_CONVERSATION = 'conversation'
TABLE_ROOM_CONVERSATION = 'room_conversation'
TABLE_RC_USER = 'rc_user'
TABLE_CONVERATION_REPLY = 'conversation_reply'
TABLE_ROOM_CONVERSATION_REPLY = 'room_conversation_reply'

class DBHelper:
    def __init__(self):
        pass

    def _increment_total_messages(self, cur, src, src_name, table,
                                  dst=None, dst_name=None, rc_user=None):
        conv_id = self._get_message_data(cur, src, src_name, table,
                                         dst=dst, dst_name=dst_name,
                                         rc_user=rc_user)[0]
        cur.execute('''
            UPDATE {0} SET total_messages = total_messages + 1
            WHERE c_id LIKE {1};'''.format(table, conv_id))

    def _increment_users_count(self, cur, room_name):
        cur.execute('''
            UPDATE rooms SET users_count = users_count + 1
            WHERE room_name LIKE ?;''', (room_name,))

    def _conversation_exists(self, cur, src, src_name, table,
                             dst=None, dst_name=None):
        data = self._get_message_data(cur, src, src_name,
                                      table, dst=dst, dst_name=dst_name)
        return data is not None

    def _get_message_data(self, cur, src, src_name, table,
                          dst=None, dst_name=None, rc_user=None):
        '''
        Returns conversation id and total message in conversation.
        It provides both getting message data from user to user and
        getting data from user to room. For the last purpose here is
        rc_user flag.

        Args:
            cur (Cursor) Database cursor
            src (int) Source user id
            src_name (str) Source filed name in the table of
                the database
            table (str) Name of table where is stored information
                about conversation
            dst (int) Destionation user or room id
            dst_name (str) Destintaion filed name in the table
                of the database
        '''

        # logger.info('Src: {0}; Src name: {1}; Dst: {2}; Dst name: {3}; Table: {4}; Rc user: {5}'
        #       .format(src, src_name, dst, dst_name, table, rc_user))
        if rc_user is not None:
            where_query = '"{0}" LIKE {1};'.format(dst_name, dst)
        else:
            where_query = '"{0}" LIKE {1};'.format(src_name, src)
            if dst is not None:
                where_query = '''
                    ("{0}" LIKE {1} AND "{2}" LIKE {3})
                    OR
                    ("{0}" LIKE {3} AND "{2}" LIKE {1});'''.format(src_name, src,
                                                                   dst_name, dst)
        cur.execute('SELECT c_id, total_messages FROM "{0}" WHERE {1}'
                    .format(table, where_query))
        return cur.fetchone()

    # TODO
    # Merge two functions below with similar function about users
    def _get_room_name(self, cur, room_id):
        '''
        Returns room name by its id

        Args:
            room_id (int) Room id

        Returns:
            (str) Room name
        '''
        cur.execute(('SELECT room_name FROM rooms WHERE '
                     'room_id LIKE ?;'), (room_id,))
        return cur.fetchone()

    def get_room_id(self, room_name):
        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            return self._get_room_id(cur, room_name)

    def _get_room_id(self, cur, room_name):
        '''
        Returns room id by its name. And if such room doesn't
        exist then it returns None

        Args:
            room_name (str) Room name

        Returns:
            (int) Room id
        '''

        cur.execute(('SELECT room_id FROM rooms WHERE '
                     'room_name LIKE ?;'), (room_name,))

        fetched = cur.fetchone()
        if fetched is not None:
            return fetched[0]

    def _user_exists_in_room(self, cur, room_id, user_id):
        '''
        Checks if passed user exists in passed room

        Args:
            cur (Cursor) Database Cursor
            room_id (int) Room id
            user_id (int) User id

        Returns:
        bool True if user exists, else False
        '''

        # Invalid arguments
        if room_id is None or user_id is None:
            return
        cur.execute('''
            SELECT * FROM rc_user WHERE
            room_id LIKE ? AND user_id LIKE ?;''',
            (room_id, user_id))
        return cur.fetchone() is not None

    def room_exists(self, room_name):
        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            return self._room_exists(cur, room_name)

    def _room_exists(self, cur, room_name):
        '''
        Checks if room with passed name exists
        in the local database

        Args:
            cur (Cursor) Database cursor
            room_name (str) Name of room

        Returns:
            bool True if room exists, else False
        '''

        room_id = self._get_room_id(cur, room_name)
        return room_id is not None

    def get_user_id(self, username):
        '''
        Returns user id by passed username. It uses private
        function that requires database cursor.

        Args:
            username (str) Username for processing

        Returns:
            int User id
        '''

        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            return self._get_user_id(cur, username)

    def _get_user_id(self, cur, username):
        '''
        Returns user id by passed username

        Args:
            cur (Cursor) Database cursor
            username (str) Username for processing

        Returns:
            int User id
        '''

        cur.execute('''
            SELECT user_id FROM users WHERE
            username LIKE ?;''', (username, ))
        return cur.fetchone()[0]

    def user_exists(self, username):
        '''
        Checks if user with passed username exists in the
        database. It uses private method with the same function

        Args:
            username (str) Passed username

        Returns:
            bool True if user exists, else False
        '''

        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            return self._user_exists(cur, username)

    def _user_exists(self, cur, username):
        '''
        Checks if user with passed username exists
        in the database

        Args:
            cur (Cursor) Database cursor
            username (str) Username for checking

        Returns:
            bool True if user exists, else False
        '''

        cur.execute('''
            SELECT user_id FROM users WHERE username LIKE ?
        ''', (username, ))
        return cur.fetchone() is not None

    def get_username(self, user_id):
        '''
        It returns username by user id

        Args:
            user_id (int) User id

        Returns:
            str Username of user with passed id
        '''

        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            return self._get_username(cur, user_id)

    def _get_username(self, cur, user_id):
        cur.execute(('SELECT username FROM users WHERE '
                     'user_id LIKE ?'), (user_id,))
        return cur.fetchone()[0]

    def get_current_user(self):
        '''
        Returns instance of user that has ran the application.

        Returns:
            Current user.
        '''

        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            cur.execute('SELECT * FROM `current_user`')
            return cur.fetchone()

    def get_room_creator(self, room_name):
        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            cur.execute('''
                SELECT creator_id FROM {0} WHERE room_name LIKE ?;'''
                .format(TABLE_ROOMS), (room_name,))
            return self._get_username(cur, cur.fetchone()[0])

    def get_user_rooms(self, username, user_id=None):
        '''
        Yields rooms, in which certain user is located.

        Args:
            username (str) Passed username
            user_id (optional, int) User id

        Yields:
            str Name of each room
        '''

        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            if user_id is None:
                user_id = self._get_user_id(cur, username)
            cur.execute('''
                SELECT room_id FROM rc_user WHERE
                user_id LIKE ?;''', (user_id,))
            for room_id in cur.fetchall():
                yield self._get_room_name(cur, room_id[0])

    # TODO pick out try...except of main DBHelper functions
    # into execute function
    def execute(self, command, error_message=''):
        try:
            command()
        except sql.Error as e:
            logger.error(error_message)
            traceback.logger.info_exc()

    def get_visibility(self, user_id):
        print('USER ID: {}'.format(user_id))
        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            return self._get_visibility(cur, user_id)

    def _get_visibility(self, cur, user_id):
        cur.execute('''
            SELECT visible FROM {0} WHERE user_id LIKE ?;'''
            .format(TABLE_USERS), (user_id,))
        return cur.fetchone()[0] == 1

    def get_last_user_id(self):
        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            cur.execute('''
                SELECT max(user_id) FROM {}'''.format(TABLE_USERS))
            return cur.fetchone()[0]

    def set_visibility(self, user_id, visible):
        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            self._set_visibility(cur, user_id, visible)

    def _set_visibility(self, cur, user_id, visible):
        cur.execute('''
            UPDATE {0} SET visible=? WHERE user_id LIKE ?;'''
            .format(TABLE_USERS), (1 if visible else 0, user_id))

    def set_root_path(self, root_path, user_id):
        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            self._set_root_path(cur, root_path, user_id)

    def _set_root_path(self, cur, root_path, user_id):
        cur.execute('''
            UPDATE {0} SET root_path=? WHERE user_id=?;'''.format(TABLE_CURRENT_USER),
            (root_path, user_id))

    def get_root_path(self):
        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            return self._get_root_path(cur)

    def _get_root_path(self, cur):
        cur.execute('''
            SELECT root_path FROM {0};'''.format(TABLE_CURRENT_USER))
        return cur.fetchone()[0]

    def try_create_room(self, room_name, creator_name, creator_id=None):
        '''
        Creates room in the local database. If room already
        exists in the database then function returns False.

        Args:
            room_name (str) Name of room that will be created
            creator_name (str) Username of room creator
        '''

        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            if creator_id is None:
                creator_id = self.get_user_id(creator_name)
            if not self._room_exists(cur, room_name):
                cur.execute('''
                    INSERT INTO rooms (room_name, creator_id)
                    VALUES (?, ?);''', (room_name, creator_id))
                logger.info('[+] Room "{0}" was created by "{1}"'
                            .format(room_name, creator_name))
                self._add_user2room(cur, creator_name, room_name)
                return True

            else:
                logger.info('[-] Room "{0}" is already exists'
                            .format(room_name))
                return False

    def try_create_database(self):
        '''
        Creates tables of database if they don't exist
        '''

        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()

            cur.execute('''
                CREATE TABLE IF NOT EXISTS {0} (
                    `user_id` INTEGER NOT NULL UNIQUE,
                    `username` VARCHAR(25) NOT NULL UNIQUE,
                    'root_path' VARCHAR(200) NOT NULL UNIQUE
                );'''.format(TABLE_CURRENT_USER))

            cur.execute('''
                CREATE TABLE IF NOT EXISTS {0} (
                   `user_id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                   `username` VARCHAR(25) NOT NULL UNIQUE,
                   `visible` INT(2) DEFAULT 1,
                   `password` VARCHAR(50) DEFAULT NULL
                );'''.format(TABLE_USERS))

            cur.execute('''
                CREATE TABLE IF NOT EXISTS {0} (
                    `room_id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    'room_name' VARCHAR(25) NOT NULL UNIQUE,
                    'creator_id' INT(11) NOT NULL,
                    `users_count` INT(11) DEFAULT 0,
                    FOREIGN KEY (creator_id) REFERENCES users(user_id)
                );'''.format(TABLE_ROOMS))

            cur.execute('''
                CREATE TABLE IF NOT EXISTS {0} (
                    `c_id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    `user_one` INT(11) NOT NULL,
                    `user_two` INT(11) NOT NULL,
                    `time` INT(11) DEFAULT NULL,
                    `total_messages` INT(11) DEFAULT 0,
                    FOREIGN KEY (user_one) REFERENCES users(user_id),
                    FOREIGN KEY (user_two) REFERENCES users(user_id)
                );'''.format(TABLE_CONVERSATION))

            cur.execute('''
                CREATE TABLE IF NOT EXISTS {0} (
                    `c_id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    `room_id` INT(11) NOT NULL,
                    `time` INT(11) DEFAULT NULL,
                    `total_messages` INT(11) DEFAULT 0,
                    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
                );'''.format(TABLE_ROOM_CONVERSATION))

            cur.execute('''
                CREATE TABLE IF NOT EXISTS {0} (
                    `с_id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    `room_id` INT(11) NOT NULL,
                    `user_id` INT(11) NOT NULL,
                    FOREIGN KEY (room_id) REFERENCES rooms(room_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );'''.format(TABLE_RC_USER))

            cur.execute('''
                CREATE TABLE IF NOT EXISTS {0} (
                    `cr_id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    `reply` TEXT,
                    `reply_id` INT(11) NOT NULL,
                    `user_id_fk` INT(11) NOT NULL,
                    `c_id_fk` INT(11) NOT NULL,
                    `time` INT(11) DEFAULT NULL,
                    FOREIGN KEY (user_id_fk) REFERENCES users(user_id),
                    FOREIGN KEY (c_id_fk) REFERENCES conversation(c_id)
                );'''.format(TABLE_CONVERATION_REPLY))

            cur.execute('''
                CREATE TABLE IF NOT EXISTS {0} (
                    `cr_id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    `reply` TEXT,
                    `reply_id` INT(11) NOT NULL,
                    `user_id_fk` INT(11) NOT NULL,
                    `c_id_fk` INT(11) NOT NULL,
                    `time` INT(11) DEFAULT NULL,
                    FOREIGN KEY (user_id_fk) REFERENCES users(user_id),
                    FOREIGN KEY (c_id_fk) REFERENCES room_conversation(c_id)
                );'''.format(TABLE_ROOM_CONVERSATION_REPLY))

            logger.info('[+] Database was successfully created(updated)')

    def save_message(self, src, dst, message, time, src_name='user_one',
                     dst_name='user_two', conv_table=TABLE_CONVERSATION,
                     conv_table_reply=TABLE_CONVERATION_REPLY, rc_user=None):
        '''
        Saves message from user to user\\room in the local database.

        Saving message to the user or room depends on the rc_user
        flag. If it is true then destination is room, else user.

        Args:
            src (int) Id of source user
            dst (int) Id of destination user or room
            message (str) Text of message
            time (int) Time of sending message
            src_name (str) Source filed name in the table of
                the database
            dst_name (str) Destintaion filed name in the table
                of the database
            conv_table (str) Name of conversation table
            conv_table_reply (str) Name of conversation reply table
        '''

        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            # Update messages count in `conversation` table
            conv_exists = self._conversation_exists(cur, src, src_name,
                                                    conv_table, dst, dst_name)
            if not conv_exists:
                if rc_user is None:
                    cur.execute('''
                        INSERT INTO {0} ({1}, {2}, total_messages)
                        VALUES (?, ?, 0);'''.format(conv_table, src_name,
                                                    dst_name), (src, dst))
                else:
                    cur.execute('''
                        INSERT INTO {0} ({1}, total_messages)
                        VALUES (?, 0);'''
                        .format(TABLE_ROOM_CONVERSATION, 'room_id'), (dst,))
            # Get number of current message in database
            c_id, total_messages = self._get_message_data(cur, src, src_name,
                                                          conv_table, dst=dst,
                                                          dst_name=dst_name,
                                                          rc_user=rc_user)
            # Save message in the database
            cur.execute('''
                INSERT INTO {0} (reply, reply_id, user_id_fk,
                c_id_fk, time) VALUES (?, ?, ?, ?, ?);'''
                .format(conv_table_reply), (message, total_messages + 1,
                                            src, c_id, time))
            self._increment_total_messages(cur, src, src_name, conv_table,
                                           dst, dst_name, rc_user)
            logger.info('[+] Message from {0} to {1} was saved'.format(src, dst))

    def save_room_message(self, src, message, time, room_name):
        '''
        It is separate function of saving message in the database.
        It uses save_message function, that provides saving room
        messages, but for clarity current function exists.

        Args:
            src (int) Id of source user
            message (str) Text of message
            time (int) Time of sending message
            room_name (str) Name of room, in which was sent message
        '''
        room_id = self.get_room_id(room_name)
        self.save_message(src=src, dst=room_id, message=message, time=time,
                          src_name='user_id', dst_name='room_id',
                          conv_table=TABLE_ROOM_CONVERSATION, rc_user=True,
                          conv_table_reply=TABLE_ROOM_CONVERSATION_REPLY)

    def save_user(self, username, user_id=None, visibility=1, password=''):
        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            if not self._user_exists(cur, username):
                if user_id is not None:
                    cur.execute('''
                        INSERT OR IGNORE INTO users (user_id, username, visible,
                        password) VALUES (?, ?, ?, ?);''', (user_id, username,
                                                            visibility, password))
                    logger.info('[+] User with id = {0} was created successfully'
                                .format(user_id))
                else:
                    cur.execute('''
                        INSERT OR IGNORE INTO users (username, visible)
                        VALUES (?, ?);''', (username, visibility))
                    logger.info('[+] User "{0}" was created successfully'
                                .format(username))
                return True
            else:
                logger.info('[-] User "{0}" is already exists'.format(username))
                return False

    def add_user2room(self, *args, **kwargs):
        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            self._add_user2room(cur=cur, *args, **kwargs)

    def _add_user2room(self, cur, username, room_name, user_id=None,
                      room_id=None):
        # Invalid function attributes
        if room_id is None:
            room_id = self._get_room_id(cur, room_name)
        if user_id is None:
            user_id = self.get_user_id(username)
        if not self._user_exists_in_room(cur, user_id=user_id,
                                         room_id=room_id):
            cur.execute('''
                INSERT INTO rc_user (user_id, room_id)
                VALUES (?, ?);''', (user_id, room_id))
            self._increment_users_count(cur, room_name)
            logger.info(('[+] User "{0}" was added to the room "{1}"'
                   ' successfully').format(username, room_name))
            return True
        else:
            logger.info('[-] User "{0}" is already exists to the room "{1}"'
                  .format(username, room_name))
            return False

    def save_current_user(self, username, user_id, cur=None, root_path=''):
        if cur is None:
            con = sql.connect(DATABASE)
            with con:
                cur = con.cursor()
                self.handle_saving_cur_user(username, user_id, cur, root_path)
        else:
            self.handle_saving_cur_user(username, user_id, cur, root_path)

    def handle_saving_cur_user(self, username, user_id, cur, root_path=''):
        user = self.get_current_user()
        if user is None:
            cur.execute('''
                INSERT OR IGNORE INTO `current_user`
                VALUES (?, ?, ?);''', (user_id, username, root_path))
            logger.info('[+] Current user saved')
        else:
            cur.execute('''
                UPDATE `current_user` SET username = ? WHERE user_id = ?;
            ''', (username, user_id))
            logger.info('[+] Current user was updated')

    def change_username(self, user_id, new_username):
        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            if not self._user_exists(cur, new_username):
                cur.execute('''
                    UPDATE users SET username = ? WHERE user_id = ?;''',
                    (new_username, user_id))
                logger.info('[+] User {0} changed username: {1}'
                            .format(user_id, new_username))
                return True
            else:
                logger.info('[-] "{0}" already exists'
                      .format(new_username))
                return False

    def get_users_by_room(self, room_name, room_id=None):
        '''
        Yields all users that was entered in the room.

        Args:
            room_name (str) Name of the room
            room_id (int, optional) Room id

        Yields:
            (int) Id of all users in the room
        '''

        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()

            if room_id is None:
                room_id = self._get_room_id(cur, room_name)

            cur.execute('''
                SELECT user_id FROM {0} WHERE room_id LIKE ?;'''
                .format(TABLE_RC_USER), (room_id,))
            for user_id in cur.fetchall():
                yield user_id[0]

    def remove_user_from_room(self, username, room_name):
        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            room_id = self._get_room_id(cur, room_name)
            user_id = self._get_user_id(cur, username)

            cur.execute('''
                DELETE FROM {0} WHERE {1} LIKE ? AND {2} LIKE ?'''
                .format(TABLE_RC_USER, 'room_id', 'user_id'), (room_id,
                                                               user_id))
            logger.info('[+] User "{0}" sucessfully removed from the "{0}" room'
                        .format(username, room_name))

    def remove_message(self, cr_id):
        pass

    def remove_room(self, room_name, room_id=None):
        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            if room_id is None:
                room_id = self._get_room_id(cur, room_name)

            cur.execute('''
                DELETE FROM {0} WHERE {1} LIKE ?;'''
                .format(TABLE_ROOMS, 'room_id'), (room_id,))

            cur.execute('''
                DELETE FROM {0} WHERE {1} LIKE ?;'''
                .format(TABLE_RC_USER, 'room_id'), (room_id,))

            logger.info('[+] Room "{0}" was sucessfully removed'.format(room_name))

    def get_history(self, src, dst, count, src_name='user_one',
                    dst_name='user_two', conv_table=TABLE_CONVERSATION,
                    conv_table_reply=TABLE_CONVERATION_REPLY, room=None):
        '''
        Returns message history of users conversation
        or conversation user in room. For the last purpose here is
        room flag.

        Args:
            src (int) Id of source user
            dst (int) Id of destination user or room
            count (int) Number of returned messages
            src_name (str) Source filed name in the table of
                the database
            dst_name (str) Destintaion filed name in the table
                of the database
            conv_table (str) Name of conversation table
            conv_table_reply (str) Name of conversation reply table
            room (bool) Flag for conversation in room
        '''

        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            try:
                msg_data = self._get_message_data(cur, src=src, src_name=src_name,
                                                  table=conv_table, dst=dst,
                                                  dst_name=dst_name,
                                                  rc_user=room)
                if msg_data is not None:
                    c_id = msg_data[0]
                else:
                    return
                cur.execute('''
                    SELECT reply, reply_id, user_id_fk, time
                    FROM {0}
                    WHERE c_id_fk LIKE ? ORDER BY cr_id DESC LIMIT ?'''
                    .format(conv_table_reply), (c_id, count))
                for msg in range(0, count):
                    message = cur.fetchone()
                    if message is None:
                        break
                    yield message
            except Exception as e:
                traceback.print_exc()
                yield None

    def get_room_history(self, src, room_name, count):
        '''
        It return yielded message history from the room.

        Args:
            src (int) Sender's id
            room_name (str) Name of the room
            count (int) Number of messages to return

        Returns:
            tuple Yielded message from self.get_history function
        '''

        return self.get_history(src=src, dst=self.get_room_id(room_name),
                                count=count, src_name='user_id',
                                dst_name='room_id',
                                room=True, conv_table=TABLE_ROOM_CONVERSATION,
                                conv_table_reply=TABLE_ROOM_CONVERSATION_REPLY)


if __name__ == '__main__':
    db = DBHelper()

    db.try_create_database()

    db.save_user(username='Mike')
    db.save_user(username='Holo')

    db.save_message(src=1, dst=2, message='hi', time=1)

    db.try_create_room(room_name='Wolf and Spice', creator_name='Holo')

    db.add_user2room(username='Mike', room_name='Wolf and Spice')

    db.try_create_room(room_name='Hyouka', creator_name='Mike')

    for user in db.get_users_by_room('Hyouka'):
        print(user)

    db.remove_user_from_room('Mike', 'Wolf and Spice')

    db.remove_room(room_name='Hyouka')

    for user in db.get_users_by_room('Wolf and Spice'):
        print(user)

    db.save_room_message(src=1, message='hi all', time=1, room_name='Wolf and Spice')

    # for message in db.get_history(src=1, dst=1, count=10, src_name='user_id',
    #                               dst_name='room_id', room=True,
    #                               conv_table=TABLE_ROOM_CONVERSATION,
    #                               conv_table_reply=TABLE_ROOM_CONVERSATION_REPLY):
    #     logger.info(message)
