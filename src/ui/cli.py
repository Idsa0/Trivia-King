from src.ui.userinterface import UserInterface
from src.ui.ansi import CLEAR


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

    def get_input(self, prompt: str = "") -> str:
        """
        Gets input from the user
        :param prompt: (Optional) The prompt to display
        :return: The user's input
        """
        return input(prompt)

    def get_boolean_input(self, prompt: str, failure_prompt: str = None, max_attempts: int = 0) -> bool:
        """
        Gets a boolean input from the user
        :param prompt: The prompt to display
        :param failure_prompt: (Optional) Prompt to display if the user's input is invalid
        :param max_attempts: (Optional) The maximum number of attempts
        :return: The user's input
        """
        attempt = 0
        while max_attempts <= 0 or attempt < max_attempts:
            response = input(prompt).lower()
            if response in self.__ANSWER_LITERALS:
                return self.__ANSWER_LITERALS[response]

            if failure_prompt:
                print(failure_prompt)

            attempt += 1
