from abc import ABC, abstractmethod
from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST


class Connection:
    sock: socket
    addr: tuple[str, int]

    def __init__(self, sock: socket, addr: tuple[str, int]) -> None:
        self.sock = sock
        self.addr = addr

    def __str__(self) -> str:
        return f"{self.addr[0]}:{self.addr[1]}"


class Server(ABC):
    __DEFAULT_IP = "127.0.0.1"
    __BROADCAST_DEST = "255.255.255.255"

    def __init__(self, ip: str = __DEFAULT_IP) -> None:
        self.__ip = ip

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    def send_broadcast(self, data: bytes, port: int) -> None:
        """
        Sends a broadcast message

        :param data: The data to send
        :param port: The port to send the data to
        :return: None
        """
        with socket(AF_INET, SOCK_DGRAM) as s:
            s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            s.sendto(data, ("<broadcast>", port))

    @abstractmethod
    def send_to(self, conn: Connection, data: bytes) -> None:
        pass

    @abstractmethod
    def send_to_all(self, data: bytes) -> None:
        pass

    @abstractmethod
    def accept_connection(self, conn: Connection) -> None:
        pass

    @property
    def ip(self) -> str:
        return self.__ip

    @property
    def broadcast_dest(self) -> str:
        return self.__BROADCAST_DEST

    @property
    def default_ip(self) -> str:
        return self.__DEFAULT_IP
