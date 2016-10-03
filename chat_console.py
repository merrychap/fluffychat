#!/usr/bin/env python3

import logging
import optparse
import logging.config
import signal

from network.client import ChatClient
from network.client import PORT

from database.chat_dbhelper import ChatDBHelper

from chats.console.main_chat import MainChat


LOG_FILE = 'logging_config.ini'


def main():
    logging.basicConfig(filename='app.log', level=logging.DEBUG)

    parser = optparse.OptionParser('usage %prog -H <connected host> ')
    parser.add_option('-H', dest='conn_host', type='string',
                      help='specify connected host')
    (options, args) = parser.parse_args()
    conn_host = options.conn_host

    # TODO check username correctness
    if conn_host is None:
        client = ChatClient()
    else:
        client = ChatClient((conn_host, PORT))

    # Create entity of chat
    chat = MainChat(client=client)
    chat.run()


if __name__ == '__main__':
    main()
