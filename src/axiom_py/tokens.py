import ujson
from dataclasses import dataclass, field, asdict
from requests import Session
from typing import Literal, Optional, List, Dict
from datetime import datetime
from .util import from_dict, handle_json_serialization

Action = Literal["create", "read", "update", "delete"]


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
    ingest: Optional[List[Action]] = field(default=None)
    # Ability to query data. Optional.
    query: Optional[List[Action]] = field(default=None)
    # Ability to use starred queries. Optional.
    starredQueries: Optional[List[Action]] = field(default=None)
    # Ability to use virtual fields. Optional.
    virtualFields: Optional[List[Action]] = field(default=None)
    # Trim capability. Optional
    trim: Optional[List[Action]] = field(default=None)
    # Vacuum capability. Optional
    vacuum: Optional[List[Action]] = field(default=None)
    # Data management capability. Optional.
    data: Optional[List[Action]] = field(default=None)
    # Share capability. Optional.
    share: Optional[List[Action]] = field(default=None)


@dataclass
class TokenOrganizationCapabilities:
    # pylint: disable=unsubscriptable-object
    """
    TokenOrganizationCapabilities describes the org-level permissions
    which a token can be assigned.
    """

    # Ability to use annotations. Optional.
    annotations: Optional[List[Action]] = field(default=None)
    # Ability to use api tokens. Optional.
    apiTokens: Optional[List[Action]] = field(default=None)
    # Audit log capability. Optional.
    auditLog: Optional[List[Action]] = field(default=None)
    # Ability to access billing. Optional.
    billing: Optional[List[Action]] = field(default=None)
    # Ability to use dashboards. Optional.
    dashboards: Optional[List[Action]] = field(default=None)
    # Ability to use datasets. Optional.
    datasets: Optional[List[Action]] = field(default=None)
    # Ability to use endpoints. Optional.
    endpoints: Optional[List[Action]] = field(default=None)
    # Ability to use flows. Optional.
    flows: Optional[List[Action]] = field(default=None)
    # Ability to use integrations. Optional.
    integrations: Optional[List[Action]] = field(default=None)
    # Ability to use monitors. Optional.
    monitors: Optional[List[Action]] = field(default=None)
    # Ability to use notifiers. Optional.
    notifiers: Optional[List[Action]] = field(default=None)
    # Ability to use role-based access controls. Optional.
    rbac: Optional[List[Action]] = field(default=None)
    # Ability to use shared access keys. Optional.
    sharedAccessKeys: Optional[List[Action]] = field(default=None)
    # Ability to use users. Optional.
    users: Optional[List[Action]] = field(default=None)
    # Ability to use views. Optional.
    views: Optional[List[Action]] = field(default=None)


@dataclass
class ApiToken:
    """
    Token contains the response from a call to POST /tokens.
    It includes the API token itself, and an ID which can be used to reference it later.
    """

    id: str
    name: str
    description: Optional[str]
    expiresAt: Optional[datetime]
    datasetCapabilities: Optional[Dict[str, TokenDatasetCapabilities]]
    orgCapabilities: Optional[TokenOrganizationCapabilities]
    samlAuthenticated: bool = field(default=False)


@dataclass
class CreateTokenRequest:
    # pylint: disable=unsubscriptable-object
    """
    CraeteTokenRequest describes the set of input parameters that the
    POST /tokens API accepts.
    """

    # Name for the token. Required.
    name: str
    # Description for the API token. Optional.
    description: Optional[str] = field(default=None)
    # Expiration date for the API token. Optional.
    expiresAt: Optional[str] = field(default=None)
    # The token's dataset-level capabilities. Keyed on dataset name. Optional.
    datasetCapabilities: Optional[Dict[str, TokenDatasetCapabilities]] = field(
        default=None
    )
    # The token's organization-level capabilities. Optional.
    orgCapabilities: Optional[TokenOrganizationCapabilities] = field(
        default=None
    )


@dataclass
class CreateTokenResponse(ApiToken):
    """
    CreateTokenResponse describes the set of output parameters that the
    POST /tokens API returns.
    """

    token: str = ""


@dataclass
class RegenerateTokenRequest:
    # pylint: disable=unsubscriptable-object
    """
    RegenerateTokenRequest describes the set of input parameters that the
    POST /tokens/{id}/regenerate API accepts.
    """

    existingTokenExpiresAt: datetime
    newTokenExpiresAt: datetime


class TokensClient:  # pylint: disable=R0903
    """TokensClient has methods to manipulate tokens."""

    session: Session

    def __init__(self, session: Session):
        self.session = session

    def list(self) -> List[ApiToken]:
        """List all API tokens."""
        res = self.session.get("/v2/tokens")
        tokens = []
        for record in res.json():
            ds = from_dict(ApiToken, record)
            tokens.append(ds)
        return tokens

    def create(self, req: CreateTokenRequest) -> CreateTokenResponse:
        """Creates a new API token with permissions specified in a TokenAttributes object."""
        res = self.session.post(
            "/v2/tokens",
            data=ujson.dumps(asdict(req), default=handle_json_serialization),
        )

        # Return the new token and ID.
        token = from_dict(CreateTokenResponse, res.json())
        return token

    def get(self, token_id: str) -> ApiToken:
        """Get an API token using its ID string."""
        res = self.session.get(f"/v2/tokens/{token_id}")
        token = from_dict(ApiToken, res.json())
        return token

    def regenerate(
        self, token_id: str, req: RegenerateTokenRequest
    ) -> ApiToken:
        """Regenerate an API token using its ID string."""
        res = self.session.post(
            f"/v2/tokens/{token_id}/regenerate",
            data=ujson.dumps(asdict(req), default=handle_json_serialization),
        )
        token = from_dict(ApiToken, res.json())
        return token

    def delete(self, token_id: str) -> None:
        """Delete an API token using its ID string."""
        self.session.delete(f"/v2/tokens/{token_id}")
