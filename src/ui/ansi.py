from random import choice

__ANSI_COLORS: dict[str, str] = {  # ANSI escape codes for colors
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "purple": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m"
}
__ANSI_FORMATS: dict[str, str] = {  # ANSI escape codes for formats
    "bold": "\033[1m",
    "italic": "\033[3m",
    "underline": "\033[4m",
    "reversed": "\033[7m",
    "strikethrough": "\033[9m",
    "double_underline": "\033[21m"
}
__ANSI_END: str = "\033[0m"  # ANSI escape code to end formatting
ANSI: dict[str, str] = {**__ANSI_COLORS, **__ANSI_FORMATS, "end": __ANSI_END}  # ANSI escape codes

CLEAR: str = "\033[H\033[J"  # ANSI escape code to clear the screen


def augment(message: str, *args: str) -> str:
    """
    Augments the message with ANSI escape codes
    :param message: The message to augment
    :param args: The arguments to augment the message with
    :return: The augmented message, priority is given to the first argument
    :raises ValueError: If an invalid argument is passed
    """
    for arg in args:
        if arg not in ANSI:
            raise ValueError(f"Invalid argument: {arg}")
        message = f"{ANSI[arg]}{message}{ANSI['end']}"

    return message


def random_color() -> str:
    """
    Returns a random color
    :return: A random color
    """
    return choice(list(__ANSI_COLORS.keys()))


def random_format() -> str:
    """
    Returns a random format
    :return: A random format
    """
    return choice(list(__ANSI_FORMATS.keys()))


def rainbowify(message: str) -> str:
    """
    Paints each character in the message with a random color
    :param message: The message to rainbowify
    :return: The rainbowified message
    """
    return "".join(augment(char, random_color()) for char in message)


def clean(message: str) -> str:
    """
    Removes all ANSI escape codes from the message
    :param message: The message to clean
    :return: The cleaned message
    """
    for ansi in ANSI.values():
        message = message.replace(ansi, "")
    return message
