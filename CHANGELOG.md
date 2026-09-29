# Changelog

## 0.3.0

A rewrite against the official 24SevenOffice OpenAPI specification (v0.60.1).
Previous releases could not talk to the API, so there is no upgrade path from
them; see the README for the new interface.

### Fixed
- **Packaging:** the published wheels only contained `py24so/__init__.py`, so
  `import py24so` failed. All subpackages and a `py.typed` marker are now included.
- **Client construction:** `Client24SO(...)` crashed. hishel 0.1 removed
  `cache_control_override_headers`, and httpx 0.28 removed `proxies=`.
- **Authentication:** it used a non-existent endpoint and flow. It now uses the
  documented client credentials flow: a JSON `POST` to
  `https://login.24sevenoffice.com/oauth/token` with `audience` and
  `login_organization`.
- **Endpoints:** `/invoices` and `/batch` do not exist in the API and have been
  removed. Invoicing is done through sales orders (`sales_orders.invoice()`).
- **Models:** they did not match the API. All models are rebuilt from the spec,
  using the API's field names.
- **Pagination:** it used a non-existent `pageSize` parameter. Lists now follow the
  API's `Link` headers, with `limit` as the page size.
- **Caching:** responses, including `POST`s, were cached for 5 minutes by default,
  so writes could be silently dropped and stale data returned. Caching is removed.
- **Retries:** `POST` requests were retried on 5xx, which risked duplicate orders.
  Retries are now safe per HTTP method and honour `Retry-After`.
- **Concurrency:** the rate limiter and token refresh were not thread-safe.
- **Deletes:** a `200` response to `delete()` raised an error.
- **Dependencies:** `pytest-asyncio`, `python-dotenv`, `tenacity`, `backoff`,
  `hishel` and `email-validator` are no longer runtime dependencies. Only `httpx`
  and `pydantic` remain.

### Added
- Coverage of all 79 operations in the spec, as `Client24SO` and `AsyncClient24SO`.
- Lazy auto-pagination (`for item in client.customers.list()`), `to_list(max_items)`,
  `pages()` and `first_page()`.
- A typed exception hierarchy with the API's `trackingId`, `X-Trace-Id`,
  validation errors and business errors.
- Automatic token refresh on expiry and on 401, shared safely across threads and tasks.
- An optional client-side rate limit, HTTP/2, proxy support, and bring-your-own
  `httpx` client.
- Credentials from the `PY24SO_*` environment variables.
- File uploads (`files.upload`) and sales order attachments.
- `client.request()` as an escape hatch for endpoints not wrapped yet.
- `scripts/check_spec.py` to detect API changes; `mypy --strict` in CI; tests on
  Python 3.9–3.13 and on the minimum supported httpx/pydantic.
