import json
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import httpx
import pytest

from py24so import AsyncClient24SO, Client24SO, ClientOptions

TOKEN_URL = "https://login.24sevenoffice.com/oauth/token"
API = "https://rest.api.24sevenoffice.com/v1"

Handler = Callable[[httpx.Request], httpx.Response]
Responder = Union[httpx.Response, Handler, List[Union[httpx.Response, Handler]]]


def json_response(
    data: Any = None, status: int = 200, headers: Optional[Dict[str, str]] = None
) -> httpx.Response:
    if data is None and status == 204:
        return httpx.Response(204, headers=headers)
    return httpx.Response(status, json=data, headers=headers)


class FakeAPI:
    """An in-memory stand-in for the identity provider and the REST API."""

    def __init__(self) -> None:
        self.routes: Dict[Tuple[str, str], List[Responder]] = {}
        self.requests: List[httpx.Request] = []
        self.token_requests: List[httpx.Request] = []
        self.token_responses: List[httpx.Response] = []
        self.token_counter = 0

    def add(self, method: str, path: str, *responses: Responder) -> None:
        """Queue responses for ``METHOD path``. The last one is reused once exhausted."""
        self.routes.setdefault((method.upper(), path), []).extend(responses)

    def _token(self, request: httpx.Request) -> httpx.Response:
        self.token_requests.append(request)
        if self.token_responses:
            return self.token_responses.pop(0)
        self.token_counter += 1
        return json_response(
            {
                "access_token": f"token-{self.token_counter}",
                "expires_in": 3600,
                "token_type": "Bearer",
            }
        )

    def handler(self, request: httpx.Request) -> httpx.Response:
        if str(request.url) == TOKEN_URL:
            return self._token(request)
        self.requests.append(request)
        path = request.url.path
        if path.startswith("/v1"):
            path = path[len("/v1") :]
        key = (request.method, path)
        queue = self.routes.get(key)
        if not queue:
            return json_response(
                {"error": {"name": "NotFoundError", "message": f"no route {key}"}}, 404
            )
        responder = queue.pop(0) if len(queue) > 1 else queue[0]
        return responder(request) if callable(responder) else responder

    @property
    def last(self) -> httpx.Request:
        return self.requests[-1]

    def last_json(self) -> Any:
        return json.loads(self.last.content)


FAST = ClientOptions(retry_backoff=0, max_retry_delay=0)


@pytest.fixture
def api() -> FakeAPI:
    return FakeAPI()


@pytest.fixture
def client(api: FakeAPI) -> Client24SO:
    http = httpx.Client(transport=httpx.MockTransport(api.handler))
    with Client24SO("client-id", "client-secret", "12345", FAST, http_client=http) as c:
        yield c
    http.close()


@pytest.fixture
async def aclient(api: FakeAPI) -> AsyncClient24SO:
    http = httpx.AsyncClient(transport=httpx.MockTransport(api.handler))
    async with AsyncClient24SO("client-id", "client-secret", "12345", FAST, http_client=http) as c:
        yield c
    await http.aclose()
