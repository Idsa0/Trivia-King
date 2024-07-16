from src.ui.userinterface import UserInterface


class CLI(UserInterface):
    _ANSI_COLORS = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m"
    }
    _ANSI_FORMATS = {
        "bold": "\033[1m",
        "italic": "\033[3m",
        "underline": "\033[4m",
        "reversed": "\033[7m",
        "strikethrough": "\033[9m",
        "double_underline": "\033[21m"
    }
    _ANSI_END = "\033[0m"
    _ANSI = {**_ANSI_COLORS, **_ANSI_FORMATS, "end": _ANSI_END}

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

    def augment(self, message: str, *args: str) -> str:
        """
        Augments the message with ANSI escape codes
        :param message: The message to augment
        :param args: The arguments to augment the message with
        :return: The augmented message, priority is given to the first argument
        :raises ValueError: If an invalid argument is passed
        """
        for arg in args:
            if arg not in self.ansi:
                raise ValueError(f"Invalid argument: {arg}")
            message = f"{self.ansi[arg]}{message}{self.ansi['end']}"

        return message

    @property
    def ansi(self):
        return self._ANSI

    @property
    def ansi_colors(self):
        return self._ANSI_COLORS

    @property
    def ansi_formats(self):
        return self._ANSI_FORMATS

    @property
    def ansi_end(self):
        return self._ANSI_END
