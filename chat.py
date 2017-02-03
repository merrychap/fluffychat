#!/usr/bin/env python3

import logging
import argparse
import logging.config
import signal

from args_parser import ArgsParser

from network.client import ChatClient

from database.chat_dbhelper import ChatDBHelper

from chats.console.main_chat import MainChat
from chats.gui.main_chat import GMainChat, gmain


LOG_FILE = 'logging_config.ini'


def main():
    logging.basicConfig(filename='app.log',
                        format='%(asctime)s : %(module)s : %(levelname)s : %(message)s',
                        level=logging.DEBUG)
    parser = ArgsParser()
    gui, host, port, recv_port, dis_enc = parser.get_params()

    if not gui:
        if host is None:
            client = ChatClient(recv_port, dis_enc=dis_enc)
        else:
            client = ChatClient(recv_port, dis_enc=dis_enc,
                                server_host=(host, port))
        # Create entity of console chat
        chat = MainChat(client=client)
        chat.run()
    else:
        gmain()


if __name__ == '__main__':
    main()
