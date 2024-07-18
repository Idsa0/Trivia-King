# client flow:
# 1. wait for server broadcast and save server address and port
# 2. send join request to server
# 3. print server messages and wait for user input
# 4. send user input to server
# 5. repeat steps 4 and 5 until server sends finish message
# 6. close connection and return to step 1

from src.ui.userinterface import UserInterface
from src.ui.cli import CLI
from src.ui.ansi import augment, random_color, random_format

from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM
import struct
import sys
import threading

from enum import Enum


class State(Enum):
    WAITING_FOR_BROADCAST = 0x1
    CONNECTING = 0x2
    GAME_STARTED = 0x4
    TERMINATED = 0x8


class Opcode(Enum):
    ABORT = 0x1  # indicates the end of the game and the client should terminate
    START = 0x2  # indicates the start of the game
    END = 0x4  # indicates the end of the game
    QUESTION = 0x8  # indicates a question
    INFO = 0x10  # indicates an informational message
    POSITIVE = 0x20  # indicates a positive response
    NEGATIVE = 0x40  # indicates a negative response


class Client:
    __PORT_UDP = 13117
    __BUFFER_SIZE = 1024

    __BROADCAST_LENGTH = 39
    __BROADCAST_MAGIC_COOKIE = 0xABCDDCBA
    __BROADCAST_MESSAGE_TYPE = 0x2
    __BROADCAST_NAME_SLICE = slice(5, 36)
    __BROADCAST_PORT_SLICE = slice(37, 39)

    def __init__(self) -> None:
        self.__state: State = State.WAITING_FOR_BROADCAST
        self.server: socket | None = None
        self.__server_addr: str | None = None
        self.__server_port: int | None = None
        self.__server_name: str | None = None
        self.__ui: UserInterface = CLI()

    def start(self) -> None:
        """
        Starts the client
        :return: None
        """
        # 1. wait for server broadcast and save server address and port
        self.__ui.display(augment("Client started, listening for offer requests...", "yellow"))
        self.__wait_for_broadcast()

        # 2. send join request to server
        self.__connect()

        # 3. print server messages and wait for user input
        receive_thread = threading.Thread(target=self.__receive)
        receive_thread.start()

        # 4. send user input to server
        send_thread = threading.Thread(target=self.__send)
        send_thread.start()

    def stop(self) -> None:
        """
        Stops the client
        :return: None
        """
        if self.server:
            self.server.close()
        self.__ui.display(augment("Client stopped", "yellow"))

    @classmethod
    def validate_broadcast(cls, data: bytes) -> bool:
        """
        Validates a broadcast message
        :param data: The data to validate
        :return: True if the data follows the broadcast format, False otherwise
        """
        return len(data) == cls.__BROADCAST_LENGTH and data.startswith(
            struct.pack("!IB", cls.__BROADCAST_MAGIC_COOKIE, cls.__BROADCAST_MESSAGE_TYPE))

    def __wait_for_broadcast(self) -> None:
        # 1. wait for server broadcast and save server address and port TODO SO_REUSEPORT
        while self.__state == State.WAITING_FOR_BROADCAST:
            sock = socket(AF_INET, SOCK_DGRAM)
            sock.bind(("", self.__PORT_UDP))
            data, addr = sock.recvfrom(self.__BUFFER_SIZE)

            if not self.validate_broadcast(data):
                continue

            self.__server_addr, _ = addr
            self.__server_name = data[self.__BROADCAST_NAME_SLICE].strip().decode()
            self.__server_port = struct.unpack("!H", data[self.__BROADCAST_PORT_SLICE])[0]
            self.__ui.display(f"Received offer from server \"{augment(self.__server_name, 'blue')}\" at address "
                              f"{augment(self.__server_addr, 'blue')}, attempting to connect...")
            self.__state = State.CONNECTING

    def __connect(self) -> None:
        # TODO HANDLE TIMEOUT
        # 2. send join request to server
        self.server = socket(AF_INET, SOCK_STREAM)
        try:
            self.server.connect((self.__server_addr, self.__server_port))
        except (TimeoutError, ConnectionRefusedError):
            self.__ui.display(augment("Could not connect", "red"))
            self.__state = State.WAITING_FOR_BROADCAST
            return

        self.__ui.display(augment("Connected to server", "green"))
        self.__state = State.GAME_STARTED

    def __receive(self) -> None:
        # 3. print server messages and wait for user input
        while self.__state == State.GAME_STARTED:
            data = self.server.recv(self.__BUFFER_SIZE)
            opcode = self.__get_opcode(data)
            match opcode:
                case Opcode.ABORT:
                    self.__ui.display(augment("Game over, server aborted", "red"))
                    self.__state = State.TERMINATED
                case Opcode.START:
                    self.__ui.display(augment("Game started", "green"))
                    self.__state = State.GAME_STARTED
                case Opcode.END:
                    self.__ui.display(augment("Game over, server finished", "green"))
                    self.__state = State.TERMINATED
                case Opcode.QUESTION:
                    self.__ui.display(data[1:].decode())
                case Opcode.INFO:
                    self.__ui.display(data[1:].decode())
                case Opcode.POSITIVE:
                    self.__ui.display(augment("Correct!", "green", "bold"))
                case Opcode.NEGATIVE:
                    self.__ui.display(augment("Incorrect!", "red", "bold"))
                case _:
                    self.__ui.display(augment("Unknown message", "red"))

    def __send(self) -> None:
        # 4. send user input to server
        while self.__state == State.GAME_STARTED:
            message = self.__ui.get_input()
            self.server.send(message.encode())

    @staticmethod
    def __get_opcode(data: bytes) -> Opcode:
        return Opcode(data[0])


def main() -> None:
    c = Client()
    c.start()


if __name__ == '__main__':
    main()
