from typing import Dict, Optional, Union

from pydantic import BaseModel, Field, HttpUrl


class ClientOptions(BaseModel):
    """Configuration options for the 24SevenOffice API client."""

    base_url: HttpUrl = Field(
        default="https://rest.api.24sevenoffice.com/v1",
        description="Base URL for the 24SevenOffice API",
    )
    timeout: float = Field(
        default=30.0,
        description="Request timeout in seconds",
        ge=0.1,
    )
    cache_enabled: bool = Field(
        default=True,
        description="Enable HTTP response caching",
    )
    cache_ttl: int = Field(
        default=300,
        description="Cache TTL in seconds",
        ge=1,
    )
    cache_max_size: int = Field(
        default=100,
        description="Maximum number of responses to cache",
        ge=1,
    )
    rate_limit_rate: int = Field(
        default=100,
        description="Maximum number of requests per minute",
        ge=1,
    )
    http2: bool = Field(
        default=False,
        description="Use HTTP/2 protocol",
    )
    headers: Dict[str, str] = Field(
        default_factory=lambda: {
            "User-Agent": "py24so - Python 24SevenOffice API Client",
            "Accept": "application/json",
        },
        description="Default headers to include in all requests",
    )
    proxies: Optional[Dict[str, str]] = Field(
        default=None,
        description="HTTP proxies to use for requests",
    )
    verify_ssl: Union[bool, str] = Field(
        default=True,
        description="Verify SSL certificates",
    ) 