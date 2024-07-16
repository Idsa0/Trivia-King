from abc import ABC, abstractmethod


class UserInterface(ABC):
    @abstractmethod
    def display(self, message: str) -> None:
        """
        Displays a message to the user
        :param message: The message to display
        :return: None
        """
        pass

    @abstractmethod
    def get_input(self, prompt: str) -> str:
        """
        Gets input from the user
        :param prompt: The prompt to display
        :return: The user's input
        """
        pass
