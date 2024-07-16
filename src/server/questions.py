from typing import Literal
import csv


def get_trivia_questions(questions: Literal["networking"] = "networking") -> dict[str: bool]:
    """
    Get a dictionary of trivia questions and their answers
    :param questions: The category of questions to get
    :return: The requested questions
    """
    with open("questions/" + questions + '.csv', mode='r') as infile:
        reader = csv.reader(infile)
        mydict = {rows[0]: bool(rows[1]) for rows in reader}
        mydict.pop("Question")  # Remove the header
    return mydict
