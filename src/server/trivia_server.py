from server import Server, Connection
from socket import socket, gethostname, gethostbyname


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


class TriviaServer(Server):
    __PORT_UDP = 13117
    __PORT_UDP_bytes = __PORT_UDP.to_bytes(2, 'big')
    __PORT_TCP = 0  # TODO

    __MAGIC_COOKIE = b'\xAB\xCD\xDC\xBA'
    __MESSAGE_TYPE = b'\x02'
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
        super().send_broadcast(self.__build_packet(data))

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
        conn.sock.send(self.__build_packet(data))

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

    def __build_packet(self, data: str) -> bytes:
        """
        Builds a packet to send to the players
        :return: The packet
        """
        return (
            f"{self.__MAGIC_COOKIE}{self.__MESSAGE_TYPE}\
            {self.name.ljust(self.__SERVER_NAME_LENGTH, '\0')}{data}".encode())

    def __update_leader(self) -> None:
        """
        Updates the leader of the game

        :return: None
        """
        # TODO potentially support multiple leaders?
        max_score = 0
        leader = None
        for player in self.__players.values():
            if player.score > max_score:
                max_score = player.score
                leader = player

        self.__leader = leader

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

    @property
    def short_port(self) -> bytes:
        return self.__PORT_UDP_bytes


def main() -> None:
    server = TriviaServer()
    server.send_broadcast(str(server.short_port))


if __name__ == "__main__":
    main()
