from py24so._client import AsyncAPIClient


class AsyncResource:
    """Base class for API resources; holds the low-level client."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client

    def __repr__(self) -> str:
        return f"<{type(self).__name__}>"
