from .util import from_dict
from dataclasses import dataclass
from requests import Session


@dataclass
class Role:
    id: str
    name: str


@dataclass
class User:
    """An authenticated axiom user."""

    id: str
    name: str
    email: str
    role: Role


class UsersClient:
    """The UsersClient is a client for the Axiom Users service."""

    def __init__(self, session: Session):
        self.session = session

    def current(self) -> User:
        """
        Get the current authenticated user.

        See https://axiom.co/docs/restapi/endpoints/getCurrentUser
        """
        res = self.session.get("/v2/user")
        user = from_dict(User, res.json())
        return user
