"""Internal error handling utilities shared between sync and async clients."""

from typing import Any, Dict
from .client import AxiomError
from .util import from_dict


def check_response_error(status_code: int, json_body: Dict[str, Any]) -> None:
    """
    Check response status code and raise AxiomError if needed.

    This function provides shared error checking logic for both sync and
    async clients.

    Args:
        status_code: HTTP status code from the response
        json_body: Parsed JSON response body

    Raises:
        AxiomError: If status code indicates an error (>= 400)
    """
    if status_code >= 400:
        try:
            error_res = from_dict(AxiomError.Response, json_body)
        except Exception:
            # Response is not in the Axiom JSON format, create generic error
            error_res = AxiomError.Response(
                message=f"HTTP {status_code} error", error=None
            )

        raise AxiomError(status_code, error_res)
