"""
Axiom Python Client
"""

# Sync API
from .client import (
    AxiomError,
    IngestFailure,
    IngestStatus,
    IngestOptions,
    AplResultFormat,
    ContentType,
    ContentEncoding,
    WrongQueryKindException,
    AplOptions,
    Client,
)
from .datasets import (
    Dataset,
    TrimRequest,
    DatasetsClient,
)
from .annotations import (
    Annotation,
    AnnotationCreateRequest,
    AnnotationUpdateRequest,
    AnnotationsClient,
)
from .logging import AxiomHandler
from .structlog import AxiomProcessor

# Async API
from .client_async import AsyncClient
from .datasets_async import AsyncDatasetsClient
from .annotations_async import AsyncAnnotationsClient
from .tokens_async import AsyncTokensClient
from .users_async import AsyncUsersClient
from .logging_async import AsyncAxiomHandler
from .structlog_async import AsyncAxiomProcessor

__all__ = [
    # Exceptions & Models (shared between sync and async)
    "AxiomError",
    "IngestFailure",
    "IngestStatus",
    "IngestOptions",
    "AplResultFormat",
    "ContentType",
    "ContentEncoding",
    "WrongQueryKindException",
    "AplOptions",
    "Dataset",
    "TrimRequest",
    "Annotation",
    "AnnotationCreateRequest",
    "AnnotationUpdateRequest",
    # Sync API
    "Client",
    "DatasetsClient",
    "AnnotationsClient",
    "AxiomHandler",
    "AxiomProcessor",
    # Async API
    "AsyncClient",
    "AsyncDatasetsClient",
    "AsyncAnnotationsClient",
    "AsyncTokensClient",
    "AsyncUsersClient",
    "AsyncAxiomHandler",
    "AsyncAxiomProcessor",
]
