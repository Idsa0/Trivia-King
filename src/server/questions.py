import csv
import os
from typing import Literal

QuestionLiteral = Literal["networking"]


def get_trivia_questions(questions: QuestionLiteral = "networking") -> dict[str, bool]:
    """
    Get a dictionary of trivia questions and their answers.
    :param questions: The category of questions to get.
    :return: The requested questions as a dictionary.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, 'questions', f"{questions}.csv")

    with open(path, mode='r') as infile:
        reader = csv.reader(infile)
        q_dict = {rows[0]: bool(rows[1]) for rows in reader}
        q_dict.pop("Question")  # Remove the header
    return q_dict
