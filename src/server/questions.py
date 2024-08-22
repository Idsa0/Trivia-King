import csv
import os
from typing import Literal

QuestionLiteral = Literal["networking", "demo"]


def get_trivia_questions(questions: QuestionLiteral = "networking") -> dict[str, bool]:
    """
    Get a dictionary of trivia questions and their answers.

    Usage warning - this function assumes that the questions are stored in a CSV file in the 'questions' directory
    and that the first column is the question and the second column is the answer.
    :param questions: The category of questions to get.
    :return: The requested questions as a dictionary.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, 'questions', f"{questions}.csv")

    with open(path, mode='r') as infile:
        reader = csv.reader(infile)
        q_dict = {rows[0]: rows[1] == "True" for rows in reader}
        q_dict.pop("Question")  # Remove the header
    return q_dict
