"""
Exception hierarchy for py24so.

Every exception raised by the client derives from :class:`Py24soError`::

    Py24soError
    └── APIError
        ├── APIConnectionError
        │   └── APITimeoutError
        ├── APIResponseValidationError
        └── APIStatusError
            ├── BadRequestError               (400)
            │   └── ValidationError           (400, error.name == "ValidationError")
            ├── AuthenticationError           (401, or a failed token request)
            ├── PermissionDeniedError         (403)
            ├── NotFoundError                 (404)
            ├── ConflictError                 (409)
            ├── UnprocessableEntityError      (422)
            ├── RateLimitError                (429)
            └── ServerError                   (5xx)

The 24SevenOffice API reports errors as::

    {"error": {"name": "...", "message": "...", "payload": {...}}, "trackingId": "..."}

These fields are exposed as attributes on :class:`APIStatusError`. Include
``tracking_id`` / ``trace_id`` when contacting 24SevenOffice support.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

__all__ = [
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


class Py24soError(Exception):
    """Base class for every exception raised by py24so."""


class APIError(Py24soError):
    """Base class for errors that happen while talking to the API."""

    def __init__(self, message: str, *, request: Optional[httpx.Request] = None) -> None:
        super().__init__(message)
        self.message = message
        self.request = request


class APIConnectionError(APIError):
    """The API could not be reached (DNS failure, refused connection, TLS error, ...)."""

    def __init__(
        self, message: str = "Connection error.", *, request: Optional[httpx.Request] = None
    ) -> None:
        super().__init__(message, request=request)


class APITimeoutError(APIConnectionError):
    """The request timed out."""

    def __init__(
        self, message: str = "Request timed out.", *, request: Optional[httpx.Request] = None
    ) -> None:
        super().__init__(message, request=request)


class APIResponseValidationError(APIError):
    """The API returned data that does not match the expected schema.

    The undecoded payload is available as :attr:`body` so no data is lost.
    """

    def __init__(
        self,
        message: str,
        *,
        response: httpx.Response,
        body: Any = None,
    ) -> None:
        super().__init__(message, request=response.request)
        self.response = response
        self.status_code = response.status_code
        self.body = body


class APIStatusError(APIError):
    """The API responded with a 4xx or 5xx status code."""

    status_code: int

    def __init__(
        self,
        message: str,
        *,
        response: httpx.Response,
        body: Any = None,
    ) -> None:
        super().__init__(message, request=response.request)
        self.response = response
        self.status_code = response.status_code
        self.body = body

        error = body.get("error") if isinstance(body, dict) else None
        if not isinstance(error, dict):
            error = {}
        #: The ``error.name`` returned by the API, e.g. ``"ValidationError"``.
        self.error_name: Optional[str] = error.get("name") or None
        #: The ``error.payload`` returned by the API, if any.
        self.payload: Dict[str, Any] = (
            error["payload"] if isinstance(error.get("payload"), dict) else {}
        )
        #: The ``trackingId`` returned in the error body.
        self.tracking_id: Optional[str] = (
            body.get("trackingId") if isinstance(body, dict) else None
        ) or None
        #: The ``X-Trace-Id`` response header.
        self.trace_id: Optional[str] = response.headers.get("x-trace-id")

    def __str__(self) -> str:
        parts = [f"{self.status_code}: {self.message}"]
        if self.tracking_id:
            parts.append(f"tracking_id={self.tracking_id}")
        elif self.trace_id:
            parts.append(f"trace_id={self.trace_id}")
        return " ".join(parts)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({str(self)!r})"


class BadRequestError(APIStatusError):
    """400 Bad Request.

    :attr:`errors` holds the structured ``error.payload.errors`` list, e.g.
    ``[{"type": "NoLines", "message": "No lines in the sales order", ...}]``.
    """

    status_code = 400

    @property
    def errors(self) -> List[Dict[str, Any]]:
        errors = self.payload.get("errors")
        return errors if isinstance(errors, list) else []


class ValidationError(BadRequestError):
    """400 with ``error.name == "ValidationError"``: the request body failed schema validation.

    :attr:`validation_errors` holds entries such as
    ``{"path": "customer.name", "keyword": "required"}``.
    """

    @property
    def validation_errors(self) -> List[Dict[str, Any]]:
        errors = self.payload.get("validationErrors")
        return errors if isinstance(errors, list) else []


class AuthenticationError(APIStatusError):
    """401 Unauthorized, or the OAuth token endpoint rejected the client credentials."""

    status_code = 401


class PermissionDeniedError(APIStatusError):
    """403 Forbidden.

    Usually means the application is missing a scope, or the client organization
    has not approved all scopes the application requests.
    """

    status_code = 403


class NotFoundError(APIStatusError):
    """404 Not Found."""

    status_code = 404


class ConflictError(APIStatusError):
    """409 Conflict, e.g. creating a resource that already exists."""

    status_code = 409


class UnprocessableEntityError(APIStatusError):
    """422 Unprocessable Entity."""

    status_code = 422


class RateLimitError(APIStatusError):
    """429 Too Many Requests. :attr:`retry_after` is the server-suggested delay in seconds."""

    status_code = 429

    def __init__(
        self,
        message: str,
        *,
        response: httpx.Response,
        body: Any = None,
        retry_after: Optional[float] = None,
    ) -> None:
        super().__init__(message, response=response, body=body)
        self.retry_after = retry_after


class ServerError(APIStatusError):
    """5xx: something went wrong on 24SevenOffice's side."""
