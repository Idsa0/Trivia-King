import struct
from enum import Enum


class Opcode(Enum):
    ABORT = 0x1  # indicates the end of the game and the client should terminate
    START = 0x2  # indicates the start of the game
    END = 0x4  # indicates the end of the game
    QUESTION = 0x8  # indicates a question
    ANSWER = QUESTION  # indicates an answer
    INFO = 0x10  # indicates an informational message
    RENAME = INFO  # indicates a rename request
    POSITIVE = 0x20  # indicates a positive response
    NEGATIVE = 0x40  # indicates a negative response
    UNKNOWN = 0x80  # indicates an unknown message


PORT_UDP = 13117
BROADCAST_LENGTH = 39
BROADCAST_MAGIC_COOKIE = 0xABCDDCBA
BROADCAST_MESSAGE_TYPE = 0x2
BROADCAST_NAME_SLICE = slice(5, 36)
BROADCAST_PORT_SLICE = slice(37, 39)
SERVER_NAME_LENGTH = 32

WAIT_FOR_PLAYER_JOIN_TIMEOUT = 10
BROADCAST_SEND_INTERVAL = 1
QUESTION_TIMEOUT = 10
MINIMUM_PLAYERS = 2

__ANSWER_LITERALS = {"y": True, "n": False,
                     "yes": True, "no": False,
                     "true": True, "false": False,
                     "t": True, "f": False,
                     "1": True, "0": False}


def create_broadcast(name: str, port: int) -> bytes:
    """
    Creates a broadcast message
    :param name: The name of the server
    :param port: The port of the server
    :return: The encoded broadcast message
    """
    return struct.pack("!IB32sH",
                       BROADCAST_MAGIC_COOKIE,
                       BROADCAST_MESSAGE_TYPE,
                       name.ljust(SERVER_NAME_LENGTH).encode(),
                       port)


def create_message(opcode: Opcode, message: str) -> str:
    """
    Creates a message with the given opcode
    :param opcode: The opcode of the message
    :param message: The content of the message
    :return: The resulting message
    """
    # TODO I really dislike this hack
    return (struct.pack("!B", opcode.value) + message.encode()).decode()


def validate_broadcast(data: bytes) -> bool:
    """
    Validates a broadcast message
    :param data: The data to validate
    :return: True if the data follows the broadcast format, False otherwise
    """
    return len(data) == BROADCAST_LENGTH and data.startswith(
        struct.pack("!IB", BROADCAST_MAGIC_COOKIE, BROADCAST_MESSAGE_TYPE))


def get_server_name(data: bytes) -> str:
    """
    Extracts the server name from a broadcast message
    :param data: The data to extract from
    :return: The server name
    """
    return data[BROADCAST_NAME_SLICE].strip().decode()


def get_server_port(data: bytes) -> int:
    """
    Extracts the server port from a broadcast message
    :param data: The data to extract from
    :return: The server port
    """
    return struct.unpack("!H", data[BROADCAST_PORT_SLICE])[0]


def get_opcode(data: bytes) -> Opcode:
    """
    Extracts the opcode from a message
    :param data: The data to extract from
    :return: The opcode
    """
    try:
        return Opcode(data[0])
    except ValueError:
        return Opcode.UNKNOWN


def get_message(data: bytes) -> str:
    """
    Extracts the message from a message
    :param data: The data to extract from
    :return: The message
    """
    return (data[1:]).decode()


def answer_literal_to_bool(answer: str) -> bool | None:
    """
    Converts a string answer to a boolean
    :param answer: The answer to convert
    :return: The converted answer or None if the answer is invalid
    """
    normalized = answer.lower().strip()
    if normalized in __ANSWER_LITERALS:
        return __ANSWER_LITERALS[normalized]
    return None
