"""
A modern Python client for the 24SevenOffice API.

This package provides a client for the 24SevenOffice API with support for
caching, rate limiting, request batching, and more.
"""

from py24so.core.client import APIClient, AsyncAPIClient
from py24so.core.exceptions import (
    APIError,
    AuthenticationError,
    BatchError,
    ConnectionError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from py24so.endpoints.customers import AsyncCustomerEndpoint, CustomerEndpoint
from py24so.endpoints.invoices import AsyncInvoiceEndpoint, InvoiceEndpoint
from py24so.endpoints.product_categories import (
    AsyncProductCategoryEndpoint,
    ProductCategoryEndpoint,
)
from py24so.endpoints.products import AsyncProductEndpoint, ProductEndpoint
from py24so.models.config import ClientOptions

__version__ = "0.1.0"


class Client24SO:
    """
    24SevenOffice API client.

    This is the main class for interacting with the 24SevenOffice API. It provides
    access to all API endpoints and handles authentication, caching, and rate limiting.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        organization_id: str,
        options: ClientOptions = None,
    ):
        """
        Initialize the 24SevenOffice client.

        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            organization_id: 24SevenOffice organization ID
            options: Client configuration options
        """
        self._api_client = APIClient(
            client_id=client_id,
            client_secret=client_secret,
            organization_id=organization_id,
            options=options,
        )

        # Initialize endpoints
        self.customers = CustomerEndpoint(self._api_client)
        self.invoices = InvoiceEndpoint(self._api_client)
        self.products = ProductEndpoint(self._api_client)
        self.product_categories = ProductCategoryEndpoint(self._api_client)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def close(self):
        """Close the client, releasing resources."""
        if self._api_client:
            self._api_client.close()


class AsyncClient24SO:
    """
    Asynchronous 24SevenOffice API client.

    This is the main class for interacting with the 24SevenOffice API asynchronously. It provides
    access to all API endpoints and handles authentication, caching, and rate limiting.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        organization_id: str,
        options: ClientOptions = None,
    ):
        """
        Initialize the asynchronous 24SevenOffice client.

        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            organization_id: 24SevenOffice organization ID
            options: Client configuration options
        """
        self._api_client = AsyncAPIClient(
            client_id=client_id,
            client_secret=client_secret,
            organization_id=organization_id,
            options=options,
        )

        # Initialize endpoints
        self.customers = AsyncCustomerEndpoint(self._api_client)
        self.invoices = AsyncInvoiceEndpoint(self._api_client)
        self.products = AsyncProductEndpoint(self._api_client)
        self.product_categories = AsyncProductCategoryEndpoint(self._api_client)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the client, releasing resources."""
        if self._api_client:
            await self._api_client.close()


# Export all relevant classes
__all__ = [
    "Client24SO",
    "AsyncClient24SO",
    "ClientOptions",
    "APIError",
    "AuthenticationError",
    "BatchError",
    "ConnectionError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "TimeoutError",
    "ValidationError",
]
