import threading
import time
import random
from socket import socket, gethostname, gethostbyname

from src.server.questions import get_trivia_questions, QuestionLiteral
from src.server.server import Server, Connection
from src.shared.protocol import *
from src.ui.ansi import augment
from src.ui.cli import CLI


class Player(Connection):
    def __init__(self, sock: socket, addr: tuple[str, int], name: str) -> None:
        super().__init__(sock, addr)
        self.__name = name
        self.__score = 0

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, name: str) -> None:
        self.__name = name

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


class State(Enum):
    INACTIVE = 0x1
    SENDING_OFFERS = 0x2
    GAME_STARTED = 0x4
    TERMINATED = 0x8


class TriviaServer(Server):
    __NAME_DEFAULT = "n3tw0rk1ng_m@st3r5"

    def __init__(self, name: str = __NAME_DEFAULT, topic: QuestionLiteral = "networking") -> None:
        if len(name) > SERVER_NAME_LENGTH:
            raise ValueError(f"Name too long, must be less than {SERVER_NAME_LENGTH} characters")

        super().__init__(ip=gethostbyname(gethostname()))
        self.__players = {}
        self.__name = name
        self.__port_tcp = 0
        self.__accept_thread = threading.Thread(target=self.accept_connections)
        self.__sock = None
        self.__accepting_connections = True
        self.__time_of_last_connection = 0
        self.__state = State.INACTIVE
        self.__ui = CLI(clr=False)  # TODO change this to default once done
        self.__topic = topic
        self.__questions = get_trivia_questions(topic)

    def send_broadcast(self, data: str, port: int) -> None:
        """
        Sends a broadcast message, asking players to join the game
        :param data: The data to send
        :param port: The port to send the data to
        :return: None
        """
        super().send_broadcast(create_broadcast(data, port), port)
        # TODO potentially use try-catch?

    def __send_broadcast(self) -> None:
        """
        Sends a broadcast message, asking players to join the game
        :return: None
        """
        self.send_broadcast(self.__name, self.__port_tcp)

    def start(self) -> None:
        """
        Starts the game
        :return: None
        """
        self.__state = State.SENDING_OFFERS
        while self.__state != State.TERMINATED:
            self.__gameloop()

        self.stop()

    def __gameloop(self) -> None:
        self.__sock = socket()
        self.__sock.bind((self.ip, 0))
        self.__port_tcp = self.__sock.getsockname()[1]
        self.__sock.listen()

        self.__ui.display(f"Server started, listening on IP address {augment(self.ip, 'blue')}")

        self.__accepting_connections = True
        self.__accept_thread.start()
        self.__ui.display(f"IM HERE {augment(self.ip, 'blue')}")
        # send offer requests every 1 second
        self.__state = State.SENDING_OFFERS
        self.__time_of_last_connection = time.time()
        self.__ui.display(f"IM HERE2 {augment(self.ip, 'blue')}")
        while self.__accepting_connections:
            self.__send_broadcast()

            # Debugging the number of players
            self.__ui.display(f"Number of players connected: {len(self.__players)}")

            if len(self.__players) >= 2:
                self.__accepting_connections = False
                self.__ui.display(f"Enough players connected, breaking out of loop")

            time.sleep(BROADCAST_SEND_INTERVAL)
            self.__ui.display(f"IM HERE3 {augment(self.ip, 'blue')}")

            if time.time() - self.__time_of_last_connection > QUESTION_TIMEOUT:
                self.__accepting_connections = False
                self.__accept_thread.join()

        # check if there are enough players
        self.__ui.display(f"IM HERE4 {augment(self.ip, 'blue')}")

        if len(self.__players) < 2:
            self.send_to_all(create_message(Opcode.END, "Not enough players to start the game"))
            self.__state = State.INACTIVE
            return

        self.__state = State.GAME_STARTED
        self.send_to_all(create_message(
            Opcode.START, f"Welcome to the {augment(self.__name, 'blue')} server, "
                          f"where we are answering trivia questions about {augment(self.__topic, 'underline')}!"))
        # TODO implement game logic
        while len(self.__players) > 1:
            # Get a random trivia question
            question, is_true = random.choice(self.__questions)
            self.send_to_all(create_message(Opcode.QUESTION, f"This statement is True or False? {question}"))

            # Give players time to respond
            start_time = time.time()
            answers = {}

            while time.time() - start_time < QUESTION_TIMEOUT:
                for player_name, player in list(self.__players.items()):
                    if player_name not in answers:
                        try:
                            answer = player.sock.recv(1024).decode().strip().upper()  # Receive and normalize answer
                            if answer:
                                answers[player_name] = answer
                                self.send_to_all(create_message(Opcode.INFO, f"{player_name} answered: {answer}"))
                        except ConnectionResetError:
                            # Handle player disconnection
                            self.__players.pop(player_name)
                            self.send_to_all(create_message(Opcode.INFO, f"{player_name} has disconnected."))

            # Evaluate the answers and update scores
            correct_answers = {"Y", "T", "1"} if is_true else {"N", "F", "0"}
            for player_name, answer in answers.items():
                player = self.__players[player_name]
                if answer in correct_answers:
                    player.increment_score()
                    self.send_to(player, create_message(Opcode.INFO, "Correct! You've earned a point."))
                else:
                    self.send_to(player, create_message(Opcode.INFO, "Incorrect! Better luck next time."))

            # Check if the game is over
            if len(self.__players) < 1:
                break  # End the game if there are no players left

            # Notify all players that the round is over and proceed to the next question
            self.send_to_all(create_message(Opcode.INFO, "Round over. Next question..."))

        # Announce the winner or game over
        if len(self.__players) == 1:
            winner = list(self.__players.values())[0]
            self.send_to_all(create_message(Opcode.END, f"Game over! Congratulations to the winner: {winner.name}"))
        else:
            self.send_to_all(create_message(Opcode.END, "Game over! No winner this time."))

        self.__sock.close()

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

    def accept_connections(self) -> None:
        """
        Accepts connections from players
        :return: None
        """
        while self.__accepting_connections:
            conn, addr = self.__sock.accept()
            self.accept_connection(Player(conn, addr, "Player" + str(len(self.__players) + 1)))
            self.__time_of_last_connection = time.time()

    def accept_connection(self, conn: Player) -> None:
        """
        Accepts a connection from a player
        :param conn: The player to accept
        :return: None
        """
        self.__players[conn.name] = conn
        self.send_to(conn, create_message(Opcode.INFO, f"Welcome to {self.__name}, {conn.name}!"))

    def __leader(self) -> Player:
        """
        Returns the player with the highest score
        :return: The leader
        """
        return max(self.__players.values())

    @property
    def name(self) -> str:
        return self.__name


def main() -> None:
    server = TriviaServer()
    server.start()


if __name__ == "__main__":
    main()
