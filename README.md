# py24so - Python Wrapper for 24SevenOffice API

A modern, feature-rich Python client for the 24SevenOffice API with support for caching, rate limiting, and request batching.

## Features

- 🚀 **Modern API**: Clean, type-annotated interface using Pydantic models
- 🔄 **Automatic Caching**: HTTP caching with [Hishel](https://github.com/karpetrosyan/hishel)
- 🛑 **Rate Limiting**: Built-in rate limiting to prevent API throttling
- 📦 **Request Batching**: Combine multiple API calls into a single request when possible
- 🧩 **Comprehensive Coverage**: Support for all public 24SevenOffice API endpoints
- ⚡ **High Performance**: Async support with HTTPX
- 🔒 **OAuth2 Authentication**: Simple authentication flow

## Installation

### Using pip

```bash
pip install py24so
```

With HTTP/2 support:

```bash
pip install py24so[http2]
```

### Using UV (faster installation)

```bash
uv pip install py24so
```

With HTTP/2 support:

```bash
uv pip install py24so[http2]
```

## Quick Start

```python
from py24so import Client24SO

# Initialize client
client = Client24SO(
    client_id="your_client_id",
    client_secret="your_client_secret",
    organization_id="your_organization_id"
)

# Get data from the API
customers = client.customers.list()
print(customers)

# Create a new customer
new_customer = client.customers.create({
    "name": "ACME Inc.",
    "email": "info@acme.com"
})
```

## Async Support

```python
import asyncio
from py24so import AsyncClient24SO

async def main():
    client = AsyncClient24SO(
        client_id="your_client_id",
        client_secret="your_client_secret",
        organization_id="your_organization_id"
    )
    
    # Get data from the API
    customers = await client.customers.list()
    print(customers)

asyncio.run(main())
```

## Configuration Options

```python
from py24so import Client24SO, ClientOptions

client = Client24SO(
    client_id="your_client_id",
    client_secret="your_client_secret",
    organization_id="your_organization_id",
    options=ClientOptions(
        base_url="https://rest.api.24sevenoffice.com/v1",
        cache_enabled=True,
        cache_max_size=100,  # Cache up to 100 responses
        cache_ttl=300,  # Cache TTL in seconds
        rate_limit_rate=100,  # Requests per minute
        timeout=30.0,  # Request timeout in seconds
        http2=False,  # Use HTTP/2
    )
)
```

## Development

### Setting up the development environment

With pip:
```bash
# Create virtual environment
python -m venv .venv
# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
# Install development dependencies
pip install -e ".[dev,docs]"
```

With UV (faster):
```bash
# Create virtual environment
uv venv
# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
# Install development dependencies
uv pip install -e ".[dev,docs]"
```

### Running tests
```bash
pytest
# With coverage
pytest --cov=py24so
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
