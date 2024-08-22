import random
import threading
import time
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
        super().send_broadcast(create_broadcast(data, port), PORT_UDP)
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
            self.__reset_game()

        self.stop()

    def __gameloop(self) -> None:
        self.__sock = socket()
        self.__sock.bind((self.ip, 0))
        self.__port_tcp = self.__sock.getsockname()[1]
        self.__sock.listen()

        self.__ui.display(f"Server started, listening on IP address {augment(self.ip, 'blue')}")

        self.__accepting_connections = True
        self.__accept_thread.start()
        # send offer requests every 1 second
        self.__state = State.SENDING_OFFERS
        self.__time_of_last_connection = time.time()
        while self.__accepting_connections:
            self.__send_broadcast()

            # Debugging the number of players
            # self.__ui.display(f"Number of players connected: {len(self.__players)}")

            time.sleep(BROADCAST_SEND_INTERVAL)

            if time.time() - self.__time_of_last_connection > QUESTION_TIMEOUT \
                    and len(self.__players) >= MINIMUM_PLAYERS:
                self.__accepting_connections = False
                self.__accept_thread.join()

        if len(self.__players) < MINIMUM_PLAYERS:
            self.send_to_all(create_message(Opcode.END, "Not enough players to start the game"))
            return

        self.__state = State.GAME_STARTED
        self.send_to_all(create_message(
            Opcode.START, f"Welcome to the {augment(self.__name, 'blue')} server, "
                          f"where we are answering trivia questions about {augment(self.__topic, 'underline')}!"))
        while len(self.__players) >= MINIMUM_PLAYERS and len(self.__questions) > 0:
            # Get a random trivia question
            question = random.choice(list(self.__questions.keys()))
            correct_answer = self.__questions[question]
            self.send_to_all(create_message(Opcode.QUESTION, question))

            # Give players time to respond
            start_time = time.time()
            answers = {}

            while time.time() - start_time < QUESTION_TIMEOUT:
                for player_name, player in list(self.__players.items()):
                    if player_name not in answers:
                        try:
                            # TODO change to non-blocking!
                            answer = answer_literal_to_bool(get_message(player.sock.recv(1024).decode()))
                            if answer:
                                answers[player_name] = answer
                                self.send_to_all(create_message(Opcode.INFO, f"{player_name} answered: {answer}"))
                                # TODO remove this send after debugging
                        except ConnectionResetError:  # TODO this probably needs to be somewhere else
                            # Handle player disconnection
                            self.__players.pop(player_name)
                            self.send_to_all(create_message(Opcode.INFO, f"{player_name} has disconnected."))
                            # TODO remove this send after debugging

            # Evaluate the answers and update scores
            for player_name, answer in answers.items():
                player = self.__players[player_name]
                if answer is correct_answer:
                    player.increment_score()
                    self.send_to(player, create_message(Opcode.POSITIVE, "Correct! You've earned a point."))
                else:
                    self.send_to(player, create_message(Opcode.NEGATIVE, "Incorrect! Better luck next time."))

            # Remove the question from the list of questions
            self.__questions.pop(question)

        # Announce the winner or game over
        if (len(self.__players) == 1 or len(self.__questions) == 0) and self.__leader().score > 0:
            winner = self.__leader()
            self.send_to_all(create_message(Opcode.END, f"Game over! Congratulations to the winner: {winner.name}"))
        else:
            self.send_to_all(create_message(Opcode.END, "Game over! No winner this time."))

    def stop(self) -> None:
        pass

    def __reset_game(self) -> None:
        """
        Ends the game, announce the winner
        :return: None
        """
        self.__state = State.INACTIVE
        self.__players.clear()
        self.__questions = get_trivia_questions(self.__topic)
        if self.__accept_thread.is_alive():
            self.__accepting_connections = False
            self.__accept_thread.join()
        if self.__sock:
            self.__sock.close()
        self.__sock = None

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
