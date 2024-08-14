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
    ingest: Literal["create"]
    # Ability to query data. Optional.
    query: Literal["read"]
    # Ability to use starred queries. Optional.
    starredQueries: Literal["create", "read", "update", "delete"]
    # Ability to use virtual fields. Optional.
    virtualFields: Literal["create", "read", "update", "delete"]


@dataclass
class TokenOrganizationCapabilities:
    """
    TokenOrganizationCapabilities describes the org-level permissions
    which a token can be assigned.
    """

    # Ability to use annotations. Optional.
    annotations: Literal["create", "read", "update", "delete"]
    # Ability to use api tokens. Optional.
    apiTokens: Literal["create", "read", "update", "delete"]
    # Ability to access billing. Optional.
    billing: Literal["read", "update"]
    # Ability to use dashboards. Optional.
    dashboards: Literal["create", "read", "update", "delete"]
    # Ability to use datasets. Optional.
    datasets: Literal["create", "read", "update", "delete"]
    # Ability to use endpoints. Optional.
    endpoints: Literal["create", "read", "update", "delete"]
    # Ability to use flows. Optional.
    flows: Literal["create", "read", "update", "delete"]
    # Ability to use integrations. Optional.
    integrations: Literal["create", "read", "update", "delete"]
    # Ability to use monitors. Optional.
    monitors: Literal["create", "read", "update", "delete"]
    # Ability to use notifiers. Optional.
    notifiers: Literal["create", "read", "update", "delete"]
    # Ability to use role-based access controls. Optional.
    rbac: Literal["create", "read", "update", "delete"]
    # Ability to use shared access keys. Optional.
    sharedAccessKeys: Literal["read", "update"]
    # Ability to use users. Optional.
    users: Literal["create", "read", "update", "delete"]


@dataclass
class TokenAttributes:
    """
    TokenAttributes describes the set of input parameters that the
    POST /tokens API accepts.
    """

    # The token's dataset-level capabilities. Keyed on dataset name. Optional.
    datasetCapabilities: dict[str, TokenDatasetCapabilities]
    # Description for the API token. Optional.
    description: str
    # Expiration date for the API token. Optional.
    expiresAt: str | None
    # Name for the token. Required.
    name: str
    # The token's organization-level capabilities. Optional.
    orgCapabilities: TokenOrganizationCapabilities