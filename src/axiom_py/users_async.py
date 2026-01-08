"""
Async version of user models and methods with AsyncUsersClient.
"""

import httpx
from typing import Optional

from .users import User
from .util import from_dict
from ._error_handling import check_response_error


class AsyncUsersClient:
    """AsyncUsersClient is an async client for the Axiom Users service."""

    client: httpx.AsyncClient
    has_personal_token: bool

    def __init__(self, client: httpx.AsyncClient, has_personal_token: bool):
        """
        Initialize the async users client.

        Args:
            client: httpx AsyncClient instance for making HTTP requests
            has_personal_token: Whether the token is a personal token
        """
        self.client = client
        self.has_personal_token = has_personal_token

    
    async def current(self) -> Optional[User]:
        """
        Asynchronously get the current authenticated user.
        If your token is not a personal token, this will return None.

        Returns:
            User object if personal token, None otherwise

        See https://axiom.co/docs/restapi/endpoints/getCurrentUser
        """
        if not self.has_personal_token:
            return None

        response = await self.client.get("/v2/user")
        check_response_error(response.status_code, response.json())

        user = from_dict(User, response.json())
        return user
