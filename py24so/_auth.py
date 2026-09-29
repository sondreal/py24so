"""OAuth2 client credentials authentication against login.24sevenoffice.com."""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import httpx

from py24so.exceptions import AuthenticationError

logger = logging.getLogger("py24so")


@dataclass(frozen=True)
class AccessToken:
    """A bearer token issued by the 24SevenOffice identity provider."""

    access_token: str = field(repr=False)
    expires_at: float
    token_type: str = "Bearer"
    scope: Optional[str] = None

    def is_expired(self, margin: float = 0.0) -> bool:
        return time.time() >= self.expires_at - margin

    @property
    def authorization(self) -> str:
        # Some identity providers return "bearer"; the API expects "Bearer".
        scheme = "Bearer" if self.token_type.lower() == "bearer" else self.token_type
        return f"{scheme} {self.access_token}"


def token_request_body(
    client_id: str, client_secret: str, organization_id: str, audience: str
) -> Dict[str, str]:
    return {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": audience,
        "login_organization": organization_id,
    }


def parse_token_response(response: httpx.Response) -> AccessToken:
    """Turn a token endpoint response into an :class:`AccessToken` or raise."""
    try:
        data: Any = response.json()
    except ValueError:
        data = None

    if response.status_code != 200 or not isinstance(data, dict):
        message = "Failed to obtain an access token"
        if isinstance(data, dict):
            detail = data.get("error_description") or data.get("error") or data.get("message")
            if detail:
                message = f"{message}: {detail}"
        else:
            message = f"{message} (HTTP {response.status_code})"
        raise AuthenticationError(message, response=response, body=data)

    access_token = data.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise AuthenticationError(
            "Token response did not contain an access_token", response=response, body=data
        )
    try:
        expires_in = float(data.get("expires_in", 3600))
    except (TypeError, ValueError):
        expires_in = 3600.0

    return AccessToken(
        access_token=access_token,
        expires_at=time.time() + expires_in,
        token_type=str(data.get("token_type") or "Bearer"),
        scope=data.get("scope"),
    )


class _TokenState:
    def __init__(self, refresh_margin: float) -> None:
        self.refresh_margin = refresh_margin
        self.token: Optional[AccessToken] = None

    def valid_token(self) -> Optional[AccessToken]:
        token = self.token
        if token is not None and not token.is_expired(self.refresh_margin):
            return token
        return None

    def invalidate(self, token: Optional[AccessToken] = None) -> None:
        # Only drop the token if it is the one that failed; another thread may
        # already have replaced it with a fresh one.
        if token is None or self.token is token:
            self.token = None


class TokenManager(_TokenState):
    """Caches the access token and refreshes it (at most once concurrently)."""

    def __init__(self, fetch: "Any", refresh_margin: float) -> None:
        super().__init__(refresh_margin)
        self._fetch = fetch
        self._lock = threading.Lock()

    def get(self) -> AccessToken:
        token = self.valid_token()
        if token is not None:
            return token
        with self._lock:
            token = self.valid_token()
            if token is None:
                logger.debug("py24so: requesting new access token")
                token = self._fetch()
                self.token = token
            return token


class AsyncTokenManager(_TokenState):
    """Async counterpart of :class:`TokenManager`."""

    def __init__(self, fetch: "Any", refresh_margin: float) -> None:
        super().__init__(refresh_margin)
        self._fetch = fetch
        self._lock: Optional[asyncio.Lock] = None

    async def get(self) -> AccessToken:
        token = self.valid_token()
        if token is not None:
            return token
        # Created lazily so the lock binds to the running event loop.
        if self._lock is None:
            self._lock = asyncio.Lock()
        async with self._lock:
            token = self.valid_token()
            if token is None:
                logger.debug("py24so: requesting new access token")
                token = await self._fetch()
                self.token = token
            return token
