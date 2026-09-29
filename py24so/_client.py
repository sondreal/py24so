"""Low-level HTTP clients: authentication, retries, throttling, errors and parsing."""

import asyncio
import logging
import os
import platform
import random
import time
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
    get_origin,
    overload,
)

import httpx
import pydantic

from py24so._auth import (
    AccessToken,
    AsyncTokenManager,
    TokenManager,
    parse_token_response,
    token_request_body,
)
from py24so._options import ClientOptions
from py24so._pagination import AsyncPaginator, Paginator
from py24so._rate_limiter import RateLimiter
from py24so._utils import build_params, parse_retry_after, type_adapter, unwrap_list
from py24so._version import __version__
from py24so.exceptions import (
    APIConnectionError,
    APIResponseValidationError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
    UnprocessableEntityError,
    ValidationError,
)
from py24so.models._base import RESPONSE_CONTEXT

logger = logging.getLogger("py24so")

T = TypeVar("T")

ENV_CLIENT_ID = "PY24SO_CLIENT_ID"
ENV_CLIENT_SECRET = "PY24SO_CLIENT_SECRET"
ENV_ORGANIZATION_ID = "PY24SO_ORGANIZATION_ID"

_IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})
# The server did not process the request, so retrying is safe for every method.
_RETRY_ALWAYS_STATUSES = frozenset({429, 503})
# The server may have processed the request; only retry idempotent methods.
_RETRY_IDEMPOTENT_STATUSES = frozenset({408, 500, 502, 504})

