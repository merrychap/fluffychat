'''Module for managing with database'''
# !/usr/bin/env python3

import sqlite3 as sql
import sys
import traceback
import logging


logger = logging.getLogger(__name__)
DATABASE = 'database.db'

class DBHelper:
    def __init__(self):
        pass

    def get_message_data(self, cur, src_id, dst_id):
        cur.execute('''
            SELECT c_id, total_messages FROM conversation WHERE
            (user_one LIKE {0} AND user_two LIKE {1})
            OR
            (user_one LIKE {1} AND user_two LIKE {0});'''.format(src_id,
                                                                 dst_id))
        return cur.fetchone()

    def get_user_id(self, cur, username):
        cur.execute('''
            SELECT user_id FROM users WHERE
            username LIKE ?;''', (username, ))
        return cur.fetchone()[0]

    def get_sd_id(self, cur, src, dst):
        src_id = self.get_user_id(cur, src)
        dst_id = self.get_user_id(cur, dst)
        return (src_id, dst_id)

    def conversation_exists(self, cur, src_id, dst_id):
        cur.execute('''
            SELECT c_id FROM conversation WHERE
            (user_one LIKE {0} AND user_two LIKE {1})
            OR
            (user_one LIKE {1} AND user_two LIKE {0})
        '''.format(src_id, dst_id))
        return cur.fetchone() is not None

    def user_exist(self, cur, username):
        cur.execute('''
            SELECT user_id FROM users WHERE username LIKE ?
        ''', (username, ))
        return cur.fetchone() is not None

    def get_username(self, user_id):
        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            cur.execute(('SELECT username FROM users WHERE'
                         'user_id LIKE {0}').format(user_id))
            return cur.fetchone()

    # TODO pick out try...except of main DBHelper functions
    # into execute function
    def execute(self, command, error_message=''):
        try:
            command()
        except sql.Error as e:
            logger.error(error_message)
            traceback.logger.info_exc()

    def try_create_database(self):
        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS `users` (
                   `user_id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                   `username` VARCHAR(25) NOT NULL UNIQUE,
                   `password` VARCHAR(50) DEFAULT NULL
                );''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS `conversation` (
                    `c_id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    `user_one` INT(11) NOT NULL,
                    `user_two` INT(11) NOT NULL,
                    `time` INT(11) DEFAULT NULL,
                    `total_messages` INT(11) DEFAULT 0,
                    FOREIGN KEY (user_one) REFERENCES users(user_id),
                    FOREIGN KEY (user_two) REFERENCES users(user_id)
                );''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS `conversation_reply` (
                    `cr_id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    `reply` TEXT,
                    `reply_id` INT(11) NOT NULL,
                    `user_id_fk` INT(11) NOT NULL,
                    `c_id_fk` INT(11) NOT NULL,
                    `time` INT(11) DEFAULT NULL,
                    FOREIGN KEY (user_id_fk) REFERENCES users(user_id),
                    FOREIGN KEY (c_id_fk) REFERENCES conversation(c_id)
                );''')
            logger.info('[+] Database successuflly created(updated)')

    def save_message(self, src, dst, message):
        def increment_total_messages(cur, src_id, dst_id):
            cur.execute('''
                UPDATE conversation SET total_messages = total_messages + 1
                WHERE
                (user_one LIKE {0} AND user_two LIKE {1})
                OR
                (user_one LIKE {1} AND user_two LIKE {0});'''.format(src_id,
                                                                     dst_id))

        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()

            # Get users id
            src_id, dst_id = self.get_sd_id(cur, src, dst)

            # Update messages count in `conversation` table
            if not self.conversation_exists(cur, src_id, dst_id):
                cur.execute('''
                    INSERT INTO conversation (user_one, user_two,
                                                        total_messages)
                    VALUES (?, ?, 0);''', (src_id, dst_id))

            # Get number of message
            c_id, total_messages = self.get_message_data(cur, src_id, dst_id)

            # Save message
            cur.execute('''
                INSERT INTO conversation_reply (reply, reply_id, user_id_fk,
                c_id_fk) VALUES (?, ?, ?, ?);''', (message, total_messages + 1,
                                                   src_id, c_id))
            increment_total_messages(cur, src_id, dst_id)

            logger.info('[+] Message from {0} to {1} saved'.format(src, dst))

    def save_user(self, username, password=''):
        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()
            if not self.user_exist(cur, username):
                cur.execute('''
                    INSERT OR IGNORE INTO users (username, password)
                    VALUES (?, ?);''', (username, password))
                logger.info('[+] User "{0}" created successuflly'.format(username))
                return True
            else:
                logger.info('[-] User "{0}" already exists'.format(username))
                return False


    def delete_user(self, username):
        pass

    def delete_message(self, cr_id):
        pass

    def get_history(self, src, dst, count):
        con = sql.connect(DATABASE)
        with con:
            cur = con.cursor()

            # Get users id
            src_id, dst_id = self.get_sd_id(cur, src, dst)

            c_id = self.get_message_data(cur, src_id, dst_id)[0]
            cur.execute('''
                SELECT reply, reply_id, user_id_fk  FROM conversation_reply
                WHERE c_id_fk LIKE ? ORDER BY cr_id DESC LIMIT ?''', (c_id,
                                                                      count))
            messages = cur.fetchall()
            return messages
