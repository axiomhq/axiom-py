from .util import from_dict
from dataclasses import dataclass
from requests import Session
from typing import Optional


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

    has_personal_token: bool

    def __init__(self, session: Session, has_personal_token: bool):
        self.session = session
        self.has_personal_token = has_personal_token

    def current(self) -> Optional[User]:
        """
        Get the current authenticated user.
        If your token is not a personal token, this will return None.

        See https://axiom.co/docs/restapi/endpoints/getCurrentUser
        """
        if not self.has_personal_token:
            return None

        res = self.session.get("/v2/user")
        user = from_dict(User, res.json())
        return user