_STATUS_ERRORS: Dict[int, Type[APIStatusError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    422: UnprocessableEntityError,
    429: RateLimitError,
}


def _error_message(response: httpx.Response, body: Any) -> str:
    message: Optional[str] = None
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            message = error.get("message") or error.get("name")
            payload = error.get("payload")
            if isinstance(payload, dict):
                details = []
                for item in payload.get("validationErrors") or []:
                    if isinstance(item, dict):
                        details.append(f"{item.get('path', '?')} ({item.get('keyword', '?')})")
                for item in payload.get("errors") or []:
                    if isinstance(item, dict):
                        details.append(str(item.get("message") or item.get("type") or item))
                if details:
                    message = f"{message or 'Request failed'}: {'; '.join(details)}"
        elif isinstance(error, str):
            message = body.get("error_description") or error
        message = message or body.get("message") or body.get("title")
    elif isinstance(body, str) and body.strip():
        message = body.strip()[:500]
    return str(message) if message else f"HTTP {response.status_code} {response.reason_phrase}"


def make_status_error(response: httpx.Response) -> APIStatusError:
    """Build the right :class:`APIStatusError` subclass for an error response."""
    try:
        body: Any = response.json()
    except ValueError:
        body = response.text or None

    message = _error_message(response, body)
    status = response.status_code

    if status == 429:
        return RateLimitError(
            message,
            response=response,
            body=body,
            retry_after=parse_retry_after(response.headers.get("retry-after")),
        )
    if status == 400:
        error = body.get("error") if isinstance(body, dict) else None
        if isinstance(error, dict) and error.get("name") == "ValidationError":
            return ValidationError(message, response=response, body=body)
    if status == 403:
        message += (
            " (check that the application has the required scopes and that the "
            "client organization has approved them)"
        )
    if status >= 500:
        return ServerError(message, response=response, body=body)
    return _STATUS_ERRORS.get(status, APIStatusError)(message, response=response, body=body)


def _user_agent() -> str:
    return f"py24so/{__version__} python/{platform.python_version()} " f"httpx/{httpx.__version__}"


def _require(value: Optional[Union[str, int]], name: str, env: str) -> str:
    if value is None:
        value = os.environ.get(env)
    text = str(value).strip() if value is not None else ""
    if not text:
        raise ValueError(f"{name} is required (pass it explicitly or set the {env} env var)")
    return text


class _BaseAPIClient:
    """State and logic shared by :class:`APIClient` and :class:`AsyncAPIClient`."""

    def __init__(
        self,
        client_id: Optional[str],
        client_secret: Optional[str],
        organization_id: Optional[Union[str, int]],
        options: Optional[ClientOptions],
    ) -> None:
        self.client_id = _require(client_id, "client_id", ENV_CLIENT_ID)
        self._client_secret = _require(client_secret, "client_secret", ENV_CLIENT_SECRET)
        self.organization_id = _require(organization_id, "organization_id", ENV_ORGANIZATION_ID)
        self.options = options or ClientOptions()

        base = httpx.URL(self.options.base_url)
        if base.scheme not in ("http", "https") or not base.host:
            raise ValueError(f"Invalid base_url: {self.options.base_url!r}")
        self._base_url = base.copy_with(path=base.path.rstrip("/") + "/")
        self._rate_limiter = (
            RateLimiter(self.options.rate_limit) if self.options.rate_limit else None
        )
        self._default_headers = {
            "Accept": "application/json",
            "User-Agent": _user_agent(),
            **self.options.headers,
        }

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(organization_id={self.organization_id!r}, "
            f"base_url={str(self._base_url)!r})"
        )

    # URLs -----------------------------------------------------------------

    def _url(self, path_or_url: str) -> httpx.URL:
        if path_or_url.startswith(("http://", "https://")):
            url = httpx.URL(path_or_url)
        else:
            url = self._base_url.join(path_or_url.lstrip("/"))
        self._check_same_origin(url)
        return url

    def _check_same_origin(self, url: httpx.URL) -> None:
        if (url.scheme, url.host, url.port) != (
            self._base_url.scheme,
            self._base_url.host,
            self._base_url.port,
        ):
            # Never send the bearer token to a host other than the API.
            raise APIConnectionError(f"Refusing to send credentials to foreign URL {url}")

    def resolve_link(self, link: str, base: Optional[httpx.URL] = None) -> str:
        """Resolve a ``Link`` header URL against the URL it was returned for (RFC 8288)."""
        url = (base or self._base_url).join(link)
        self._check_same_origin(url)
        return str(url)

    # Retry policy -----------------------------------------------------------

    def _should_retry_status(self, method: str, status: int) -> bool:
        return status in _RETRY_ALWAYS_STATUSES or (
            method in _IDEMPOTENT_METHODS and status in _RETRY_IDEMPOTENT_STATUSES
        )

    @staticmethod
    def _should_retry_exception(method: str, exc: httpx.RequestError) -> bool:
        # The request never reached the server: always safe to retry.
        if isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout)):
            return True
        # It may have reached the server: only retry if repeating it is harmless.
        return method in _IDEMPOTENT_METHODS and isinstance(exc, httpx.TransportError)

    def _retry_delay(self, attempt: int, response: Optional[httpx.Response] = None) -> float:
        if response is not None:
            retry_after = parse_retry_after(response.headers.get("retry-after"))
            if retry_after is not None:
                return min(retry_after, self.options.max_retry_delay)
        delay = min(self.options.retry_backoff * (2**attempt), self.options.max_retry_delay)
        jitter = 1 - 0.25 * random.random()  # avoid synchronized retries across clients
        return float(delay * jitter)

    @staticmethod
    def _wrap_exception(exc: httpx.RequestError, request: httpx.Request) -> Exception:
        if isinstance(exc, httpx.TimeoutException):
            return APITimeoutError(f"Request timed out: {exc!r}", request=request)
        return APIConnectionError(f"Connection error: {exc!r}", request=request)

    # Requests & responses -------------------------------------------------------

    def _build_request(
        self,
        http: Union[httpx.Client, httpx.AsyncClient],
        method: str,
        url: Union[str, httpx.URL],
        *,
        params: Optional[Mapping[str, Any]],
        json: Any,
        content: Optional[bytes],
        headers: Optional[Mapping[str, str]],
        token: Optional[AccessToken],
    ) -> httpx.Request:
        merged = {**self._default_headers, **(headers or {})}
        if token is not None:
            merged["Authorization"] = token.authorization
        return http.build_request(
            method,
            url,
            params=build_params(params) or None,
            json=json,
            content=content,
            headers=merged,
        )

    def _token_request(self, http: Union[httpx.Client, httpx.AsyncClient]) -> httpx.Request:
        return http.build_request(
            "POST",
            self.options.token_url,
            json=token_request_body(
                self.client_id, self._client_secret, self.organization_id, self.options.audience
            ),
            headers={
                "Accept": "application/json",
                "User-Agent": self._default_headers["User-Agent"],
            },
        )

    @staticmethod
    def _log_response(response: httpx.Response, started: float) -> None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "py24so: %s %s -> %s (%.0f ms, trace id %s)",
                response.request.method,
                response.request.url,
                response.status_code,
                (time.monotonic() - started) * 1000,
                response.headers.get("x-trace-id"),
            )

    @staticmethod
    def _decode(response: httpx.Response) -> Any:
        if response.status_code == 204 or not response.content.strip():
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise APIResponseValidationError(
                "Response body is not valid JSON", response=response, body=response.text
            ) from exc

    def parse(self, response: httpx.Response, cast_to: Any) -> Any:
        """Decode a response body and validate it into ``cast_to``."""
        data = self._decode(response)
        if cast_to is None or data is None:
            return None
        if cast_to is Any:
            return data
        if get_origin(cast_to) in (list, List):
            data = unwrap_list(data)
        try:
            return type_adapter(cast_to).validate_python(data, context=RESPONSE_CONTEXT)
        except pydantic.ValidationError as exc:
            raise APIResponseValidationError(
                f"Unexpected response format from {response.request.method} "
                f"{response.request.url.path}: {exc}",
                response=response,
                body=data,
            ) from exc

    def parse_model(self, response: httpx.Response, model: Type[T]) -> T:
        """Like :meth:`parse`, but a response body is required."""
        result = self.parse(response, model)
        if result is None:
            raise APIResponseValidationError(
                f"Expected a {model.__name__} in the response but the body was empty",
                response=response,
            )
        return cast(T, result)

    def parse_list(self, response: httpx.Response, item_type: Type[T]) -> List[T]:
        result = self.parse(response, List[item_type])  # type: ignore[valid-type]
        return result if result is not None else []


