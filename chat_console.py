#!/usr/bin/env python3

import sys
import threading
import network as net


class Chat():
    def __init__(self):
        self.network = net.Network()
        self.is_name_set = False
        self.name = ''
        self.text = ''

    def send_msg(self):
        pass

    def recv_msg(self):
        pass


def run():
    pass


if __name__ == '__main__':
    run()
