from src.ui.userinterface import UserInterface


class CLI(UserInterface):
    def display(self, message: str) -> None:
        """
        Displays a message to the user
        :param message: The message to display
        :return: None
        """
        print(message)

    def get_input(self, prompt: str) -> str:
        """
        Gets input from the user
        :param prompt: The prompt to display
        :return: The user's input
        """
        return input(prompt)
