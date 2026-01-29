# Async Implementation for axiom-py

This document summarizes the async implementation added to the axiom-py SDK.

## Overview

An async version of the Axiom Python SDK has been implemented using httpx, providing full async/await support for all client operations while maintaining complete backward compatibility with the existing synchronous API.

## Architecture

### HTTP Library
- **Sync API**: Uses `requests` library (unchanged)
- **Async API**: Uses `httpx` library for async HTTP operations

### File Organization
- **Separate Files**: Each async client is in a separate `*_async.py` file
- **Shared Utilities**: Common code shared via internal modules:
  - `_http_client.py`: HTTP configuration and retry logic
  - `_error_handling.py`: Shared error handling

### Naming Convention
- Async classes prefixed with `Async`: `AsyncClient`, `AsyncDatasetsClient`, etc.
- All methods use `async def` with `await` for HTTP calls

## Implementation Summary

### Core Async Clients

1. **AsyncClient** (`src/axiom_py/client_async.py`)
   - Main async client with context manager support
   - Methods: `ingest()`, `ingest_events()`, `query()`, `apl_query()`, `query_legacy()`
   - Automatic cleanup via `__aenter__` and `__aexit__`

2. **AsyncDatasetsClient** (`src/axiom_py/datasets_async.py`)
   - 6 async methods: `get()`, `create()`, `get_list()`, `update()`, `delete()`, `trim()`

3. **AsyncAnnotationsClient** (`src/axiom_py/annotations_async.py`)
   - 5 async methods: `get()`, `create()`, `list()`, `update()`, `delete()`

4. **AsyncTokensClient** (`src/axiom_py/tokens_async.py`)
   - 5 async methods: `list()`, `create()`, `get()`, `regenerate()`, `delete()`

5. **AsyncUsersClient** (`src/axiom_py/users_async.py`)
   - 1 async method: `current()`

### Async Logging Handlers

6. **AsyncAxiomHandler** (`src/axiom_py/logging_async.py`)
   - Async logging handler for Python's logging module
   - Uses `asyncio.Task` for periodic flushing instead of `threading.Timer`
   - Hybrid approach: `emit()` is sync, but schedules async flush operations

7. **AsyncAxiomProcessor** (`src/axiom_py/structlog_async.py`)
   - Async processor for structlog
   - Fully async `__call__()` method

### Supporting Files

8. **_http_client.py** (`src/axiom_py/_http_client.py`)
   - Shared HTTP utilities
   - `get_common_headers()`: Returns common headers for both sync and async
   - `async_retry()`: Decorator for exponential backoff retry logic

9. **_error_handling.py** (`src/axiom_py/_error_handling.py`)
   - Shared error checking
   - `check_response_error()`: Validates response and raises AxiomError if needed

## Dependencies Added

### Runtime Dependencies
- `httpx>=0.27.0` - Async HTTP client

### Development Dependencies
- `pytest-asyncio>=0.23.0` - Async test support
- `respx>=0.21.0` - HTTP mocking for httpx tests

## Usage Examples

### Basic Usage
```python
import asyncio
from axiom_py import AsyncClient

async def main():
    async with AsyncClient() as client:
        # Ingest events
        await client.ingest_events(
            "dataset",
            [{"field": "value"}]
        )

        # Query data
        result = await client.query("['dataset'] | limit 100")
        print(f"Found {len(result.matches)} matches")

asyncio.run(main())
```

### Concurrent Operations
```python
import asyncio
from axiom_py import AsyncClient

async def main():
    async with AsyncClient() as client:
        # Run multiple operations concurrently
        results = await asyncio.gather(
            client.ingest_events("dataset1", events1),
            client.ingest_events("dataset2", events2),
            client.query("['dataset1']"),
        )

asyncio.run(main())
```

### Async Logging
```python
import asyncio
import logging
from axiom_py import AsyncClient, AsyncAxiomHandler

async def main():
    async with AsyncClient() as client:
        handler = AsyncAxiomHandler(client, "logs")
        logger = logging.getLogger()
        logger.addHandler(handler)

        logger.info("This log will be sent to Axiom")

        # Important: flush before exit
        await handler.close()

asyncio.run(main())
```

## Testing

### Test Infrastructure
- `pytest.ini` configured with `asyncio_mode = auto`
- Test files: `tests/test_client_async.py`, `tests/test_datasets_async.py`
- Uses `respx` for mocking httpx requests

### Running Tests
```bash
pytest tests/test_client_async.py -v
pytest tests/test_datasets_async.py -v
```

## Examples

Example scripts are provided in the `examples/` directory:
- `async_basic.py` - Basic async client usage
- `async_concurrent.py` - Concurrent operations
- `async_datasets.py` - Dataset management
- `async_logging.py` - Async logging handler

## Key Design Decisions

1. **Separate Files**: Each async client is in its own file to keep code clean and maintainable
2. **Context Manager**: AsyncClient uses `async with` for automatic resource cleanup
3. **Retry Logic**: HTTP calls include exponential backoff retry for 5xx errors
4. **No Breaking Changes**: Existing sync API remains unchanged
5. **Shared Models**: Data models (Dataset, Annotation, etc.) are shared between sync and async

## Success Criteria

✅ All 19 public methods have async equivalents
✅ Both sync and async APIs work side-by-side
✅ Context manager properly manages httpx client lifecycle
✅ Error handling matches sync client behavior
✅ Async logging handlers properly flush on close
✅ Documentation includes async examples
✅ No breaking changes to existing sync API

## Future Improvements

Potential enhancements for future releases:
1. Add integration tests against real Axiom API
2. Implement connection pooling optimization
3. Add support for streaming large result sets
4. Benchmark async vs sync performance
5. Add more comprehensive async logging examples

## Version

This async implementation will be released as version 0.10.0 (minor version bump for new features).
