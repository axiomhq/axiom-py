"""This module contains helper functions for tests."""

import random
from datetime import datetime


def get_random_name() -> str:
    random_string = ""

    for _ in range(10):
        random_integer = random.randint(97, 122)
        # Keep appending random characters using chr(x)
        random_string += chr(random_integer)

    return random_string


def parse_time(txt: str) -> datetime:
    return datetime.strptime(txt, "%Y-%m-%dT%H:%M:%S.%f")
