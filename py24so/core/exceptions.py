from typing import Any, Dict, Optional

import httpx


class APIError(Exception):
    """Base exception for all API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[httpx.Response] = None,
        error_data: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response = response
        self.error_data = error_data
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.status_code:
            return f"{self.message} (Status: {self.status_code})"
        return self.message


class AuthenticationError(APIError):
    """Raised when there is an issue with authentication."""

    pass


class RateLimitError(APIError):
    """Raised when the API rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        status_code: Optional[int] = 429,
        response: Optional[httpx.Response] = None,
        error_data: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ):
        self.retry_after = retry_after
        super().__init__(message, status_code, response, error_data)

    def __str__(self) -> str:
        if self.retry_after:
            return f"{self.message} (Retry after: {self.retry_after} seconds)"
        return super().__str__()


class NotFoundError(APIError):
    """Raised when a resource is not found."""

    pass


class ValidationError(APIError):
    """Raised when request data fails validation."""

    pass


class ServerError(APIError):
    """Raised when the server returns a 5xx error."""

    pass


class TimeoutError(APIError):
    """Raised when a request times out."""

    pass


class ConnectionError(APIError):
    """Raised when there's a connection error."""

    pass


class BatchError(APIError):
    """Raised when there's an error with a batch request."""

    def __init__(
        self,
        message: str,
        batch_results: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        self.batch_results = batch_results
        super().__init__(message, **kwargs)


def handle_api_error(response: httpx.Response) -> None:
    """
    Handle and raise appropriate exceptions based on API response.

    Args:
        response: The HTTP response from the API

    Raises:
        AuthenticationError: For 401 errors
        RateLimitError: For 429 errors
        NotFoundError: For 404 errors
        ValidationError: For 400 errors
        ServerError: For 5xx errors
        APIError: For all other errors
    """
    error_data = None
    try:
        error_data = response.json()
    except (ValueError, httpx.HTTPError):
        pass

    status_code = response.status_code
    error_message = (
        error_data.get("message", "") if error_data and isinstance(error_data, dict) else ""
    )
    if not error_message:
        error_message = f"HTTP Error {status_code}: {response.reason_phrase}"

    if status_code == 401:
        raise AuthenticationError(error_message, status_code, response, error_data)
    elif status_code == 429:
        retry_after = None
        if "Retry-After" in response.headers:
            try:
                retry_after = int(response.headers["Retry-After"])
            except (ValueError, TypeError):
                pass
        raise RateLimitError(error_message, status_code, response, error_data, retry_after)
    elif status_code == 404:
        raise NotFoundError(error_message, status_code, response, error_data)
    elif status_code == 400:
        raise ValidationError(error_message, status_code, response, error_data)
    elif 500 <= status_code < 600:
        raise ServerError(error_message, status_code, response, error_data)
    else:
        raise APIError(error_message, status_code, response, error_data) 