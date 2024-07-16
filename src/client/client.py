# mock client for testing the server
from socket import socket, AF_INET, SOCK_DGRAM, SO_BROADCAST, SOL_SOCKET
from random import choice

from src.ui.cli import CLI


class Client:
    __PORT_UDP = 13117

    def __init__(self) -> None:
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.sock.bind(('', self.__PORT_UDP))
        self.ui = CLI()

    def recv(self) -> None:
        msg, _ = self.sock.recvfrom(1024)
        msg_str = msg.decode()

        if len(msg_str) < 47:
            return

        if msg_str[:19] != "b'\\xab\\xcd\\xdc\\xba'":
            return

        if msg_str[19:26] != "b'\\x02'":
            self.ui.display("Invalid message type")
            self.ui.display(msg_str[19:26])

        # server name = msg_str[26:56].strip()

        self.ui.display(msg_str)
        msg_str = msg_str[56:]

        self.ui.display(self.ui.augment(msg_str,
                                        choice(list(self.ui.ansi_colors.keys())),
                                        choice(list(self.ui.ansi_formats.keys()))))

        # this is obviously wrong, tomorrow I'll try to use the struct module


if __name__ == '__main__':
    c = Client()
    while True:
        c.recv()
