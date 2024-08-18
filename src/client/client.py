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
from src.shared.protocol import *

from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM
from _socket import SOL_SOCKET, SO_REUSEADDR
import threading
import sys

from enum import Enum


class State(Enum):
    WAITING_FOR_BROADCAST = 0x1
    CONNECTING = 0x2
    GAME_STARTED = 0x4
    TERMINATED = 0x8


class Client:
    __BUFFER_SIZE = 1024

    def __init__(self) -> None:
        self.__state: State = State.WAITING_FOR_BROADCAST
        self.__server: socket | None = None
        self.__server_addr: str | None = None
        self.__server_port: int | None = None
        self.__server_name: str | None = None
        self.__ui: UserInterface = CLI()
        self.__receive_thread: threading.Thread | None = None
        self.__send_thread: threading.Thread | None = None

    def start(self) -> None:
        """
        Starts the client
        :return: None
        """
        while self.__state != State.TERMINATED:
            self.__gameloop()

        self.stop()

    def __gameloop(self) -> None:
        if self.__send_thread:
            self.__send_thread.join(timeout=0)

        # 1. wait for server broadcast and save server address and port
        if not self.__wait_for_broadcast():
            return

        # 2. send join request to server
        if not self.__connect():
            return

        # 3. print server messages and wait for user input
        self.__receive_thread = threading.Thread(target=self.__receive(), name="receive_thread")
        self.__receive_thread.start()

        self.__send_thread = threading.Thread(target=self.__send(), name="send_thread")
        self.__send_thread.start()

        self.__receive_thread.join()
        self.__send_thread.join()

    def __reset(self) -> None:
        self.__state = State.WAITING_FOR_BROADCAST
        self.__server_addr = None
        self.__server_port = None
        self.__server_name = None
        if self.__server:
            self.__server.close()

        # TODO maybe interrupt?
        self.__receive_thread.join()

    def stop(self) -> None:
        """
        Stops the client
        :return: None
        """
        # TODO implement
        self.__ui.display(augment("Client stopped", "yellow"))

    def __wait_for_broadcast(self) -> bool:
        # 1. wait for server broadcast and save server address and port
        self.__ui.display(augment("Client started, listening for offer requests...", "yellow"))
        while self.__state == State.WAITING_FOR_BROADCAST:
            sock = socket(AF_INET, SOCK_DGRAM)
            sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            sock.bind(("", PORT_UDP))
            data, addr = sock.recvfrom(self.__BUFFER_SIZE)

            if not validate_broadcast(data):
                continue

            self.__server_addr, _ = addr
            self.__server_name = get_server_name(data)
            self.__server_port = get_server_port(data)
            self.__ui.display(f"Received offer from server \"{augment(self.__server_name, 'blue')}\" at address "
                              f"{augment(self.__server_addr, 'blue')}, attempting to connect...")
            self.__state = State.CONNECTING

        return True

    def __connect(self) -> bool:
        # TODO HANDLE TIMEOUT
        # 2. send join request to server
        self.__server = socket(AF_INET, SOCK_STREAM)
        try:
            self.__server.connect((self.__server_addr, self.__server_port))
        except:  # TODO check for specific exception
            self.__ui.display(augment("Could not connect", "red"))
            self.__state = State.WAITING_FOR_BROADCAST
            self.__server.close()
            return False

        self.__ui.display(augment("Connected to server", "green"))
        self.__state = State.GAME_STARTED
        return True

    def __receive(self) -> None:
        # 3. print server messages and wait for user input
        while self.__state == State.GAME_STARTED:
            data = self.__server.recv(self.__BUFFER_SIZE)
            self.__ui.display(augment("Connection lost", "red"))
            self.__state = State.WAITING_FOR_BROADCAST

            opcode = get_opcode(data)
            msg = get_message(data)
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
                    self.__ui.display(msg)
                case Opcode.INFO:
                    self.__ui.display(msg)
                case Opcode.POSITIVE:
                    self.__ui.display(augment("Correct!", "green", "bold"))
                case Opcode.NEGATIVE:
                    self.__ui.display(augment("Incorrect!", "red", "bold"))
                case _:
                    self.__ui.display(augment("Unknown message", "red"))

    def __send(self) -> None:
        # 4. send user input to server
        while self.__state is not State.TERMINATED:
            # try:
            message = self.__ui.get_input()
            # except KeyboardInterrupt:
            #     sys.exit(0)

            if message == "exit":
                sys.exit(0)

            if self.__server:
                self.__server.send(message.encode())


def main() -> None:
    c = Client()
    c.start()


if __name__ == '__main__':
    main()
