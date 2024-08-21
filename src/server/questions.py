import csv
from typing import Literal

QuestionLiteral = Literal["networking"]


def get_trivia_questions(questions: QuestionLiteral = "networking") -> dict[str: bool]:
    """
    Get a dictionary of trivia questions and their answers
    :param questions: The category of questions to get
    :return: The requested questions
    """
    if __name__ == "__main__":
        path = f"questions/{questions}.csv"
    else:
        path = f"src/server/questions/{questions}.csv"
    # TODO fix this so it works from any directory

    with open(path, mode='r') as infile:
        reader = csv.reader(infile)
        mydict = {rows[0]: bool(rows[1]) for rows in reader}
        mydict.pop("Question")  # Remove the header
    return mydict