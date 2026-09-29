"""The async transport loop is hand-written, so its behaviour is tested separately."""

from typing import Any, List

import httpx
import pytest

from py24so import (
    APIConnectionError,
    APITimeoutError,
    AsyncClient24SO,
    AuthenticationError,
    RateLimitError,
    ServerError,
)
from py24so._auth import parse_token_response
from tests.conftest import FAST, TOKEN_URL, FakeAPI, json_response


def make_client(api: FakeAPI, handler: Any = None, **options: Any) -> AsyncClient24SO:
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler or api.handler))
    client = AsyncClient24SO("id", "secret", "1", FAST.model_copy(update=options), http_client=http)
    sleeps: List[float] = []

    async def sleep(seconds: float) -> None:
        sleeps.append(seconds)

    client._client._sleep = sleep  # type: ignore[method-assign]
    client.sleeps = sleeps  # type: ignore[attr-defined]
    return client


def failing(
    api: FakeAPI, exc: Exception, times: int, host: str = "rest.api.24sevenoffice.com"
) -> Any:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == host and calls["n"] < times:
            calls["n"] += 1
            raise exc
        return api.handler(request)

    return handler


async def test_401_refreshes_token(api: FakeAPI) -> None:
    api.add("GET", "/taxes", json_response({}, 401), json_response([{"id": 1}]))
    client = make_client(api)
    assert (await client.taxes.list())[0].id == 1
    assert [r.headers["authorization"] for r in api.requests] == [
        "Bearer token-1",
        "Bearer token-2",
    ]
    assert await client.get_access_token() == "token-2"


async def test_retries_then_succeeds_with_retry_after(api: FakeAPI) -> None:
    api.add(
        "GET",
        "/taxes",
        httpx.Response(429, headers={"Retry-After": "3"}),
        httpx.Response(503),
        json_response([]),
    )
    client = make_client(api, max_retries=2, retry_backoff=1.0, max_retry_delay=10)
    assert await client.taxes.list() == []
    assert client.sleeps[0] == 3.0  # type: ignore[attr-defined]
    assert 1.5 <= client.sleeps[1] <= 2.0  # type: ignore[attr-defined]


async def test_rate_limit_error_after_retries(api: FakeAPI) -> None:
    api.add("POST", "/salesorders", httpx.Response(429))
    client = make_client(api, max_retries=1)
    with pytest.raises(RateLimitError):
        await client.sales_orders.create({"customer": {"id": 1}})
    assert len(api.requests) == 2


async def test_post_not_retried_on_500(api: FakeAPI) -> None:
    api.add("POST", "/salesorders", httpx.Response(500))
    client = make_client(api, max_retries=3)
    with pytest.raises(ServerError):
        await client.sales_orders.create({"customer": {"id": 1}})
    assert len(api.requests) == 1


async def test_connect_errors_retried_then_raised(api: FakeAPI) -> None:
    api.add("POST", "/salesorders", json_response({"id": 1}))
    client = make_client(api, failing(api, httpx.ConnectError("refused"), 1))
    assert (await client.sales_orders.create({"customer": {"id": 1}})).id == 1

    client = make_client(api, failing(api, httpx.ConnectError("refused"), 99), max_retries=1)
    with pytest.raises(APIConnectionError):
        await client.taxes.list()


async def test_read_timeout_not_retried_for_post(api: FakeAPI) -> None:
    client = make_client(api, failing(api, httpx.ReadTimeout("slow"), 1))
    with pytest.raises(APITimeoutError):
        await client.sales_orders.create({"customer": {"id": 1}})


async def test_token_errors(api: FakeAPI) -> None:
    api.token_responses = [json_response({"error": "access_denied"}, 401)]
    client = make_client(api)
    with pytest.raises(AuthenticationError, match="access_denied"):
        await client.taxes.list()

    api.token_responses = [httpx.Response(500)] * 3
    client = make_client(api, max_retries=2)
    with pytest.raises(ServerError):
        await client.taxes.list()


async def test_token_endpoint_unreachable(api: FakeAPI) -> None:
    client = make_client(
        api,
        failing(api, httpx.ConnectError("dns"), 99, host="login.24sevenoffice.com"),
        max_retries=1,
    )
    with pytest.raises(APIConnectionError, match="dns"):
        await client.taxes.list()


async def test_raw_request(api: FakeAPI) -> None:
    api.add("DELETE", "/products/1", httpx.Response(204))
    client = make_client(api)
    assert await client.request("DELETE", "/products/1") is None


async def test_file_upload_with_retry_and_no_token(api: FakeAPI) -> None:
    uploads: List[httpx.Request] = []
    attempts = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "upload.example":
            uploads.append(request)
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise httpx.ConnectError("blip")
            return httpx.Response(503) if attempts["n"] == 2 else httpx.Response(200)
        return api.handler(request)

    api.add(
        "POST",
        "/fileUpload",
        json_response(
            {"uploadMethod": "PUT", "uploadUrl": "https://upload.example/f", "fileId": "f"}
        ),
    )
    api.add("GET", "/fileUpload/f", json_response({"fileId": "f", "status": "Pending"}))
    client = make_client(api, handler, max_retries=2)
    status = await client.files.upload(b"x", content_type="image/png")
    assert status.status == "Pending"
    assert all("authorization" not in r.headers for r in uploads)


async def test_file_upload_failure_and_wait_timeout(api: FakeAPI) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "upload.example":
            return httpx.Response(403, text="signature expired")
        return api.handler(request)

    api.add(
        "POST",
        "/fileUpload",
        json_response(
            {"uploadMethod": "PUT", "uploadUrl": "https://upload.example/f", "fileId": "f"}
        ),
    )
    client = make_client(api, handler)
    from py24so import PermissionDeniedError

    with pytest.raises(PermissionDeniedError, match="signature expired"):
        await client.files.upload(b"x", content_type="image/png")

    api.add("GET", "/fileUpload/f", json_response({"fileId": "f", "status": "Pending"}))
    with pytest.raises(APITimeoutError, match="not processed"):
        await client.files.wait_until_processed("f", timeout=0.0, poll_interval=1.0)


async def test_upload_requires_upload_url(api: FakeAPI) -> None:
    api.add("POST", "/fileUpload", json_response({"fileId": "f"}))
    client = make_client(api)
    with pytest.raises(ValueError, match="upload URL"):
        await client.files.upload(b"x", content_type="image/png")


async def test_owned_client_closes() -> None:
    client = AsyncClient24SO("id", "secret", "1")
    await client.close()
    assert client._client._http.is_closed


@pytest.mark.parametrize(
    "response, message",
    [
        (httpx.Response(200, text="not json"), "HTTP 200"),
        (httpx.Response(200, json={"token_type": "Bearer"}), "did not contain an access_token"),
        (httpx.Response(400, json={"message": "bad audience"}), "bad audience"),
    ],
)
def test_parse_token_response_errors(response: httpx.Response, message: str) -> None:
    response.request = httpx.Request("POST", TOKEN_URL)
    with pytest.raises(AuthenticationError, match=message):
        parse_token_response(response)


def test_parse_token_response_defaults() -> None:
    response = httpx.Response(
        200, json={"access_token": "s3cr3t-jwt", "expires_in": "oops", "token_type": "bearer"}
    )
    response.request = httpx.Request("POST", TOKEN_URL)
    token = parse_token_response(response)
    assert token.authorization == "Bearer s3cr3t-jwt"
    assert not token.is_expired(margin=60)  # unparseable expires_in falls back to 1 hour
    assert "s3cr3t-jwt" not in repr(token)
