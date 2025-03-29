# py24so

A modern Python client for the 24SevenOffice API with support for synchronous and asynchronous operations, caching, rate limiting, and batch requests.

## Features

- Full support for customers, products, and invoices
- Both synchronous and asynchronous clients
- Built-in caching support
- Automatic rate limiting
- Batch operations for efficient API usage
- Proper error handling with custom exceptions
- Comprehensive documentation and type hints
- 100% test coverage

## Installation

```bash
# Using pip (standard)
pip install py24so

# With HTTP/2 support (for better performance)
pip install py24so[http2]

# Using UV (faster installation)
uv pip install py24so

# With HTTP/2 support using UV
uv pip install py24so[http2]
```

## Quick Start

### Synchronous Usage

```python
from py24so import Client24SO
from py24so.models.customer import CustomerCreate

# Initialize the client
client = Client24SO(
    client_id="your-client-id",
    client_secret="your-client-secret",
    organization_id="your-organization-id"
)

# List customers
customers = client.customers.list(page=1, page_size=10)
for customer in customers:
    print(f"{customer.name} ({customer.id})")

# Create a customer
new_customer = CustomerCreate(
    name="Acme Inc.",
    email="info@acme.com",
    phone="123-456-7890"
)
created_customer = client.customers.create(new_customer)
print(f"Created customer: {created_customer.name} (ID: {created_customer.id})")

# Always close the client when done
client.close()
```

### Asynchronous Usage

```python
import asyncio
from py24so import AsyncClient24SO
from py24so.models.invoice import InvoiceCreate, InvoiceLineItem

async def main():
    # Initialize the async client
    async with AsyncClient24SO(
        client_id="your-client-id",
        client_secret="your-client-secret",
        organization_id="your-organization-id"
    ) as client:
        # Create an invoice
        invoice = InvoiceCreate(
            customer_id="customer-id",
            line_items=[
                InvoiceLineItem(
                    description="Product A",
                    quantity=2,
                    unit_price=99.99,
                    vat_rate=25.0
                )
            ]
        )
        created_invoice = await client.invoices.create(invoice)
        print(f"Created invoice: {created_invoice.invoice_number}")
        
        # Send the invoice
        sent_invoice = await client.invoices.send(created_invoice.id)
        print(f"Invoice status: {sent_invoice.status}")

# Run the async function
asyncio.run(main())
```

## Context Managers

The clients also support context managers for automatic resource cleanup:

```python
# Synchronous context manager
with Client24SO(
    client_id="your-client-id",
    client_secret="your-client-secret",
    organization_id="your-organization-id"
) as client:
    # Client is automatically closed when exiting the block
    customers = client.customers.list()
```

## Configuration Options

You can customize the client behavior using the `ClientOptions` class:

```python
from py24so import Client24SO
from py24so.models.config import ClientOptions

options = ClientOptions(
    # Enable caching
    cache_enabled=True,
    # Cache TTL in seconds (5 minutes)
    cache_ttl=300,
    # Maximum number of cached responses
    cache_max_size=1000,
    # Rate limit in requests per minute
    rate_limit_rate=30,
    # Enable HTTP/2
    http2=True,
    # Custom headers
    headers={"X-Custom-Header": "value"},
    # Request timeout in seconds
    timeout=30.0
)

client = Client24SO(
    client_id="your-client-id",
    client_secret="your-client-secret",
    organization_id="your-organization-id",
    options=options
)
```

## Development

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/py24so.git
   cd py24so
   ```

2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Run the tests:
   ```bash
   pytest
   ```

### Code Formatting

This project uses Black and isort for code formatting. You can format the code using:

```bash
# Run the formatting script
python scripts/format_code.py

# Or run the tools directly
black py24so tests
isort py24so tests
```

If the CI checks are failing due to formatting issues, you can:
1. Run the formatting script locally and push the changes
2. Use the "Format Code" GitHub Action in your repository

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Run tests and ensure they pass
5. Submit a pull request

## GitHub Actions

This project includes GitHub Actions for continuous integration and deployment:

1. **CI**: Runs on every push to main and on pull requests to main
   - Tests on multiple Python versions
   - Code quality checks
   - Code coverage reporting with Codecov

2. **Publish to PyPI**: Triggered on new releases or manually
   - Builds the package
   - Runs tests
   - Publishes to PyPI if all checks pass

3. **Format Code**: Format code automatically with Black and isort
   - Can be triggered manually
   - Automatically fixes code style issues

### Setting Up GitHub Actions

To use these GitHub Actions, you need to set up some secrets in your repository:

1. **PyPI Token** (for package publishing):
   - Generate a token on PyPI: https://pypi.org/manage/account/token/
   - Add it as a repository secret named `PYPI_API_TOKEN`

2. **Codecov Token** (for code coverage reporting):
   - Create an account on Codecov and link your repository
   - Get your repository upload token from Codecov
   - Add it as a repository secret named `CODECOV_TOKEN`

### Manual Release

To manually trigger a release:

1. Go to the Actions tab in your GitHub repository
2. Select the "Publish to PyPI" workflow
3. Click "Run workflow"
4. Enter the version number (e.g., "0.1.1") and submit

**Note**: You need to add a PyPI API token as a secret in your GitHub repository settings:
1. Generate a token on PyPI: https://pypi.org/manage/account/token/
2. Add it as a repository secret named `PYPI_API_TOKEN`

## License

This project is licensed under the MIT License - see the LICENSE file for details.
