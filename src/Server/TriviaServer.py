from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST


class Player:
    sock: socket
    name: str
    score: int = 0

    def __init__(self, sock: socket, name: str) -> None:
        self.sock = sock
        self.name = name

    def __str__(self) -> str:
        return f"{self.name} : {self.score}"


class Server:
    __PORT_UDP = 13117
    __PORT_TCP = 0  # TODO
    __IP = "127.0.0.1"  # TODO
    __BROADCAST_DEST = "255.255.255.255"
    __MAGIC_COOKIE = 0xABCDDCBA
    __MESSAGE_TYPE = 0x2
    __PLAYER_JOIN_DELAY_MILLIS = 10_000
    __SERVER_NAME_LENGTH = 32
    __NAME = "😀👑💩"  # TODO naming things is harder than it seems
    __STRINGS = {"start": f"Server started, listening on IP address {__IP}",
                 "game_over": "Game over!\nCongratulations to the winner: ",
                 "restart": "Game over, sending out offer requests..."}

    __players: dict[Player]
    __leader: Player

    def __init__(self) -> None:
        # TODO find ip
        pass

    def __send_broadcast(self, data: str) -> None:
        """
        Sends a broadcast message, asking players to join the game

        :param data: The data to send
        :return: None
        """
        s = socket(AF_INET, SOCK_DGRAM)
        s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

        try:
            s.sendto(self.__build_packet(data), (self.__BROADCAST_DEST, self.__PORT_UDP))
        except Exception as e:
            print(e)  # TODO better error handling
        finally:
            s.close()

    def __send_message(self, player: Player, data: str) -> None:
        """
        Sends a message to a specific player

        :param player: The player to send the message to
        :param data: The data to send
        :return: None
        """
        pass

    def __accept_connection(self, player: Player) -> None:
        """
        Accepts a connection from a player

        :param player: The player to accept
        :return: None
        """
        pass

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

    def __build_packet(self, data: str) -> bytes:
        """
        Builds a packet to send to the players
        :return: The packet
        """
        # TODO test print
        return (
            f"{self.__MAGIC_COOKIE}{self.__MESSAGE_TYPE}{self.__NAME.ljust(self.__SERVER_NAME_LENGTH, '\0')}{data}".encode())

    def start_game(self) -> None:
        """
        Starts the game
        :return: None
        """
        pass

    def __reset_game(self) -> None:
        """
        Ends the game, announce the winner
        :return: None
        """
        pass


if __name__ == "__main__":
    pass
