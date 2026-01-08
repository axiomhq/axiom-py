"""
Async version of token models and methods with AsyncTokensClient.
"""

import ujson
import httpx
from typing import List
from dataclasses import asdict

from .tokens import (
    ApiToken,
    CreateTokenRequest,
    CreateTokenResponse,
    RegenerateTokenRequest,
)
from .util import from_dict, handle_json_serialization
from ._error_handling import check_response_error


class AsyncTokensClient:
    """AsyncTokensClient has async methods to manipulate tokens."""

    client: httpx.AsyncClient

    def __init__(self, client: httpx.AsyncClient):
        """
        Initialize the async tokens client.

        Args:
            client: httpx AsyncClient instance for making HTTP requests
        """
        self.client = client

    
    async def list(self) -> List[ApiToken]:
        """
        Asynchronously list all API tokens.

        Returns:
            List of ApiToken objects
        """
        response = await self.client.get("/v2/tokens")
        check_response_error(response.status_code, response.json())

        tokens = []
        for record in response.json():
            token = from_dict(ApiToken, record)
            tokens.append(token)
        return tokens

    
    async def create(self, req: CreateTokenRequest) -> CreateTokenResponse:
        """
        Asynchronously create a new API token with permissions specified
        in a CreateTokenRequest object.

        Args:
            req: Token creation request

        Returns:
            CreateTokenResponse with the new token and ID
        """
        payload = ujson.dumps(asdict(req), default=handle_json_serialization)
        response = await self.client.post("/v2/tokens", content=payload)
        check_response_error(response.status_code, response.json())

        token = from_dict(CreateTokenResponse, response.json())
        return token

    
    async def get(self, token_id: str) -> ApiToken:
        """
        Asynchronously get an API token using its ID string.

        Args:
            token_id: Token identifier

        Returns:
            ApiToken object
        """
        response = await self.client.get(f"/v2/tokens/{token_id}")
        check_response_error(response.status_code, response.json())

        token = from_dict(ApiToken, response.json())
        return token

    
    async def regenerate(
        self, token_id: str, req: RegenerateTokenRequest
    ) -> ApiToken:
        """
        Asynchronously regenerate an API token using its ID string.

        Args:
            token_id: Token identifier
            req: Regenerate token request with expiration dates

        Returns:
            ApiToken object with updated information
        """
        payload = ujson.dumps(asdict(req), default=handle_json_serialization)
        response = await self.client.post(
            f"/v2/tokens/{token_id}/regenerate", content=payload
        )
        check_response_error(response.status_code, response.json())

        token = from_dict(ApiToken, response.json())
        return token

    
    async def delete(self, token_id: str) -> None:
        """
        Asynchronously delete an API token using its ID string.

        Args:
            token_id: Token identifier
        """
        response = await self.client.delete(f"/v2/tokens/{token_id}")
        check_response_error(response.status_code, response.json())
