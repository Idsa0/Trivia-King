from inputimeout import inputimeout, TimeoutOccurred

from src.ui.ansi import CLEAR
from src.ui.userinterface import UserInterface


class CLI(UserInterface):
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
