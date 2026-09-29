"""
py24so: a typed Python client for the 24SevenOffice REST API.

    from py24so import Client24SO

    with Client24SO(client_id, client_secret, organization_id) as client:
        for customer in client.customers.list(is_company=True):
            print(customer.id, customer.name)

See https://rest.api.24sevenoffice.com/v1/openapi.json for the API reference.
"""

from py24so import models
from py24so._auth import AccessToken
from py24so._client import APIClient, AsyncAPIClient
from py24so._options import ClientOptions
from py24so._pagination import AsyncPaginator, Page, Paginator
from py24so._version import __version__
from py24so.exceptions import (
    APIConnectionError,
    APIError,
    APIResponseValidationError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    Py24soError,
    RateLimitError,
    ServerError,
    UnprocessableEntityError,
    ValidationError,
)
from py24so.resources._async.client import AsyncClient24SO
from py24so.resources._sync.client import Client24SO

__all__ = [
    "__version__",
    "Client24SO",
    "AsyncClient24SO",
    "ClientOptions",
    "APIClient",
    "AsyncAPIClient",
    "AccessToken",
    "Page",
    "Paginator",
    "AsyncPaginator",
    "models",
    # Exceptions
    "Py24soError",
    "APIError",
    "APIConnectionError",
    "APITimeoutError",
    "APIResponseValidationError",
    "APIStatusError",
    "BadRequestError",
    "ValidationError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "RateLimitError",
    "ServerError",
]
