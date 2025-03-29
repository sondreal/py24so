import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union, cast

import backoff
import hishel
import httpx
from pydantic import AnyHttpUrl, BaseModel
from tenacity import (
    RetryError,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from py24so.core.auth import AsyncOAuth2Client, OAuth2Client, OAuth2Token
from py24so.core.batch import BatchRequest, BatchResponse
from py24so.core.exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
    handle_api_error,
)
from py24so.core.rate_limiter import RateLimiter
from py24so.models.config import ClientOptions

logger = logging.getLogger("py24so")

T = TypeVar("T", bound=BaseModel)


class BaseClient:
    """
    Base client for the 24SevenOffice API.

    This class provides common functionality for both sync and async client
    implementations, including configuration and request preparation.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        organization_id: str,
        options: Optional[ClientOptions] = None,
    ):
        """
        Initialize the base client.

        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            organization_id: 24SevenOffice organization ID
            options: Client configuration options
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.organization_id = organization_id
        self.options = options or ClientOptions()
        self.rate_limiter = RateLimiter(rate=self.options.rate_limit_rate)


class APIClient(BaseClient):
    """
    Synchronous client for the 24SevenOffice API.

    This class provides methods for making HTTP requests to the API with
    automatic authentication, rate limiting, error handling, and caching.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        organization_id: str,
        options: Optional[ClientOptions] = None,
    ):
        """
        Initialize the API client.

        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            organization_id: 24SevenOffice organization ID
            options: Client configuration options
        """
        super().__init__(client_id, client_secret, organization_id, options)

        # Set up HTTP client with caching if enabled
        transport = None
        if self.options.cache_enabled:
            transport = hishel.CacheTransport(
                transport=httpx.HTTPTransport(http2=self.options.http2),
                cache_control_override_headers={
                    # Force caching even for POST requests
                    "*": f"max-age={self.options.cache_ttl}"
                },
                max_entries=self.options.cache_max_size,
            )
        else:
            transport = httpx.HTTPTransport(http2=self.options.http2)

        self.http_client = httpx.Client(
            base_url=str(self.options.base_url),
            headers=self.options.headers,
            timeout=self.options.timeout,
            proxies=self.options.proxies,
            verify=self.options.verify_ssl,
            transport=transport,
        )

        self.auth_client = OAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            organization_id=self.organization_id,
            http_client=self.http_client,
        )

    def close(self) -> None:
        """Close the HTTP client, releasing resources."""
        if self.http_client:
            self.http_client.close()

    def __enter__(self) -> "APIClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            HTTP response

        Raises:
            APIError: If the request fails
        """
        # Apply rate limiting
        success, wait_time = self.rate_limiter.acquire()
        if not success and wait_time:
            logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
            success, wait_time = self.rate_limiter.acquire()
            if not success:
                raise RateLimitError(
                    f"Rate limit exceeded (rate: {self.options.rate_limit_rate} requests/minute)"
                )

        # Get authorization token
        token = self.auth_client.get_token()

        # Prepare URL
        url = path if path.startswith(("http://", "https://")) else path

        # Make the request with retry logic for certain errors
        try:
            for attempt in Retrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=0.5, max=10),
                retry=retry_if_exception_type((ServerError, ConnectionError, TimeoutError)),
                reraise=True,
            ):
                with attempt:
                    try:
                        headers = kwargs.get("headers", {})
                        # Add auth headers
                        headers.update(token.auth_header)
                        kwargs["headers"] = headers

                        response = self.http_client.request(
                            method=method,
                            url=url,
                            **kwargs,
                        )

                        # Handle error responses
                        if response.status_code >= 400:
                            handle_api_error(response)

                        return response
                    except httpx.TimeoutException as e:
                        raise TimeoutError(f"Request timed out: {str(e)}")
                    except httpx.ConnectError as e:
                        raise ConnectionError(f"Connection error: {str(e)}")

        except RetryError as e:
            if isinstance(e.last_attempt.exception(), APIError):
                raise e.last_attempt.exception()
            raise APIError(f"Request failed after multiple attempts: {str(e)}")

    def send_batch_request(
        self,
        batch: BatchRequest,
        path: str = "/batch",
    ) -> BatchResponse:
        """
        Send a batch request to the API.

        Args:
            batch: Batch request to send
            path: API endpoint path for batch requests

        Returns:
            Batch response

        Raises:
            APIError: If the batch request fails
        """
        if batch.is_empty():
            raise ValueError("Batch is empty")

        response = self.request(
            method="POST",
            path=path,
            json=batch.prepare_request(),
        )

        return BatchResponse(response, batch.request_ids)

    def parse_response(
        self,
        response: httpx.Response,
        model: Type[T],
    ) -> T:
        """
        Parse a response into a Pydantic model.

        Args:
            response: HTTP response
            model: Pydantic model class

        Returns:
            Parsed model instance

        Raises:
            ValidationError: If the response cannot be parsed into the model
        """
        try:
            data = response.json()
            return model.model_validate(data)
        except Exception as e:
            raise ValidationError(
                f"Error parsing response: {str(e)}", response.status_code, response
            )

    def parse_response_list(
        self,
        response: httpx.Response,
        model: Type[T],
    ) -> List[T]:
        """
        Parse a response into a list of Pydantic models.

        Args:
            response: HTTP response
            model: Pydantic model class

        Returns:
            List of parsed model instances

        Raises:
            ValidationError: If the response cannot be parsed into the model list
        """
        try:
            data = response.json()
            if not isinstance(data, list):
                # Handle case where API returns an object with a data field
                data = data.get("data", []) if isinstance(data, dict) else [data]

            return [model.model_validate(item) for item in data]
        except Exception as e:
            raise ValidationError(
                f"Error parsing response list: {str(e)}", response.status_code, response
            )

    def get(
        self,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make a GET request to the API.

        Args:
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            HTTP response
        """
        return self.request("GET", path, **kwargs)

    def post(
        self,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make a POST request to the API.

        Args:
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            HTTP response
        """
        return self.request("POST", path, **kwargs)

    def put(
        self,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make a PUT request to the API.

        Args:
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            HTTP response
        """
        return self.request("PUT", path, **kwargs)

    def patch(
        self,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make a PATCH request to the API.

        Args:
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            HTTP response
        """
        return self.request("PATCH", path, **kwargs)

    def delete(
        self,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make a DELETE request to the API.

        Args:
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            HTTP response
        """
        return self.request("DELETE", path, **kwargs)


class AsyncAPIClient(BaseClient):
    """
    Asynchronous client for the 24SevenOffice API.

    This class provides methods for making asynchronous HTTP requests to the API
    with automatic authentication, rate limiting, error handling, and caching.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        organization_id: str,
        options: Optional[ClientOptions] = None,
    ):
        """
        Initialize the async API client.

        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            organization_id: 24SevenOffice organization ID
            options: Client configuration options
        """
        super().__init__(client_id, client_secret, organization_id, options)

        # Set up HTTP client with caching if enabled
        transport = None
        if self.options.cache_enabled:
            transport = hishel.AsyncCacheTransport(
                transport=httpx.AsyncHTTPTransport(http2=self.options.http2),
                cache_control_override_headers={
                    # Force caching even for POST requests
                    "*": f"max-age={self.options.cache_ttl}"
                },
                max_entries=self.options.cache_max_size,
            )
        else:
            transport = httpx.AsyncHTTPTransport(http2=self.options.http2)

        self.http_client = httpx.AsyncClient(
            base_url=str(self.options.base_url),
            headers=self.options.headers,
            timeout=self.options.timeout,
            proxies=self.options.proxies,
            verify=self.options.verify_ssl,
            transport=transport,
        )

        self.auth_client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            organization_id=self.organization_id,
            http_client=self.http_client,
        )

    async def close(self) -> None:
        """Close the HTTP client, releasing resources."""
        if self.http_client:
            await self.http_client.aclose()

    async def __aenter__(self) -> "AsyncAPIClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make an asynchronous HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            HTTP response

        Raises:
            APIError: If the request fails
        """
        # Apply rate limiting
        success, wait_time = self.rate_limiter.acquire()
        if not success and wait_time:
            logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
            success, wait_time = self.rate_limiter.acquire()
            if not success:
                raise RateLimitError(
                    f"Rate limit exceeded (rate: {self.options.rate_limit_rate} requests/minute)"
                )

        # Get authorization token
        token = await self.auth_client.get_token()

        # Prepare URL
        url = path if path.startswith(("http://", "https://")) else path

        # Make the request with retry logic for certain errors
        retry_count = 0
        max_retries = 3

        while True:
            try:
                headers = kwargs.get("headers", {})
                # Add auth headers
                headers.update(token.auth_header)
                kwargs["headers"] = headers

                response = await self.http_client.request(
                    method=method,
                    url=url,
                    **kwargs,
                )

                # Handle error responses
                if response.status_code >= 400:
                    handle_api_error(response)

                return response

            except (ServerError, ConnectionError, TimeoutError) as e:
                retry_count += 1
                if retry_count >= max_retries:
                    raise

                # Exponential backoff
                wait_time = min(2**retry_count, 10)
                logger.debug(
                    f"Retrying request after error: {str(e)}. Attempt {retry_count} of {max_retries}. Waiting {wait_time}s"
                )
                await asyncio.sleep(wait_time)

            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {str(e)}")
            except httpx.ConnectError as e:
                raise ConnectionError(f"Connection error: {str(e)}")

    async def send_batch_request(
        self,
        batch: BatchRequest,
        path: str = "/batch",
    ) -> BatchResponse:
        """
        Send an asynchronous batch request to the API.

        Args:
            batch: Batch request to send
            path: API endpoint path for batch requests

        Returns:
            Batch response

        Raises:
            APIError: If the batch request fails
        """
        if batch.is_empty():
            raise ValueError("Batch is empty")

        response = await self.request(
            method="POST",
            path=path,
            json=batch.prepare_request(),
        )

        return BatchResponse(response, batch.request_ids)

    async def parse_response(
        self,
        response: httpx.Response,
        model: Type[T],
    ) -> T:
        """
        Parse a response into a Pydantic model.

        Args:
            response: HTTP response
            model: Pydantic model class

        Returns:
            Parsed model instance

        Raises:
            ValidationError: If the response cannot be parsed into the model
        """
        try:
            data = response.json()
            return model.model_validate(data)
        except Exception as e:
            raise ValidationError(
                f"Error parsing response: {str(e)}", response.status_code, response
            )

    async def parse_response_list(
        self,
        response: httpx.Response,
        model: Type[T],
    ) -> List[T]:
        """
        Parse a response into a list of Pydantic models.

        Args:
            response: HTTP response
            model: Pydantic model class

        Returns:
            List of parsed model instances

        Raises:
            ValidationError: If the response cannot be parsed into the model list
        """
        try:
            data = response.json()
            if not isinstance(data, list):
                # Handle case where API returns an object with a data field
                data = data.get("data", []) if isinstance(data, dict) else [data]

            return [model.model_validate(item) for item in data]
        except Exception as e:
            raise ValidationError(
                f"Error parsing response list: {str(e)}", response.status_code, response
            )

    async def get(
        self,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make an asynchronous GET request to the API.

        Args:
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            HTTP response
        """
        return await self.request("GET", path, **kwargs)

    async def post(
        self,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make an asynchronous POST request to the API.

        Args:
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            HTTP response
        """
        return await self.request("POST", path, **kwargs)

    async def put(
        self,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make an asynchronous PUT request to the API.

        Args:
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            HTTP response
        """
        return await self.request("PUT", path, **kwargs)

    async def patch(
        self,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make an asynchronous PATCH request to the API.

        Args:
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            HTTP response
        """
        return await self.request("PATCH", path, **kwargs)

    async def delete(
        self,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make an asynchronous DELETE request to the API.

        Args:
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            HTTP response
        """
        return await self.request("DELETE", path, **kwargs)
