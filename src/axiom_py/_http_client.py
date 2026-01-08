"""Internal HTTP client utilities shared between sync and async clients."""

import asyncio
from functools import wraps
from typing import Optional
import httpx

from .version import __version__


# Retry configuration constants
RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_FACTOR = 2
RETRY_STATUS_CODES = [500, 502, 503, 504]
DEFAULT_TIMEOUT = 30.0


def get_common_headers(token: str, org_id: Optional[str] = None) -> dict:
    """
    Get common headers for both sync and async clients.

    Args:
        token: API token for authentication
        org_id: Optional organization ID

    Returns:
        Dictionary of common HTTP headers
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": f"axiom-py/{__version__}",
    }
    if org_id:
        headers["X-Axiom-Org-Id"] = org_id
    return headers


def async_retry(
    max_attempts: int = RETRY_MAX_ATTEMPTS,
    backoff_factor: float = RETRY_BACKOFF_FACTOR,
    status_codes: list = None,
):
    """
    Decorator for async functions that implements exponential backoff retry
    logic for HTTP requests.

    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Exponential backoff factor (delay = backoff_factor ** attempt)
        status_codes: List of status codes to retry on

    Returns:
        Decorated async function with retry logic
    """
    if status_codes is None:
        status_codes = RETRY_STATUS_CODES

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            response = None

            for attempt in range(max_attempts):
                try:
                    response = await func(*args, **kwargs)

                    # If status code is not in retry list, return immediately
                    if response.status_code not in status_codes:
                        return response

                    # If this is the last attempt, return the response
                    if attempt == max_attempts - 1:
                        return response

                    # Wait before retrying
                    delay = backoff_factor**attempt
                    await asyncio.sleep(delay)

                except httpx.RequestError as e:
                    last_exception = e
                    # If this is the last attempt, raise the exception
                    if attempt == max_attempts - 1:
                        raise

                    # Wait before retrying
                    delay = backoff_factor**attempt
                    await asyncio.sleep(delay)

            # If we exhausted all retries and have a response, return it
            if response is not None:
                return response

            # If we have an exception, raise it
            if last_exception is not None:
                raise last_exception

            # This should never happen, but just in case
            raise RuntimeError("Retry logic failed unexpectedly")

        return wrapper

    return decorator
