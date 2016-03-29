#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import network as net
from tkinter import *


class Chat:
    def __init__(self):
        self.network = net.Network()

        self.tk = Tk()
        self.tk.title('Chat')
        self.tk.geometry('400x300')

        self.is_name_set = False

        self.name = StringVar()
        self.text = StringVar()

        self.name.set('Your name is:')
        self.text.set('')

        self.log = Text(self.tk)
        self.nick = Label(self.tk, textvariable=self.name)
        self.msg = Entry(self.tk, textvariable=self.text)

        self.msg.pack(side='bottom', fill='x', expand='true')
        self.nick.pack(side='bottom', fill='x', expand='true')
        self.log.pack(side='top', fill='both', expand='true')

        self.msg.bind('<Return>', self.send_msg)
        self.msg.focus_set()

        self.log.insert(END, 'bot: Hello. Enter your name below')

    def get_msg(self):
        self.log.see(END)
        self.network.listen_sock.setblocking(False)
        try:
            data = self.network.recv_data()
            self.log.insert(END, data + '\n')
        except:
            self.tk.after(1, self.get_msg)
            return
        self.tk.after(1, self.get_msg)
        return

    def send_msg(self, event):
        if not self.is_name_set:
            self.name.set(self.text.get())
            self.is_name_set = True
            self.log.delete('1.0', END)
        else:
            self.network.send_data(('%s : %s\n') % (self.name.get(), self.text.get()))
        self.text.set('')

    def __call__(self):
        self.tk.after(1, self.get_msg)
        self.tk.mainloop()


def run():
    chat = Chat()
    chat()


if __name__ == '__main__':
    run()
