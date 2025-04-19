import ujson
from dataclasses import dataclass, field, asdict
from requests import Session
from typing import Literal, Optional

@dataclass
class TokenDatasetCapabilities:
    # pylint: disable=unsubscriptable-object
    """
    TokenDatasetCapabilities describes the dataset-level permissions
    which a token can be assigned.
    Each token can have multiple dataset-level capability objects;
    one per dataset.
    """

    # Ability to ingest data. Optional.
    ingest: Optional[list[Literal["create"]]] = field(default=None)
    # Ability to query data. Optional.
    query: Optional[list[Literal["read"]]] = field(default=None)
    # Ability to use starred queries. Optional.
    starredQueries: Optional[
        list[Literal["create", "read", "update", "delete"]]
    ] = field(default=None)
    # Ability to use virtual fields. Optional.
    virtualFields: Optional[
        list[Literal["create", "read", "update", "delete"]]
    ] = field(default=None)


@dataclass
class TokenOrganizationCapabilities:
    # pylint: disable=unsubscriptable-object
    """
    TokenOrganizationCapabilities describes the org-level permissions
    which a token can be assigned.
    """

    # Ability to use annotations. Optional.
    annotations: Optional[
        list[Literal["create", "read", "update", "delete"]]
    ] = field(default=None)
    # Ability to use api tokens. Optional.
    apiTokens: Optional[
        list[Literal["create", "read", "update", "delete"]]
    ] = field(default=None)
    # Ability to access billing. Optional.
    billing: Optional[list[Literal["read", "update"]]] = field(default=None)
    # Ability to use dashboards. Optional.
    dashboards: Optional[
        list[Literal["create", "read", "update", "delete"]]
    ] = field(default=None)
    # Ability to use datasets. Optional.
    datasets: Optional[list[Literal["create", "read", "update", "delete"]]] = (
        field(default=None)
    )
    # Ability to use endpoints. Optional.
    endpoints: Optional[
        list[Literal["create", "read", "update", "delete"]]
    ] = field(default=None)
    # Ability to use flows. Optional.
    flows: Optional[list[Literal["create", "read", "update", "delete"]]] = (
        field(default=None)
    )
    # Ability to use integrations. Optional.
    integrations: Optional[
        list[Literal["create", "read", "update", "delete"]]
    ] = field(default=None)
    # Ability to use monitors. Optional.
    monitors: Optional[list[Literal["create", "read", "update", "delete"]]] = (
        field(default=None)
    )
    # Ability to use notifiers. Optional.
    notifiers: Optional[
        list[Literal["create", "read", "update", "delete"]]
    ] = field(default=None)
    # Ability to use role-based access controls. Optional.
    rbac: Optional[list[Literal["create", "read", "update", "delete"]]] = (
        field(default=None)
    )
    # Ability to use shared access keys. Optional.
    sharedAccessKeys: Optional[list[Literal["read", "update"]]] = field(
        default=None
    )
    # Ability to use users. Optional.
    users: Optional[list[Literal["create", "read", "update", "delete"]]] = (
        field(default=None)
    )


@dataclass
class TokenAttributes:
    # pylint: disable=unsubscriptable-object
    """
    TokenAttributes describes the set of input parameters that the
    POST /tokens API accepts.
    """

    # Name for the token. Required.
    name: str
    # The token's dataset-level capabilities. Keyed on dataset name. Optional.
    datasetCapabilities: Optional[dict[str, TokenDatasetCapabilities]] = field(
        default=None
    )
    # Description for the API token. Optional.
    description: Optional[str] = field(default=None)
    # Expiration date for the API token. Optional.
    expiresAt: Optional[str] = field(default=None)
    # The token's organization-level capabilities. Optional.
    orgCapabilities: Optional[TokenOrganizationCapabilities] = field(
        default=None
    )


@dataclass
class Token:
    """
    Token contains the response from a call to POST /tokens.
    It includes the API token itself, and an ID which can be used to reference it later.
    """

    id: str
    token: str


class TokensClient:  # pylint: disable=R0903
    """TokensClient has methods to manipulate tokens."""

    session: Session

    def __init__(self, session: Session):
        self.session = session

    def create_api_token(self, opts: TokenAttributes) -> Token:
        """Creates a new API token with permissions specified in a TokenAttributes object."""
        res = self.session.post(
            "/v2/tokens",
            data=ujson.dumps(asdict(opts)),
        )

        # Return the new token and ID.
        response = res.json()
        return Token(id=response["id"], token=response["token"])

    def delete_api_token(self, token_id: str) -> None:
        """Delete an API token using its ID string."""
        self.session.delete(f"/v2/tokens/{token_id}")
