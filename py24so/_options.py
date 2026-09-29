from typing import Dict, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

DEFAULT_BASE_URL = "https://rest.api.24sevenoffice.com/v1"
DEFAULT_TOKEN_URL = "https://login.24sevenoffice.com/oauth/token"
DEFAULT_AUDIENCE = "https://api.24sevenoffice.com"


class ClientOptions(BaseModel):
    """Configuration for :class:`~py24so.Client24SO` and :class:`~py24so.AsyncClient24SO`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    base_url: str = Field(
        default=DEFAULT_BASE_URL,
        description="Base URL of the 24SevenOffice REST API.",
    )
    token_url: str = Field(
        default=DEFAULT_TOKEN_URL,
        description="OAuth2 token endpoint used for the client credentials flow.",
    )
    audience: str = Field(
        default=DEFAULT_AUDIENCE,
        description="OAuth2 audience requested for the access token.",
    )
    timeout: float = Field(
        default=30.0,
        gt=0,
        description="Timeout in seconds for connecting, reading and writing.",
    )
    max_retries: int = Field(
        default=2,
        ge=0,
        description=(
            "How many times a failed request is retried. Connection errors, 429 and 503 "
            "are retried for every method; timeouts and other 5xx errors only for "
            "idempotent methods (GET, PUT, DELETE), so writes are never duplicated."
        ),
    )
    retry_backoff: float = Field(
        default=0.5,
        ge=0,
        description="Base delay in seconds for exponential backoff between retries.",
    )
    max_retry_delay: float = Field(
        default=30.0,
        ge=0,
        description="Upper bound in seconds for any single retry delay, incl. Retry-After.",
    )
    rate_limit: Optional[int] = Field(
        default=None,
        ge=1,
        description=(
            "Client-side limit in requests per minute. Requests wait until a slot is "
            "free. None disables client-side throttling (429s are still retried)."
        ),
    )
    token_refresh_margin: float = Field(
        default=60.0,
        ge=0,
        description="Refresh the access token this many seconds before it expires.",
    )
    http2: bool = Field(
        default=False,
        description="Use HTTP/2. Requires the 'http2' extra: pip install 'py24so[http2]'.",
    )
    headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Extra headers sent with every API request.",
    )
    proxy: Optional[str] = Field(
        default=None,
        description="Proxy URL, e.g. 'http://user:pass@proxy:8080'.",
    )
    verify_ssl: Union[bool, str] = Field(
        default=True,
        description="Verify TLS certificates. Pass a path to use a custom CA bundle.",
    )
