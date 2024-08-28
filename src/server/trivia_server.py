import random
import sys
import threading
import time
from socket import socket, gethostname, gethostbyname

from src.server.questions import get_trivia_questions, QuestionLiteral
from src.server.server import Server, Connection
from src.shared.protocol import *
from src.ui.ansi import augment
from src.ui.cli import CLI
from src.ui.userinterface import UserInterface


class Player(Connection):
    """
    Represents a player in the trivia game
    """

    def __init__(self, sock: socket, addr: tuple[str, int], name: str) -> None:
        super().__init__(sock, addr)
        self.__name = name
        self.__score = 0

    @property
    def name(self) -> str:
        """
        :return: The name of the player
        """
        return self.__name

    @name.setter
    def name(self, name: str) -> None:
        """
        Sets the name of the player
        :param name: The new name
        :return: None
        """
        self.__name = name

    @property
    def score(self) -> int:
        """
        :return: The score of the player
        """
        return self.__score

    def increment_score(self) -> None:
        """
        Increments the score of the player
        :return: None
        """
        self.__score += 1

    def __str__(self) -> str:
        """
        :return: A string representation of the player
        """
        return f"{self.__name} : {self.__score}"

    def __cmp__(self, other) -> int:
        """
        Compares the player with another player
        :param other: The other player
        :return: The difference in scores
        """
        if not isinstance(other, Player):
            raise ValueError(f"Cannot compare Player with {type(other)}")
        return self.score - other.score

    def __lt__(self, other) -> bool:
        """
        Compares the player with another player
        :param other: The other player
        :return: Returns True if the player has a lower score than the other player
        """
        return self.__cmp__(other) < 0


class State(Enum):
    """
    Represents the state of the server
    """

    INACTIVE = 0x1
    """
    The server is not running
    """
    SENDING_OFFERS = 0x2
    """
    The server is sending offers to players
    """
    GAME_STARTED = 0x4
    """
    The game has started
    """
    TERMINATED = 0x8
    """
    The server is terminating
    """