class APIClient(_BaseAPIClient):
    """Synchronous low-level client. Most users want :class:`py24so.Client24SO`."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        organization_id: Optional[Union[str, int]] = None,
        options: Optional[ClientOptions] = None,
        *,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        super().__init__(client_id, client_secret, organization_id, options)
        self._owns_http_client = http_client is None
        if http_client is None:
            try:
                http_client = httpx.Client(
                    timeout=self.options.timeout,
                    http2=self.options.http2,
                    proxy=self.options.proxy,
                    verify=self.options.verify_ssl,
                    follow_redirects=False,
                )
            except ImportError as exc:
                raise ImportError(
                    "HTTP/2 support requires the 'h2' package: pip install 'py24so[http2]'"
                ) from exc
        self._http = http_client
        self._tokens = TokenManager(self._fetch_token, self.options.token_refresh_margin)

    def close(self) -> None:
        """Release network resources. Only closes an ``http_client`` we created."""
        if self._owns_http_client:
            self._http.close()

    def __enter__(self) -> "APIClient":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def _sleep(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)

    def _fetch_token(self) -> AccessToken:
        attempt = 0
        while True:
            request = self._token_request(self._http)
            try:
                response = self._http.send(request)
            except httpx.RequestError as exc:
                if attempt < self.options.max_retries:
                    self._sleep(self._retry_delay(attempt))
                    attempt += 1
                    continue
                raise self._wrap_exception(exc, request) from exc
            if response.status_code in (429,) or response.status_code >= 500:
                if attempt < self.options.max_retries:
                    self._sleep(self._retry_delay(attempt, response))
                    attempt += 1
                    continue
                raise make_status_error(response)
            return parse_token_response(response)

    def get_access_token(self) -> str:
        """Return a valid access token, fetching or refreshing it if needed."""
        return self._tokens.get().access_token

    def send(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        content: Optional[bytes] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> httpx.Response:
        """Send an authenticated request with retries; raise on error statuses."""
        method = method.upper()
        url = self._url(path)
        attempt = 0
        reauthenticated = False
        while True:
            if self._rate_limiter is not None:
                self._sleep(self._rate_limiter.reserve())
            token = self._tokens.get()
            request = self._build_request(
                self._http,
                method,
                url,
                params=params,
                json=json,
                content=content,
                headers=headers,
                token=token,
            )
            started = time.monotonic()
            try:
                response = self._http.send(request)
            except httpx.RequestError as exc:
                if attempt < self.options.max_retries and self._should_retry_exception(method, exc):
                    delay = self._retry_delay(attempt)
                    logger.info("py24so: %r, retrying %s %s in %.1fs", exc, method, url, delay)
                    self._sleep(delay)
                    attempt += 1
                    continue
                raise self._wrap_exception(exc, request) from exc

            self._log_response(response, started)
            if response.is_success:
                return response
            if response.status_code == 401 and not reauthenticated:
                # The token may have been revoked or expired early: refresh once.
                reauthenticated = True
                self._tokens.invalidate(token)
                continue
            if attempt < self.options.max_retries and self._should_retry_status(
                method, response.status_code
            ):
                delay = self._retry_delay(attempt, response)
                logger.info(
                    "py24so: HTTP %s, retrying %s %s in %.1fs",
                    response.status_code,
                    method,
                    url,
                    delay,
                )
                self._sleep(delay)
                attempt += 1
                continue
            raise make_status_error(response)

    def send_external(
        self, method: str, url: str, *, content: bytes, headers: Mapping[str, str]
    ) -> httpx.Response:
        """Send a request to a non-API URL (e.g. a pre-signed upload URL) without credentials."""
        method = method.upper()
        attempt = 0
        while True:
            request = self._http.build_request(method, url, content=content, headers=headers)
            try:
                response = self._http.send(request)
            except httpx.RequestError as exc:
                if attempt < self.options.max_retries and self._should_retry_exception(method, exc):
                    self._sleep(self._retry_delay(attempt))
                    attempt += 1
                    continue
                raise self._wrap_exception(exc, request) from exc
            if response.is_success:
                return response
            if attempt < self.options.max_retries and self._should_retry_status(
                method, response.status_code
            ):
                self._sleep(self._retry_delay(attempt, response))
                attempt += 1
                continue
            raise make_status_error(response)

    @overload
    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        content: Optional[bytes] = None,
        headers: Optional[Mapping[str, str]] = None,
        cast_to: Type[T],
    ) -> T: ...

    @overload
    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        content: Optional[bytes] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any: ...

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        content: Optional[bytes] = None,
        headers: Optional[Mapping[str, str]] = None,
        cast_to: Any = None,
    ) -> Any:
        """Send a request and return the response body.

        With ``cast_to`` the body is validated into that type (and must not be
        empty); without it the decoded JSON is returned as-is.
        """
        response = self.send(
            method, path, params=params, json=json, content=content, headers=headers
        )
        if cast_to is None:
            return self.parse(response, Any)
        return self.parse_model(response, cast_to)

    def paginate(
        self,
        path: str,
        item_type: Type[T],
        params: Optional[Mapping[str, Any]] = None,
        *,
        page_param: Optional[str] = None,
        page_size: Optional[int] = None,
    ) -> Paginator[T]:
        return Paginator(self, path, item_type, params, page_param=page_param, page_size=page_size)


class AsyncAPIClient(_BaseAPIClient):
    """Asynchronous low-level client. Most users want :class:`py24so.AsyncClient24SO`."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        organization_id: Optional[Union[str, int]] = None,
        options: Optional[ClientOptions] = None,
        *,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        super().__init__(client_id, client_secret, organization_id, options)
        self._owns_http_client = http_client is None
        if http_client is None:
            try:
                http_client = httpx.AsyncClient(
                    timeout=self.options.timeout,
                    http2=self.options.http2,
                    proxy=self.options.proxy,
                    verify=self.options.verify_ssl,
                    follow_redirects=False,
                )
            except ImportError as exc:
                raise ImportError(
                    "HTTP/2 support requires the 'h2' package: pip install 'py24so[http2]'"
                ) from exc
        self._http = http_client
        self._tokens = AsyncTokenManager(self._fetch_token, self.options.token_refresh_margin)

    async def close(self) -> None:
        """Release network resources. Only closes an ``http_client`` we created."""
        if self._owns_http_client:
            await self._http.aclose()

    async def __aenter__(self) -> "AsyncAPIClient":
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.close()

    async def _sleep(self, seconds: float) -> None:
        if seconds > 0:
            await asyncio.sleep(seconds)

    async def _fetch_token(self) -> AccessToken:
        attempt = 0
        while True:
            request = self._token_request(self._http)
            try:
                response = await self._http.send(request)
            except httpx.RequestError as exc:
                if attempt < self.options.max_retries:
                    await self._sleep(self._retry_delay(attempt))
                    attempt += 1
                    continue
                raise self._wrap_exception(exc, request) from exc
            if response.status_code in (429,) or response.status_code >= 500:
                if attempt < self.options.max_retries:
                    await self._sleep(self._retry_delay(attempt, response))
                    attempt += 1
                    continue
                raise make_status_error(response)
            return parse_token_response(response)

    async def get_access_token(self) -> str:
        """Return a valid access token, fetching or refreshing it if needed."""
        return (await self._tokens.get()).access_token

    async def send(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        content: Optional[bytes] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> httpx.Response:
        """Send an authenticated request with retries; raise on error statuses."""
        method = method.upper()
        url = self._url(path)
        attempt = 0
        reauthenticated = False
        while True:
            if self._rate_limiter is not None:
                await self._sleep(self._rate_limiter.reserve())
            token = await self._tokens.get()
            request = self._build_request(
                self._http,
                method,
                url,
                params=params,
                json=json,
                content=content,
                headers=headers,
                token=token,
            )
            started = time.monotonic()
            try:
                response = await self._http.send(request)
            except httpx.RequestError as exc:
                if attempt < self.options.max_retries and self._should_retry_exception(method, exc):
                    delay = self._retry_delay(attempt)
                    logger.info("py24so: %r, retrying %s %s in %.1fs", exc, method, url, delay)
                    await self._sleep(delay)
                    attempt += 1
                    continue
                raise self._wrap_exception(exc, request) from exc

            self._log_response(response, started)
            if response.is_success:
                return response
            if response.status_code == 401 and not reauthenticated:
                reauthenticated = True
                self._tokens.invalidate(token)
                continue
            if attempt < self.options.max_retries and self._should_retry_status(
                method, response.status_code
            ):
                delay = self._retry_delay(attempt, response)
                logger.info(
                    "py24so: HTTP %s, retrying %s %s in %.1fs",
                    response.status_code,
                    method,
                    url,
                    delay,
                )
                await self._sleep(delay)
                attempt += 1
                continue
            raise make_status_error(response)

    async def send_external(
        self, method: str, url: str, *, content: bytes, headers: Mapping[str, str]
    ) -> httpx.Response:
        """Send a request to a non-API URL (e.g. a pre-signed upload URL) without credentials."""
        method = method.upper()
        attempt = 0
        while True:
            request = self._http.build_request(method, url, content=content, headers=headers)
            try:
                response = await self._http.send(request)
            except httpx.RequestError as exc:
                if attempt < self.options.max_retries and self._should_retry_exception(method, exc):
                    await self._sleep(self._retry_delay(attempt))
                    attempt += 1
                    continue
                raise self._wrap_exception(exc, request) from exc
            if response.is_success:
                return response
            if attempt < self.options.max_retries and self._should_retry_status(
                method, response.status_code
            ):
                await self._sleep(self._retry_delay(attempt, response))
                attempt += 1
                continue
            raise make_status_error(response)

    @overload
    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        content: Optional[bytes] = None,
        headers: Optional[Mapping[str, str]] = None,
        cast_to: Type[T],
    ) -> T: ...

    @overload
    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        content: Optional[bytes] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any: ...

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        content: Optional[bytes] = None,
        headers: Optional[Mapping[str, str]] = None,
        cast_to: Any = None,
    ) -> Any:
        """Send a request and return the response body.

        With ``cast_to`` the body is validated into that type (and must not be
        empty); without it the decoded JSON is returned as-is.
        """
        response = await self.send(
            method, path, params=params, json=json, content=content, headers=headers
        )
        if cast_to is None:
            return self.parse(response, Any)
        return self.parse_model(response, cast_to)

    def paginate(
        self,
        path: str,
        item_type: Type[T],
        params: Optional[Mapping[str, Any]] = None,
        *,
        page_param: Optional[str] = None,
        page_size: Optional[int] = None,
    ) -> AsyncPaginator[T]:
        return AsyncPaginator(
            self, path, item_type, params, page_param=page_param, page_size=page_size
        )
