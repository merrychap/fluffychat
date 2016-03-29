#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import threading
import network as net

class Chat():
    def __init__(self):
        self.network = net.Network()
        self.is_name_set = False
        self.name = ''
        self.text = ''

    def __call__(self):
        recv = threading.Thread(target=self.get_msg)
        recv.start()

    def entering_msg(self):
        if not self.is_name_set:
            print('Enter your name')
            name = str(input())
            print(name)
            self.is_name_set = True
        else:
            self.text = str(input())
            self.send_msg()

    def send_msg(self):
        if not self.is_name_set:
            self.name = self.text
            self.is_name_set = True
        else:
            self.network.send_data(('%s : %s') % (self.name, self.text))

    def get_msg(self):
        try:
            data = self.network.recv_data()
            print(data)
        except:
            return


def run():
    chat = Chat()
    chat()


if __name__ == '__main__':
    run()
