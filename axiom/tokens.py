from dataclasses import dataclass
from typing import Literal


@dataclass
class TokenDatasetCapabilities:
    """
    TokenDatasetCapabilities describes the dataset-level permissions
    which a token can be assigned.
    Each token can have multiple dataset-level capability objects;
    one per dataset.
    """

    # Ability to ingest data. Optional.
    ingest: list[Literal["create"]] | None = None
    # Ability to query data. Optional.
    query: list[Literal["read"]] | None = None
    # Ability to use starred queries. Optional.
    starredQueries: list[Literal["create", "read", "update", "delete"]] | None = None
    # Ability to use virtual fields. Optional.
    virtualFields: list[Literal["create", "read", "update", "delete"]] | None = None


@dataclass
class TokenOrganizationCapabilities:
    """
    TokenOrganizationCapabilities describes the org-level permissions
    which a token can be assigned.
    """

    # Ability to use annotations. Optional.
    annotations: list[Literal["create", "read", "update", "delete"]] | None = None
    # Ability to use api tokens. Optional.
    apiTokens: list[Literal["create", "read", "update", "delete"]] | None = None
    # Ability to access billing. Optional.
    billing: list[Literal["read", "update"]] | None = None
    # Ability to use dashboards. Optional.
    dashboards: list[Literal["create", "read", "update", "delete"]] | None = None
    # Ability to use datasets. Optional.
    datasets: list[Literal["create", "read", "update", "delete"]] | None = None
    # Ability to use endpoints. Optional.
    endpoints: list[Literal["create", "read", "update", "delete"]] | None = None
    # Ability to use flows. Optional.
    flows: list[Literal["create", "read", "update", "delete"]] | None = None
    # Ability to use integrations. Optional.
    integrations: list[Literal["create", "read", "update", "delete"]] | None = None
    # Ability to use monitors. Optional.
    monitors: list[Literal["create", "read", "update", "delete"]] | None = None
    # Ability to use notifiers. Optional.
    notifiers: list[Literal["create", "read", "update", "delete"]] | None = None
    # Ability to use role-based access controls. Optional.
    rbac: list[Literal["create", "read", "update", "delete"]] | None = None
    # Ability to use shared access keys. Optional.
    sharedAccessKeys: list[Literal["read", "update"]] | None = None
    # Ability to use users. Optional.
    users: list[Literal["create", "read", "update", "delete"]] | None = None


@dataclass
class TokenAttributes:
    """
    TokenAttributes describes the set of input parameters that the
    POST /tokens API accepts.
    """

    # Name for the token. Required.
    name: str
    # The token's dataset-level capabilities. Keyed on dataset name. Optional.
    datasetCapabilities: dict[str, TokenDatasetCapabilities] | None = None
    # Description for the API token. Optional.
    description: str | None = None
    # Expiration date for the API token. Optional.
    expiresAt: str | None = None
    # The token's organization-level capabilities. Optional.
    orgCapabilities: TokenOrganizationCapabilities | None = None


@dataclass
class Token:
    """
    Token contains the response from a call to POST /tokens.
    It includes the API token itself, and an ID which can be used to reference it later.
    """

    id: str
    token: str
