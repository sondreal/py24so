"""Core functionality for the 24SevenOffice API client."""

from py24so.core.auth import AsyncOAuth2Client, OAuth2Client, OAuth2Token
from py24so.core.batch import BatchRequest, BatchResponse
from py24so.core.client import APIClient, AsyncAPIClient, BaseClient
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
    handle_api_error,
)
from py24so.core.rate_limiter import RateLimiter

__all__ = [
    "APIClient",
    "AsyncAPIClient",
    "BaseClient",
    "OAuth2Client",
    "AsyncOAuth2Client",
    "OAuth2Token",
    "BatchRequest",
    "BatchResponse",
    "RateLimiter",
    "APIError",
    "AuthenticationError",
    "BatchError",
    "ConnectionError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "TimeoutError",
    "ValidationError",
    "handle_api_error",
]
