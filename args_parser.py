'''
Module includes class for parsing command line arguments
'''

import argparse
import re

from opt.appearance import printc


class ArgsParser:
    '''
    Class for parsing command line arguments
    '''

    def __init__(self):
        self.IP_pattern = re.compile(r'^(\d{0,3}\.){3}\d{0,3}$')
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument('--create', action='store_true',
                                 help='Create a new chat')
        self.parser.add_argument('--host', action='store', type=str,
                                 help='IP of a host you want to connect')
        self.parser.add_argument('-p', action='store', type=str,
                                 help='Port of a host you want to connect')
        self.parser.add_argument('-r', action='store', type=str,
                                 help=('Port for receiving messages on the'
                                       ' current computer'))
        self.parser.add_argument('--gui', action='store_true',
                                 help='Enable GUI mode')
        self.parser.add_argument('--dis-enc', action='store_true',
                                 help=('Disable encryption. it means when '
                                       'a host from the chat sends you a '
                                       'message it will not be encrypted'))

    def get_params(self):
        '''
        Get host IP and port and also port for receiving messages
        '''

        args = self.parser.parse_args()
        host, port, recv_port, gui = args.host, args.p, args.r, args.gui
        create, dis_enc = args.create, args.dis_enc

        recv_port = int(self._check_recv_port(recv_port))

        if create:
            return gui, None, None, recv_port, dis_enc

        if host:
            return self._specify_host_port(gui, host, port, recv_port, dis_enc)

        server_host = input('Do you want to start a new chat? (yes/no): ')
        if server_host.lower() == 'yes':
            return gui, None, None, recv_port, dis_enc
        else:
            return self._specify_host_port(gui, host, port, recv_port, dis_enc)

    def _specify_host_port(self, gui, host, port, recv_port, dis_enc):
        host = self._check_host_IP(host)
        port = int(self._check_host_port(port))
        return gui, host, port, recv_port, dis_enc

    def _check_correctness(self, msg, err_msg, obj, is_correct):
        '''
        Check if object is correct
        '''

        if not obj:
            obj = input(msg)
        while not is_correct(obj):
            printc('<lred>[-]</lred> Incorrect {}'.format(err_msg))
            obj = input(msg)
        return obj

    def _check_host_IP(self, host):
        return self._check_correctness(('Enter IP of a host you want to'
                                       ' connect: '), 'host IP', host,
                                       self._is_correct_host)

    def _check_host_port(self, port):
        return self._check_correctness('Port of a host you want to connect: ',
                                       'host port', port, self._is_number)

    def _check_recv_port(self, recv_port):
        return self._check_correctness('Port for receiving messages: ',
                                       'port', recv_port, self._is_number)

    def _is_number(self, obj):
        try:
            int(obj)
            return True
        except Exception:
            return False

    def _is_correct_host(self, host):
        ''' Check if host IP is correct '''

        return self.IP_pattern.match(host) is not None
