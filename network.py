#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket


class Network:
    def __init__(self):
        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.listen_sock.bind(('0.0.0.0', 11719))

        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def send_data(self, msg):
        self.send_sock.sendto(msg.encode('utf-8'), ('255.255.255.255', 11719))

    def recv_data(self):
        return self.listen_sock.recv(1024).decode('utf-8')
