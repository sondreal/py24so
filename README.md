# py24so

A typed, sync + async Python client for the [24SevenOffice](https://developer.24sevenoffice.com/) (Finago Office) REST API.

- **Complete**: every operation in the [official OpenAPI spec](https://rest.api.24sevenoffice.com/v1/openapi.json) (v0.60.1). A test fails if the spec has an operation without a wrapper.
- **Typed**: Pydantic v2 models for every request and response, a `py.typed` marker, and `mypy --strict` clean. Attributes are `snake_case`; the wire format is the API's `camelCase`.
- **Sync and async**: `Client24SO` and `AsyncClient24SO` have identical APIs.
- **Robust**:
  - Tokens refresh automatically before expiry and after a 401, safely across threads and tasks.
  - Retries honour `Retry-After` and never re-send a write that may already have been processed.
  - Errors are typed and carry the API's `trackingId`.
  - Responses tolerate new fields and malformed dates, so an API change never breaks parsing.
- **Pagination**: list endpoints return lazy iterators that follow the API's `Link` headers.

## Installation

```bash
pip install py24so
pip install "py24so[http2]"   # optional HTTP/2 support
```

Requires Python 3.9+.

## Credentials

You need an application in the 24SevenOffice [Developer admin panel](https://finago.no/developer/rest-api-get-started) with the scopes your integration uses. Authentication uses the OAuth2 client credentials flow. Pass the credentials explicitly or set these environment variables:

```bash
export PY24SO_CLIENT_ID=...          # your application's client id
export PY24SO_CLIENT_SECRET=...      # your application's client secret
export PY24SO_ORGANIZATION_ID=...    # the client organization to act on (login_organization)
```

## Quick start

```python
from py24so import Client24SO
from py24so import models as m

with Client24SO() as client:   # or Client24SO(client_id, client_secret, organization_id)
    # Iterate over *all* matching customers; pages are fetched lazily.
    for customer in client.customers.list(is_company=True, sort_by="name:asc"):
        print(customer.id, customer.name, customer.email.billing if customer.email else None)

    # Create a customer (a company needs a name; a person needs `person`).
    customer = client.customers.create(
        m.CustomerCreate(is_company=True, name="Acme AS", organization_number="999999999")
    )

    # Plain dicts work too, in snake_case or camelCase.
    client.customers.update(customer.id, {"mobile_phone": "+4799999999"})
```

### Async

```python
import asyncio
from py24so import AsyncClient24SO

async def main() -> None:
    async with AsyncClient24SO() as client:
        taxes, units = await asyncio.gather(client.taxes.list(), client.product_units.list())
        async for product in client.products.list(search="coffee"):
            print(product.name, product.sales_price)

asyncio.run(main())
```

## Invoicing

The API has no separate invoice endpoint. You invoice a **sales order** by adding lines and setting its status to `Invoice`. The order then goes to the invoice queue and is sent according to the organization's settings.

```python
order = client.sales_orders.create(
    m.SalesOrderCreate(
        customer=m.SalesOrderCustomer(id=customer.id, name=customer.name),
        invoice=m.SalesOrderInvoice(
            payment_terms=m.PaymentTerms(type=m.PaymentTermsType.NUMBER_OF_DAYS, value=14)
        ),
    )
)
client.sales_orders.lines.create(
    order.id,
    m.SalesOrderLineCreate(type="product", product=m.LineProduct(id=101), quantity=2, price=49.99),
)
client.sales_orders.attachments.upload(order.id, "terms.pdf")
client.sales_orders.invoice(order.id)   # PATCH status -> "Invoice"
```

## Available resources

| Attribute | Endpoints |
| --- | --- |
| `customers` (+ `.bank_accounts`) | `/customers`, `/customers/{id}/bankaccounts` |
| `sales_orders` (+ `.lines`, `.attachments`) | `/salesorders`, lines, attachments |
| `sales_types`, `payment_methods` | `/salestypes`, `/paymentmethods` |
| `products` (+ `.dimensions`, `.sales_type_overrides`) | `/products` and sub-resources |
| `product_categories`, `product_units`, `price_lists` | `/productcategories`, `/productunits`, `/pricelists` |
| `accounts`, `account_balances`, `taxes`, `currencies`, `fiscal_periods` | chart of accounts, balances, VAT codes, … |
| `transaction_lines`, `transactions`, `transaction_types` | general ledger read/write |
| `dimensions` (+ `.elements`) | departments, projects, custom dimensions |
| `bank_accounts`, `bank_transactions` | `/bankaccounts`, `/banktransactions` |
| `files`, `documents` | `/fileUpload` (upload receipts), `/documents` |
| `organization` (+ `.people`), `me` (+ `.identifiers`, `.licenses`) | `/organization/*`, `/me/*` |

For anything else, use the escape hatch. It has the same auth, retries and errors:

```python
data = client.request("GET", "/customers", params={"limit": 5})
```

## Pagination

`list()` on paginated endpoints (customers, products, product categories, sales orders, transaction lines, bank transactions and dimension elements) returns a `Paginator`:

```python
paginator = client.transaction_lines.list(date_from="2024-01-01", date_to="2024-12-31", page_size=100)

for line in paginator:                 # every item, across all pages
    ...
paginator.to_list(max_items=500)      # stop after 500 items
page = paginator.first_page()          # a single request: page.items, page.next_url
for page in paginator.pages():         # page by page
    ...
```

The async paginator supports `async for`, and `await paginator.to_list()`.

## Errors

```python
from py24so import APIStatusError, BadRequestError, NotFoundError, RateLimitError, ValidationError

try:
    client.sales_orders.invoice(order_id)
except ValidationError as err:          # 400 with error.name == "ValidationError"
    print(err.validation_errors)        # [{"path": "customer.name", "keyword": "required"}]
except BadRequestError as err:          # other 400s
    print(err.errors)                   # [{"type": "NoLines", "message": "No lines in the sales order"}]
except APIStatusError as err:           # any other 4xx/5xx
    print(err.status_code, err.message, err.tracking_id, err.trace_id)
```

| Exception | When |
| --- | --- |
| `BadRequestError` / `ValidationError` | 400 |
| `AuthenticationError` | 401, or the token endpoint rejected the credentials |
| `PermissionDeniedError` | 403: usually a missing scope, or the client hasn't approved new scopes |
| `NotFoundError`, `ConflictError`, `UnprocessableEntityError` | 404, 409, 422 |
| `RateLimitError` | 429 after retries (`.retry_after`) |
| `ServerError` | 5xx after retries |
| `APIConnectionError` / `APITimeoutError` | network problems |
| `APIResponseValidationError` | the API returned something unexpected (`.body` has the raw data) |

All of them inherit from `py24so.Py24soError`.

## Configuration

```python
from py24so import Client24SO, ClientOptions

client = Client24SO(
    options=ClientOptions(
        timeout=30.0,          # seconds
        max_retries=2,         # see "Retries" below
        rate_limit=120,        # optional client-side throttle, requests/minute
        http2=True,            # needs py24so[http2]
        proxy="http://proxy:8080",
        headers={"X-Correlation-Id": "abc"},
    ),
)
```

You can also pass your own `httpx.Client` / `httpx.AsyncClient` as `http_client=...` for custom transports, or to mock the API in your tests.

### Retries

- **Always retried:** connection failures (the request never reached the server), `429`, and `503`.
- **Retried only for `GET`/`PUT`/`DELETE`:** timeouts and `500`/`502`/`504`. These may have been processed already, so a `POST` or `PATCH` is never repeated and can't create a duplicate order or voucher.
- **Timing:** exponential backoff with jitter, honouring `Retry-After`.
- **On a 401:** the token is refreshed and the request retried once.

### Logging

Every request is logged at `DEBUG` on the `py24so` logger, with timing and the `X-Trace-Id`. Retries are logged at `INFO`. Secrets and tokens are never logged.

## Development

```bash
make install-dev       # uv pip install -e ".[dev]"
make test              # unit tests (no network)
make lint              # black, isort, mypy --strict, generated-code check
make check-spec        # diff the live OpenAPI spec against openapi/openapi.json
make test-integration  # live API tests (read-only unless PY24SO_ALLOW_WRITES=1)
```

The async resources in `py24so/resources/_async` are the source of truth. `scripts/unasync.py` (`make generate`) generates the sync resources in `py24so/resources/_sync`, so the two APIs can't drift apart. Don't edit the `_sync` files by hand.

## License

MIT
