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
        msg = msg.decode()
        self.ui.display(self.ui.augment(msg, choice(list(self.ui.ansi.keys()))))


if __name__ == '__main__':
    c = Client()
    while True:
        c.recv()
