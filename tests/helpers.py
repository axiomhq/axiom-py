"""This module contains helper functions for tests."""

import os
import random
from datetime import datetime


def get_random_name() -> str:
    """Generate a random dataset name.

    If AXIOM_DATASET_SUFFIX is set, use it as a suffix for easier cleanup.
    Otherwise, generate a random string.
    """
    suffix = os.getenv("AXIOM_DATASET_SUFFIX")
    if suffix:
        random_part = "".join(chr(random.randint(97, 122)) for _ in range(6))
        return f"test-axiom-py-{random_part}-{suffix}"

    random_string = ""
    for _ in range(10):
        random_integer = random.randint(97, 122)
        random_string += chr(random_integer)

    return random_string


def parse_time(txt: str) -> datetime:
    return datetime.strptime(txt, "%Y-%m-%dT%H:%M:%S.%f")
