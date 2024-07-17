# mock client for testing the server
import struct
from socket import socket, AF_INET, SOCK_DGRAM, SO_BROADCAST, SOL_SOCKET

from src.ui.ansi import augment, random_color, random_format
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
        if len(msg) != 39 or not msg.startswith(struct.pack("!IB", 0xABCDDCBA, 0x2)):
            return

        msg_str = msg.decode(errors='replace')

        self.ui.display(augment(f"server name: {msg_str[5:36].strip()}",
                                random_color(),
                                random_format()))

        self.ui.display(augment(f"server port: {struct.unpack("!H", msg[37:])[0]}",
                                random_color(),
                                random_format()))


def main() -> None:
    c = Client()
    while True:
        c.recv()


if __name__ == '__main__':
    main()
