from typing import List
from .util import Util
from dataclasses import dataclass
from requests import Session


@dataclass
class User:
    """An authenticated axiom user."""

    id: str
    name: str
    emails: List[str]


class UsersClient:
    """The UsersClient is a client for the Axiom Users service."""

    def __init__(self, session: Session):
        self.session = session

    def current(self) -> User:
        """Get the current authenticated user."""
        res = self.session.get("user")
        user = Util.from_dict(User, res.json())
        return user