class TriviaServer(Server):
    """
    A dedicated server for hosting trivia games, uses the UDP protocol for broadcasting
    and the TCP protocol for communication with players, uses a thread-per-client model
    """

    __BUFFER_SIZE = 1024  # buffer size for receiving messages
    __NAME_DEFAULT = "n3tw0rk1ng_m@st3r5"  # default name for the server
    __DEFAULT_ROUNDS_PER_GAME = 1  # default number of rounds per game
    __TIME_BETWEEN_RESULTS = 0.5  # time to wait when showing players the results, for cosmetic purposes

    def __init__(self, name: str = __NAME_DEFAULT, topic: QuestionLiteral = "networking",
                 rounds_per_game: int = __DEFAULT_ROUNDS_PER_GAME) -> None:
        if len(name) > SERVER_NAME_LENGTH:
            raise ValueError(f"Name too long, must be less than {SERVER_NAME_LENGTH} characters")

        super().__init__(ip=gethostbyname(gethostname()))
        self.__name: str = name
        self.__topic: QuestionLiteral = topic
        self.__rounds_per_game: int = rounds_per_game
        self.__sock: socket = socket()
        self.__port_tcp: int = 0
        self.__accept_thread: threading.Thread = threading.Thread(target=self.accept_connections)
        self.__connection_threads: dict[str, threading.Thread] = {}
        self.__accepting_connections: bool = True
        self.__time_of_last_connection: float = 0
        self.__players: dict[str, Player] = {}
        self.__state: State = State.INACTIVE
        self.__ui: UserInterface = CLI()
        self.__questions: dict[str, bool] = get_trivia_questions(topic)
        self.__answers: dict[str, bool | None] = {}
        self.__lock: threading.Lock = threading.Lock()
        self.__ui_lock: threading.Lock = threading.Lock()

    def send_broadcast(self, data: str, port: int) -> None:
        """
        Sends a broadcast message, asking players to join the game
        :param data: The data to send
        :param port: The port which the server is listening on
        :return: None
        """
        super().send_broadcast(create_broadcast(data, port), PORT_UDP)

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
        try:
            self.__state = State.SENDING_OFFERS
            while self.__state != State.TERMINATED:
                self.__gameloop()
                self.__reset_game()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def __gameloop(self) -> None:
        """
        The main game loop, handles the game logic for a single game
        :return: None
        """

        self.__sock.bind(('', 0))
        self.__port_tcp = self.__sock.getsockname()[1]
        self.__sock.listen()

        with self.__ui_lock:
            self.__ui.display(f"Server started, listening on IP address {augment(self.ip, 'blue')}")

        self.__accepting_connections = True
        self.__accept_thread.start()
        # send offer requests every 1 second
        self.__state = State.SENDING_OFFERS
        self.__time_of_last_connection = time.time()
        while self.__accepting_connections:
            self.__send_broadcast()

            time.sleep(BROADCAST_SEND_INTERVAL)

            # stop sending offers if no one has connected for a while and there are enough players
            if time.time() - self.__time_of_last_connection > QUESTION_TIMEOUT \
                    and self.player_count >= MINIMUM_PLAYERS:
                self.__accepting_connections = False
                self.__accept_thread.join(0)

        # extremely rare race condition where a player disconnects after the game has started
        if self.player_count < MINIMUM_PLAYERS:
            self.send_to_all(create_message(Opcode.END, augment("Not enough players to start the game", "red")))
            return

        self.__state = State.GAME_STARTED
        self.send_to_all(create_message(
            Opcode.START, f"Welcome to the {augment(self.__name, 'blue')} server, "
                          f"where we are answering trivia questions about {augment(self.__topic, 'underline')}!"))
        with self.__ui_lock:
            self.__ui.display(f"Game started! Topic: {self.__topic}")

        _round = 0
        # send questions to players until there are not enough players, no more questions, or the game is over
        while self.__legal_game_state(_round):
            with self.__lock:
                players = "\n".join([str(player) for player in self.__players.values()])
            self.send_to_all(create_message(Opcode.INFO, f"\nRound {_round + 1}\nCurrent Scores:\n{players}\n"))
            with self.__ui_lock:
                self.__ui.display(f"\nRound {_round + 1}\nCurrent Scores:\n{players}\n")

            # Get a random trivia question
            question, correct_answer = random.choice(list(self.__questions.items()))
            with self.__ui_lock:
                self.__ui.display(
                    f"Question: {question}\nAnswer: {augment(correct_answer, 'green' if correct_answer else 'red')}")
            time.sleep(self.__TIME_BETWEEN_RESULTS)  # give players time to see the results
            self.send_to_all(create_message(Opcode.QUESTION, question))

            # Give players time to respond
            time.sleep(QUESTION_TIMEOUT)

            # Evaluate the answers and update scores
            with self.__lock:
                for player_name, answer in self.__answers.items():
                    player = self.__players[player_name]
                    if answer is correct_answer:
                        player.increment_score()
                        self.send_to(player, create_message(Opcode.POSITIVE, "Correct! You've earned a point."))
                        with self.__ui_lock:
                            self.__ui.display(augment(f"{player.name} answered correctly!", "italic"))
                    else:
                        self.send_to(player, create_message(Opcode.NEGATIVE, "Incorrect! Better luck next time."))
                        with self.__ui_lock:
                            self.__ui.display(augment(f"{player.name} answered incorrectly.", "italic"))

            # Remove the question from the list of questions
            self.__questions.pop(question)
            _round += 1
            self.__answers.clear()
            time.sleep(self.__TIME_BETWEEN_RESULTS)  # give players time to see the results

        # Announce the winner or game over
        if (self.player_count == 1 or self.question_count == 0 or _round == self.__rounds_per_game) \
                and self.__leader().score > 0:
            winner = self.__leader()
            self.send_to_all(create_message(
                Opcode.END, f"Game Over! Congratulations to the winner: {winner.name}"))
            with self.__ui_lock:
                self.__ui.display(augment(f"Game Over! {winner.name} is the winner!", "italic"))
        else:
            self.send_to_all(create_message(Opcode.END, "Game Over! No winner this time."))
            with self.__ui_lock:
                self.__ui.display(augment("Game Over! No winner this time.", "italic"))

    def __legal_game_state(self, _round: int):
        """
        Determines if the game is in a legal state
        :param _round: The current round
        :return: True if the game is in a legal state
        """
        return self.player_count >= MINIMUM_PLAYERS and self.question_count > 0 and _round < self.__rounds_per_game

    def stop(self) -> None:
        """
        Stops the server
        :return: None
        """
        self.__reset_game()
        with self.__ui_lock:
            self.__ui.display(augment("Server shutting down...", "red"))

    def __reset_game(self) -> None:
        """
        Resets the server to its initial state
        :return: None
        """
        try:
            with self.__lock:
                self.__state = State.INACTIVE
                if self.__accept_thread.is_alive():
                    self.__accepting_connections = False
                    self.__accept_thread.join(0)
                del self.__accept_thread
                self.__accept_thread = threading.Thread(target=self.accept_connections)
                for thread in self.__connection_threads.values():
                    thread.join(0)
                    del thread
                self.__connection_threads.clear()
                self.__questions = get_trivia_questions(self.__topic)
                if self.__sock:
                    self.__sock.close()
                    del self.__sock
                self.__sock = socket()
                for player in self.__players.values():
                    player.sock.close()
                self.__players.clear()
                self.__answers.clear()
                self.__time_of_last_connection = 0
        except KeyboardInterrupt:
            # exit gracefully, an uncaught KeyboardInterrupt here will otherwise be caught incorrectly
            with self.__ui_lock:
                self.__ui.display(augment("Server shutting down...", "red"))
            sys.exit(0)

    def send_to(self, conn: Connection, data: str) -> None:
        """
        Sends a message to a specific player
        :param conn: The player to send the message to
        :param data: The data to send
        :return: None
        """
        try:
            conn.sock.send(data.encode())
        except OSError:
            # this should only happen in the rare case that the player disconnects
            # while the server is sending a message
            pass

    def send_to_all(self, data: str) -> None:
        """
        Sends a message to all players
        :param data: The data to send
        :return: None
        """
        with self.__lock:
            for player in self.__players.values():
                self.send_to(player, data)

    def accept_connections(self) -> None:
        """
        Accepts connections from players
        :return: None
        """
        while self.__accepting_connections:
            try:
                conn, addr = self.__sock.accept()
            except OSError:
                return
            player = Player(conn, addr, f"Player{self.player_count + 1}")
            self.accept_connection(player)
            with self.__ui_lock:
                self.__ui.display(f"Accepted connection from {player.name}")
            self.__time_of_last_connection = time.time()

    def accept_connection(self, conn: Player) -> None:
        """
        Accepts a connection from a player
        :param conn: The player to accept
        :return: None
        """
        with self.__lock:
            self.__players[conn.name] = conn
            self.__connection_threads[conn.name] = threading.Thread(target=self.__handle_connection, args=(conn,))
            self.__connection_threads[conn.name].start()

    def __handle_connection(self, player: Player) -> None:
        """
        Handles a connection from a player
        :param player: The player to handle
        :return: None
        """
        while self.__state != State.TERMINATED:
            try:
                data = player.sock.recv(self.__BUFFER_SIZE)
                if not data:
                    continue
                opcode = get_opcode(data)
                msg = get_message(data)
                match opcode:
                    case Opcode.ANSWER:
                        # If the game has started, store the answer
                        if self.__state == State.GAME_STARTED:
                            with self.__lock:
                                self.__answers[player.name] = answer_literal_to_bool(msg)
                    case Opcode.RENAME:
                        # If the game has started, do not allow renaming
                        if self.__state == State.GAME_STARTED:
                            self.send_to(player, create_message(Opcode.INFO, "Cannot rename during game"))
                        else:
                            self.__rename_player(player, msg)
                            self.send_to(player, create_message(Opcode.INFO,
                                                                f"Henceforth, you shall be known as {player.name}"))
                    case _:
                        pass
            except ConnectionResetError:
                # Handle player disconnect
                with self.__lock:
                    p = self.__players.pop(player.name)
                p.sock.close()
                self.send_to_all(create_message(Opcode.INFO, f"{player.name} has disconnected."))
                with self.__ui_lock:
                    self.__ui.display(f"{player.name} has disconnected.")
                with self.__lock:
                    self.__connection_threads.pop(player.name)
                return
            except ConnectionAbortedError:
                # carefully handle player disconnect,
                # while technically reused code, we must ensure fully synchronized access>
                # POTENTIAL future improvement: refactor to a common method: __handle_disconnect(self, player)
                with self.__lock:
                    if player.name in self.__players:
                        p = self.__players.pop(player.name)
                        p.sock.close()
                self.send_to_all(create_message(Opcode.INFO, f"{player.name} has disconnected."))
                with self.__lock:
                    self.__ui.display(f"{player.name} has disconnected.")
                    if player.name in self.__connection_threads:
                        self.__connection_threads.pop(player.name)
                return
            except OSError:
                return

    def __rename_player(self, player: Player, new_name: str) -> None:
        """
        Renames a player
        :param player: The player to rename
        :param new_name: The new name
        :return: None
        """
        with self.__lock:
            while new_name in self.__players:
                # If the name is already taken, append a random digit to the name
                new_name += random.choice("0123456789")
            else:
                old_name = player.name
                player.name = new_name
                self.__players[new_name] = self.__players.pop(old_name)
                self.__connection_threads[new_name] = self.__connection_threads.pop(old_name)
                with self.__ui_lock:
                    self.__ui.display(f"{old_name} is now known as {new_name}")

    def __leader(self) -> Player:
        """
        Returns the player with the highest score
        :return: The leader
        """
        with self.__lock:
            return max(self.__players.values())

    @property
    def name(self) -> str:
        """
        :return: The name of the server
        """
        return self.__name

    @property
    def topic(self) -> QuestionLiteral:
        """
        :return: The topic of the trivia questions
        """
        return self.__topic

    @property
    def player_count(self) -> int:
        """
        :return: The number of players connected to the server
        """
        with self.__lock:
            return len(self.__players)

    @property
    def question_count(self) -> int:
        """
        :return: The number of questions remaining
        """
        return len(self.__questions)


def main() -> None:
    server = TriviaServer()
    server.start()


if __name__ == "__main__":
    main()
