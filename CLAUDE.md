# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

axiom-py is the official Python client library for Axiom, a serverless log management and analytics platform. The library provides bindings for ingesting events, querying data, and managing datasets via the Axiom REST API.

## Development Commands

### Running Tests
```bash
# Run all tests (requires AXIOM_TOKEN, AXIOM_ORG_ID, and optionally AXIOM_URL env vars)
uv run pytest

# Run a specific test file
uv run pytest tests/test_client.py

# Run a specific test
uv run pytest tests/test_client.py::TestClient::test_step001_ingest
```

### Linting and Formatting
```bash
# Check code with ruff
uv run ruff check

# Auto-fix issues
uv run ruff check --fix

# Check formatting
uv run ruff format --check

# Format code
uv run ruff format
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks
uv run pre-commit install

# Run hooks manually
uv run pre-commit run --all-files
```

### Building
```bash
# Build the package for distribution
uv build
```

## Architecture

### Core Components

**Client (`src/axiom_py/client.py`)**: The main `Client` class is the entry point for all Axiom operations. It manages:
- HTTP session with automatic retries (3 retries with exponential backoff for 5xx errors)
- Authentication via Bearer token (from constructor or `AXIOM_TOKEN` env var)
- Organization ID handling (from constructor or `AXIOM_ORG_ID` env var)
- Shutdown hooks registered with `atexit` to flush buffered logs

The Client exposes specialized sub-clients as properties:
- `client.datasets` - Dataset CRUD operations
- `client.annotations` - Annotation management
- `client.users` - User information
- `client.tokens` - API token management

**DatasetsClient (`src/axiom_py/datasets.py`)**: Handles dataset operations (create, get, list, update, delete, trim). Takes a requests.Session object and makes API calls to `/v1/datasets` endpoints.

**Query System (`src/axiom_py/query/`)**: Supports two query types:
- **APL queries** (recommended): Uses Axiom Processing Language via `client.query()` or `client.apl_query()`. Supports both "legacy" and "tabular" result formats.
- **Legacy structured queries**: Uses `QueryLegacy` dataclass with filters, aggregations, groupBy, etc. via `client.query_legacy()`.

**Logging Integration (`src/axiom_py/logging.py`, `src/axiom_py/structlog.py`)**:
- `AxiomHandler`: Standard Python logging handler that buffers log records and flushes to Axiom every 1 second or when buffer reaches 1000 events.
- `AxiomProcessor`: Structlog processor with similar buffering behavior.
- Both use threading.Timer (AxiomHandler) or time checks to periodically flush.

### Key Design Patterns

**Ingestion**: Events are encoded as NDJSON and gzip-compressed before sending. The `ingest_events()` method is a convenience wrapper around the lower-level `ingest()` method that handles this automatically.

**Error Handling**: All HTTP responses are checked via a response hook that raises `AxiomError` for status codes >= 400. This exception includes the status code and error message from the API.

**Serialization**: Uses `dacite` for deserializing API responses to dataclasses, and custom JSON handling (`handle_json_serialization` in `util.py`) for datetime objects during serialization.

**Type Safety**: The codebase heavily uses dataclasses and type hints (Python 3.8+). Field names use snake_case in Python but are automatically converted to/from camelCase for API communication using the `pyhumps` library.

## Testing Guidelines

- Tests are integration tests that run against live Axiom environments (dev and staging)
- Test methods should be prefixed with `test_step` and numbered (e.g., `test_step001_ingest`) to control execution order when needed
- Use `get_random_name()` helper from `tests/helpers.py` to generate unique dataset names
- Clean up resources in `tearDownClass` even on test failures to avoid zombie datasets
- Tests use the `responses` library for mocking HTTP requests when testing client behavior (retries, error handling)

## Code Style

- Line length: 79 characters (PEP 8)
- Uses Ruff for both linting and formatting
- Python 3.8+ compatible (check `classifiers` in pyproject.toml before using newer syntax)

## Important Notes

- Version 0.9.0 removed the aggregation operation enum (see #158). Use string literals instead.
- When using APL queries with `limit`, pass it via `AplOptions.limit` parameter (not in the APL query string).
- Personal tokens don't require an org_id, but organization tokens do. The `is_personal_token()` utility in `tokens.py` detects token type.