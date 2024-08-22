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
    def clear(self) -> None:
        """
        Clears the screen
        :return: None
        """
        pass

    @abstractmethod
    def get_input(self, prompt: str = "", timeout: int = -1) -> str | None:
        """
        Gets input from the user
        :param prompt: (Optional) The prompt to display
        :param timeout: (Optional) The timeout in seconds
        :return: The user's input
        """
        pass
