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

    parser = optparse.OptionParser('usage %prog -H <connected host> --sP <conn'
                                   ' host port> --rP <receiving port')
    parser.add_option('-H', dest='conn_host', type='string',
                      help='specify connected host')
    parser.add_option('--sP', dest='s_port', type='int',
                      help='specify conn host port')
    parser.add_option('--rP', dest='r_port', type='int',
                      help='specify port for receiving')
    (options, args) = parser.parse_args()
    conn_host = options.conn_host
    s_port = options.s_port
    r_port = options.r_port
    if conn_host is None:
        client = ChatClient(r_port)
    else:
        client = ChatClient(r_port, (conn_host, s_port))

    # Create entity of chat
    chat = MainChat(client=client)
    chat.run()


if __name__ == '__main__':
    main()
