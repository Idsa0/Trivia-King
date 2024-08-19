import struct
from socket import socket, gethostname, gethostbyname

from src.server.server import Server, Connection


class Player(Connection):
    def __init__(self, sock: socket, addr: tuple[str, int], name: str) -> None:
        super().__init__(sock, addr)
        self.__name = name
        self.__score = 0

    @property
    def name(self) -> str:
        return self.__name

    @property
    def score(self) -> int:
        return self.__score

    def increment_score(self) -> None:
        self.__score += 1

    def __str__(self) -> str:
        return f"{self.__name} : {self.__score}"

    def __cmp__(self, other) -> int:
        if not isinstance(other, Player):
            raise ValueError(f"Cannot compare Player with {type(other)}")
        return self.score - other.score

    def __lt__(self, other) -> bool:
        return self.__cmp__(other) < 0


class TriviaServer(Server):
    __PORT_UDP = 13117
    __PORT_TCP = 0  # TODO

    __MAGIC_COOKIE = 0xABCDDCBA
    __MESSAGE_TYPE = 0x2
    __SERVER_NAME_LENGTH = 32
    __NAME = "n3tw0rk1ng_m@st3r5"

    __STRINGS = {"start": f"Server started, listening on IP address: ",
                 "game_over": "Game over!\nCongratulations to the winner: ",
                 "restart": "Game over, sending out offer requests..."}

    __PLAYER_JOIN_DELAY_MILLIS = 10_000

    def __init__(self, name: str = __NAME) -> None:
        if len(name) > self.__SERVER_NAME_LENGTH:
            raise ValueError(f"Name too long, must be less than {self.__SERVER_NAME_LENGTH} characters")

        super().__init__(gethostbyname(gethostname()), TriviaServer.__PORT_UDP)
        self.__players = {}
        self.__name = name

    def send_broadcast(self, data: str) -> None:
        """
        Sends a broadcast message, asking players to join the game

        :param data: The data to send
        :return: None
        """
        super().send_broadcast(struct.pack("!IB32sH",
                                           0xABCDDCBA,
                                           0x2,
                                           self.name.ljust(self.__SERVER_NAME_LENGTH).encode(),
                                           self.__PORT_TCP))
        # TODO potentially use try-catch?

    def start(self) -> None:
        """
        Starts the game
        :return: None
        """
        pass

    def stop(self) -> None:
        pass

    def __reset_game(self) -> None:
        """
        Ends the game, announce the winner
        :return: None
        """
        pass

    def send_to(self, conn: Connection, data: str) -> None:
        """
        Sends a message to a specific player

        :param conn: The player to send the message to
        :param data: The data to send
        :return: None
        """
        conn.sock.send(data.encode())

    def send_to_all(self, data: str) -> None:
        """
        Sends a message to all players

        :param data: The data to send
        :return: None
        """
        for player in self.__players.values():
            self.send_to(player, data)

    def accept_connection(self, conn: Connection) -> None:
        """
        Accepts a connection from a player

        :param conn: The player to accept
        :return: None
        """
        # TODO
        pass

    def __leader(self) -> Player:
        """
        Returns the player with the highest score
        :return: The leader
        """
        return max(self.__players.values())

    def __add__(self, other: Connection) -> None:
        """
        Syntax sugar for adding a player to the game
        :param other: The player to add
        :return: None
        """
        self.__players[other.sock] = other

    @property
    def name(self) -> str:
        return self.__name


def main() -> None:
    server = TriviaServer()
    server.send_broadcast("")


if __name__ == "__main__":
    main()
