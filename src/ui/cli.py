from time import time

from inputimeout import inputimeout, TimeoutOccurred

from src.ui.ansi import CLEAR
from src.ui.userinterface import UserInterface


class CLI(UserInterface):
    __ANSWER_LITERALS = {"y": True, "n": False,
                         "yes": True, "no": False,
                         "true": True, "false": False,
                         "t": True, "f": False,
                         "1": True, "0": False}

    def __init__(self, clr: bool = True) -> None:
        """
        Initializes the CLI
        :param clr: (Optional) Whether to clear the screen on initialization (default is True)
        """
        if clr:
            self.clear()

    def display(self, message: str) -> None:
        """
        Displays a message to the user
        :param message: The message to display
        :return: None
        """
        print(message)

    def clear(self) -> None:
        """
        Clears the screen
        :return: None
        """
        print(CLEAR, end="")

    def get_input(self, prompt: str = "", timeout: int = -1) -> str | None:
        """
        Gets input from the user
        :param prompt: (Optional) The prompt to display
        :param timeout: (Optional) The timeout in seconds
        :return: The user's input
        """
        try:
            return inputimeout(prompt, timeout)
        except TimeoutOccurred:
            return None

    def get_boolean_input(self, prompt: str, failure_prompt: str = None, max_attempts: int = 0,
                          timeout: int = -1) -> bool | None:
        """
        Gets a boolean input from the user
        :param prompt: The prompt to display
        :param failure_prompt: (Optional) Prompt to display if the user's input is invalid
        :param max_attempts: (Optional) The maximum number of attempts
        :param timeout: (Optional) The timeout in seconds
        :return: The user's input
        """
        attempt = 0
        elapsed = 0
        start = time()

        while (max_attempts <= 0 or attempt < max_attempts) and elapsed < timeout:
            try:
                response = inputimeout(prompt, timeout - elapsed)
            except TimeoutOccurred:
                return None

            if response in self.__ANSWER_LITERALS:
                return self.__ANSWER_LITERALS[response]

            if failure_prompt:
                print(failure_prompt)

            attempt += 1
            elapsed = time() - start

            # TODO check that the timing logic is correct

        return None
