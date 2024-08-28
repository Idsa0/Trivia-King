import random
import sys
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM

from _socket import SOL_SOCKET, SO_REUSEADDR

from src.shared.protocol import *
from src.ui.ansi import augment, rainbowify
from src.ui.cli import CLI
from src.ui.userinterface import UserInterface


class State(Enum):
    """
    Enum representing the state of the client
    """

    WAITING_FOR_BROADCAST = 0x1
    """
    Indicates that the client is waiting for a broadcast from the server
    """
    CONNECTING = 0x2
    """
    Indicates that the client is connecting to the server
    """
    CONNECTED = 0x4
    """
    Indicates that the client is connected to the server
    """
    GAME_STARTED = 0x8
    """
    Indicates that the game has started
    """
    TERMINATED = 0x10
    """
    Indicates that the client has been terminated
    """


class Client:
    __BUFFER_SIZE = 1024  # buffer size for receiving messages

    __COMMON_NAMES = [  # common names to choose from when joining the server
        "Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Heidi", "Ivan", "Judy", "Kevin",
        "Linda", "Mallory", "Nancy", "Oscar", "Peggy", "Quentin", "Romeo", "Sue", "Trent", "Ursula",
        "Victor", "Walter", "Xander", "Yvonne", "Zelda"]

    def __init__(self) -> None:
        self.__state: State = State.WAITING_FOR_BROADCAST
        self.__server: socket | None = None
        self.__server_addr: str | None = None
        self.__server_port: int | None = None
        self.__server_name: str | None = None
        self.__ui: UserInterface = CLI()

    def start(self) -> None:
        """
        Starts the client
        :return: None
        """
        try:
            while self.__state != State.TERMINATED:
                self.__gameloop()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def __gameloop(self) -> None:
        """
        Main game loop, handles the client flow for a single game
        :return: None
        """
        # 1. wait for server broadcast and save server address and port
        if not self.__wait_for_broadcast():
            return

        # 2. send join request to server
        if not self.__connect():
            return

        self.__receive()

    def __reset(self) -> None:
        """
        Resets the client state
        :return: None
        """
        self.__state = State.WAITING_FOR_BROADCAST
        self.__server_addr = None
        self.__server_port = None
        self.__server_name = None
        if self.__server:
            self.__server.close()
            self.__server = None

    def stop(self) -> None:
        """
        Stops the client
        :return: None
        """
        self.__reset()
        self.__state = State.TERMINATED
        self.__ui.display(augment("Client shutting down...", "red"))

    def __wait_for_broadcast(self) -> bool:
        """
        Waits for a broadcast from the server and saves the server data
        :return: True if the client successfully received a broadcast, False otherwise
        """
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
        """
        Connects to the server
        :return: True if the client successfully connected to the server, False otherwise
        """
        # 2. send join request to server
        self.__server = socket(AF_INET, SOCK_STREAM)
        try:
            self.__server.connect((self.__server_addr, self.__server_port))
        except:
            self.__ui.display(augment("Could not connect", "red"))
            self.__state = State.WAITING_FOR_BROADCAST
            self.__server.close()
            return False

        self.__ui.display(augment("Connected to server", "green"))
        self.__server.send(create_message(Opcode.RENAME, random.choice(self.__COMMON_NAMES)).encode())
        self.__state = State.GAME_STARTED
        return True

    def __receive(self) -> None:
        """
        Receives messages from the server and handles them
        :return: None
        """
        # 3. print server messages and wait for user input
        while self.__state == State.GAME_STARTED or self.__state == State.CONNECTED:
            try:
                data = self.__server.recv(self.__BUFFER_SIZE)
            except (ConnectionResetError, ConnectionAbortedError):
                self.__ui.display(augment("Server disconnected", "red"))
                self.__reset()
                return
            except KeyboardInterrupt as e:
                # start() should handle this
                raise e

            opcode = get_opcode(data)
            msg = get_message(data)
            match opcode:
                case Opcode.ABORT:
                    self.__ui.display(msg if msg else "Game Over! Terminating...")
                    self.__state = State.TERMINATED
                case Opcode.START:
                    self.__ui.display(msg if msg else augment("Game started", "green"))
                    self.__state = State.GAME_STARTED
                case Opcode.END:
                    self.__ui.display(msg if msg else "Game Over!")
                    self.__reset()
                case Opcode.QUESTION:
                    self.__ui.display(msg)
                    self.__send()
                case Opcode.INFO:
                    self.__ui.display(msg)
                case Opcode.POSITIVE:
                    self.__ui.display(augment(rainbowify(msg if msg else "Correct!"), "bold"))
                case Opcode.NEGATIVE:
                    self.__ui.display(augment(msg if msg else "Incorrect!", "red", "bold"))
                case Opcode.UNKNOWN:
                    self.__ui.display(augment("Received an unknown message", "italic", "yellow"))

    def __send(self) -> None:
        """
        Sends an answer to the server
        :return: None
        """
        try:
            message = self.__ui.get_input(prompt="answer: ", timeout=QUESTION_TIMEOUT)
            if not message:
                self.__ui.display(augment("No input received", "red"))
        except KeyboardInterrupt:
            sys.exit(0)

        if message == "exit":
            sys.exit(0)

        if self.__server and message:
            bool_msg = answer_literal_to_bool(message)
            if bool_msg is not None:
                self.__server.send(create_message(Opcode.ANSWER, str(bool_msg)).encode())
            else:
                self.__ui.display(augment("Invalid input", "red"))


def main() -> None:
    c = Client()
    c.start()


if __name__ == '__main__':
    main()
