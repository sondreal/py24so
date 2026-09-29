# AUTO-GENERATED from py24so/resources/_async by scripts/unasync.py. DO NOT EDIT.

from py24so._client import APIClient


class Resource:
    """Base class for API resources; holds the low-level client."""

    def __init__(self, client: APIClient) -> None:
        self._client = client

    def __repr__(self) -> str:
        return f"<{type(self).__name__}>"
