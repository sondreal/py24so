import time
from typing import Dict, Optional, Union

import httpx

from py24so.core.exceptions import AuthenticationError


class OAuth2Token:
    """
    Represents an OAuth2 token with its metadata.

    This class stores the access token and related information such as
    expiration time, token type, and scope.
    """

    def __init__(
        self,
        access_token: str,
        token_type: str,
        expires_in: int,
        scope: Optional[str] = None,
    ):
        """
        Initialize an OAuth2 token.

        Args:
            access_token: The access token string
            token_type: The token type (usually "Bearer")
            expires_in: Token lifetime in seconds
            scope: Space-separated list of granted scopes
        """
        self.access_token = access_token
        self.token_type = token_type
        self.expires_in = expires_in
        self.scope = scope
        self.created_at = time.time()

    @property
    def expires_at(self) -> float:
        """
        Get the token expiration timestamp.

        Returns:
            Unix timestamp when the token expires
        """
        return self.created_at + self.expires_in

    @property
    def is_expired(self) -> bool:
        """
        Check if the token is expired.

        Returns:
            True if the token is expired
        """
        # Consider token expired 30 seconds before actual expiration
        # to avoid edge cases
        return time.time() > (self.expires_at - 30)

    @property
    def auth_header(self) -> Dict[str, str]:
        """
        Get the authorization header for API requests.

        Returns:
            Dictionary with the Authorization header
        """
        return {"Authorization": f"{self.token_type} {self.access_token}"}

    @classmethod
    def from_response(cls, response_data: Dict[str, Union[str, int]]) -> "OAuth2Token":
        """
        Create a token from an API response.

        Args:
            response_data: API response data

        Returns:
            New OAuth2Token instance

        Raises:
            AuthenticationError: If required fields are missing
        """
        try:
            return cls(
                access_token=str(response_data["access_token"]),
                token_type=str(response_data["token_type"]),
                expires_in=int(response_data["expires_in"]),
                scope=str(response_data.get("scope", "")),
            )
        except (KeyError, ValueError) as e:
            raise AuthenticationError(f"Invalid token response: {e}")


class OAuth2Client:
    """
    Handles OAuth2 authentication for the 24SevenOffice API.

    This class manages the OAuth2 token acquisition and refreshing process
    using the client credentials flow.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        organization_id: str,
        token_url: str = "https://rest.api.24sevenoffice.com/oauth2/token",
        http_client: Optional[httpx.Client] = None,
    ):
        """
        Initialize the OAuth2 client.

        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            organization_id: 24SevenOffice organization ID
            token_url: OAuth2 token endpoint URL
            http_client: Optional HTTPX client to use for requests
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.organization_id = organization_id
        self.token_url = token_url
        self.http_client = http_client or httpx.Client()
        self._token: Optional[OAuth2Token] = None

    def get_token(self, force_refresh: bool = False) -> OAuth2Token:
        """
        Get a valid OAuth2 token, refreshing if necessary.

        Args:
            force_refresh: Force token refresh even if current token is valid

        Returns:
            Valid OAuth2Token

        Raises:
            AuthenticationError: If token acquisition fails
        """
        if self._token is None or force_refresh or self._token.is_expired:
            self._token = self._fetch_token()
        return self._token

    def _fetch_token(self) -> OAuth2Token:
        """
        Fetch a new token from the OAuth2 token endpoint.

        Returns:
            New OAuth2Token

        Raises:
            AuthenticationError: If token acquisition fails
        """
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://api.24sevenoffice.com/rest",
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-24so-organizationId": self.organization_id,
        }

        try:
            response = self.http_client.post(
                self.token_url,
                data=data,
                headers=headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = {}
                try:
                    error_data = response.json()
                except (ValueError, httpx.HTTPError):
                    pass

                error_message = error_data.get("error_description", "") or error_data.get(
                    "error", ""
                )
                if not error_message:
                    error_message = f"Failed to obtain token: HTTP {response.status_code}"

                raise AuthenticationError(error_message, response.status_code, response, error_data)

            return OAuth2Token.from_response(response.json())

        except httpx.HTTPError as e:
            raise AuthenticationError(f"HTTP error during authentication: {str(e)}")


class AsyncOAuth2Client:
    """
    Async version of the OAuth2 client for the 24SevenOffice API.

    This class provides the same functionality as OAuth2Client but uses
    async/await for network operations.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        organization_id: str,
        token_url: str = "https://rest.api.24sevenoffice.com/oauth2/token",
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        """
        Initialize the async OAuth2 client.

        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            organization_id: 24SevenOffice organization ID
            token_url: OAuth2 token endpoint URL
            http_client: Optional HTTPX async client to use for requests
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.organization_id = organization_id
        self.token_url = token_url
        self.http_client = http_client
        self._token: Optional[OAuth2Token] = None
        self._client_owned = http_client is None

    async def __aenter__(self) -> "AsyncOAuth2Client":
        """Async context manager entry."""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._client_owned and self.http_client is not None:
            await self.http_client.aclose()

    async def get_token(self, force_refresh: bool = False) -> OAuth2Token:
        """
        Get a valid OAuth2 token, refreshing if necessary.

        Args:
            force_refresh: Force token refresh even if current token is valid

        Returns:
            Valid OAuth2Token

        Raises:
            AuthenticationError: If token acquisition fails
        """
        if self._token is None or force_refresh or self._token.is_expired:
            self._token = await self._fetch_token()
        return self._token

    async def _fetch_token(self) -> OAuth2Token:
        """
        Fetch a new token from the OAuth2 token endpoint.

        Returns:
            New OAuth2Token

        Raises:
            AuthenticationError: If token acquisition fails
        """
        if self.http_client is None:
            self.http_client = httpx.AsyncClient()
            self._client_owned = True

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://api.24sevenoffice.com/rest",
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-24so-organizationId": self.organization_id,
        }

        try:
            response = await self.http_client.post(
                self.token_url,
                data=data,
                headers=headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = {}
                try:
                    error_data = response.json()
                except (ValueError, httpx.HTTPError):
                    pass

                error_message = error_data.get("error_description", "") or error_data.get(
                    "error", ""
                )
                if not error_message:
                    error_message = f"Failed to obtain token: HTTP {response.status_code}"

                raise AuthenticationError(error_message, response.status_code, response, error_data)

            return OAuth2Token.from_response(response.json())

        except httpx.HTTPError as e:
            raise AuthenticationError(f"HTTP error during authentication: {str(e)}")
