import struct
from enum import Enum


class Opcode(Enum):  # TODO change this to reflect the actual requirements
    ABORT = 0x1  # indicates the end of the game and the client should terminate
    START = 0x2  # indicates the start of the game
    END = 0x4  # indicates the end of the game
    QUESTION = 0x8  # indicates a question
    INFO = 0x10  # indicates an informational message
    POSITIVE = 0x20  # indicates a positive response
    NEGATIVE = 0x40  # indicates a negative response
    UNKNOWN = 0x80  # indicates an unknown message


PORT_UDP = 13117
BROADCAST_LENGTH = 39
BROADCAST_MAGIC_COOKIE = 0xABCDDCBA
BROADCAST_MESSAGE_TYPE = 0x2
BROADCAST_NAME_SLICE = slice(5, 36)
BROADCAST_PORT_SLICE = slice(37, 39)

QUESTION_TIMEOUT = 10


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
    print(data)  # TODO remove
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
    return data[1:].decode()
