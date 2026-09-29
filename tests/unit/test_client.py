import json
import threading
import time
from typing import Any, List

import httpx
import pytest

import py24so
from py24so import (
    APIConnectionError,
    APIResponseValidationError,
    APITimeoutError,
    AsyncClient24SO,
    AuthenticationError,
    BadRequestError,
    Client24SO,
    ClientOptions,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from tests.conftest import FAST, TOKEN_URL, FakeAPI, json_response


def make_client(api: FakeAPI, **options: Any) -> Client24SO:
    opts = FAST.model_copy(update=options)
    http = httpx.Client(transport=httpx.MockTransport(api.handler))
    client = Client24SO("client-id", "client-secret", "12345", opts, http_client=http)
    client._client._sleep = lambda seconds: None  # type: ignore[method-assign]
    return client


# --- construction ---------------------------------------------------------------


def test_credentials_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PY24SO_CLIENT_ID", "env-id")
    monkeypatch.setenv("PY24SO_CLIENT_SECRET", "env-secret")
    monkeypatch.setenv("PY24SO_ORGANIZATION_ID", "999")
    with Client24SO() as client:
        assert client.organization_id == "999"
        assert client._client.client_id == "env-id"


def test_missing_credentials_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("PY24SO_CLIENT_ID", "PY24SO_CLIENT_SECRET", "PY24SO_ORGANIZATION_ID"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(ValueError, match="client_secret is required"):
        Client24SO("id", "  ", "1")


def test_secret_not_in_repr() -> None:
    with Client24SO("id", "super-secret", "1") as client:
        assert "super-secret" not in repr(client)
        assert "super-secret" not in repr(client._client)


def test_options_are_validated() -> None:
    with pytest.raises(Exception):
        ClientOptions(timeout=0)
    with pytest.raises(Exception):
        ClientOptions(cache_enabled=True)  # type: ignore[call-arg]  # removed option
    with pytest.raises(ValueError, match="Invalid base_url"):
        Client24SO("id", "secret", "1", ClientOptions(base_url="not a url"))


def test_async_client_constructs_without_running_loop() -> None:
    client = AsyncClient24SO("id", "secret", "1")
    assert client.organization_id == "1"


def test_version_is_exposed() -> None:
    assert py24so.__version__.count(".") == 2


# --- authentication ----------------------------------------------------------------


def test_token_request_follows_documented_flow(api: FakeAPI) -> None:
    api.add("GET", "/taxes", json_response([]))
    client = make_client(api)
    client.taxes.list()

    token_request = api.token_requests[0]
    assert str(token_request.url) == TOKEN_URL
    assert token_request.method == "POST"
    assert json.loads(token_request.content) == {
        "grant_type": "client_credentials",
        "client_id": "client-id",
        "client_secret": "client-secret",
        "audience": "https://api.24sevenoffice.com",
        "login_organization": "12345",
    }
    assert "authorization" not in token_request.headers
    assert api.last.headers["authorization"] == "Bearer token-1"


def test_token_is_cached_and_refreshed_before_expiry(api: FakeAPI) -> None:
    api.add("GET", "/taxes", json_response([]))
    api.token_responses = [
        json_response({"access_token": "short", "expires_in": 30}),  # inside refresh margin
        json_response({"access_token": "long", "expires_in": 3600}),
    ]
    client = make_client(api)
    client.taxes.list()
    client.taxes.list()
    client.taxes.list()
    assert [r.headers["authorization"] for r in api.requests] == [
        "Bearer short",
        "Bearer long",
        "Bearer long",
    ]
    assert len(api.token_requests) == 2


def test_401_refreshes_token_once_and_retries(api: FakeAPI) -> None:
    api.add(
        "GET",
        "/taxes",
        json_response({"error": {"name": "Unauthorized"}}, 401),
        json_response([{"id": 1}]),
    )
    client = make_client(api)
    assert client.taxes.list()[0].id == 1
    assert [r.headers["authorization"] for r in api.requests] == [
        "Bearer token-1",
        "Bearer token-2",
    ]


def test_persistent_401_raises(api: FakeAPI) -> None:
    api.add("GET", "/taxes", json_response({"error": {"message": "Invalid token"}}, 401))
    client = make_client(api)
    with pytest.raises(AuthenticationError, match="Invalid token"):
        client.taxes.list()
    assert len(api.requests) == 2  # original + one retry with a fresh token


def test_invalid_credentials_raise_authentication_error(api: FakeAPI) -> None:
    api.token_responses = [
        json_response({"error": "access_denied", "error_description": "Unauthorized"}, 403)
    ]
    client = make_client(api)
    with pytest.raises(AuthenticationError, match="Unauthorized") as info:
        client.taxes.list()
    assert info.value.status_code == 403
    assert api.requests == []


def test_token_endpoint_outage_is_retried(api: FakeAPI) -> None:
    api.add("GET", "/taxes", json_response([]))
    api.token_responses = [httpx.Response(503), httpx.Response(502)]
    client = make_client(api)
    client.taxes.list()
    assert len(api.token_requests) == 3


def test_concurrent_threads_share_one_token_fetch(api: FakeAPI) -> None:
    api.add("GET", "/taxes", json_response([]))
    original = api._token

    def slow_token(request: httpx.Request) -> httpx.Response:
        time.sleep(0.05)
        return original(request)

    api._token = slow_token  # type: ignore[method-assign]
    client = make_client(api)
    threads = [threading.Thread(target=client.taxes.list) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(api.token_requests) == 1
    assert len(api.requests) == 8


async def test_async_concurrent_requests_share_one_token_fetch(api: FakeAPI) -> None:
    import asyncio

    api.add("GET", "/taxes", json_response([]))
    http = httpx.AsyncClient(transport=httpx.MockTransport(api.handler))
    async with AsyncClient24SO("id", "secret", "1", FAST, http_client=http) as client:
        await asyncio.gather(*(client.taxes.list() for _ in range(8)))
    assert len(api.token_requests) == 1


# --- errors ------------------------------------------------------------------------


@pytest.mark.parametrize(
    "status, exc",
    [
        (400, BadRequestError),
        (403, PermissionDeniedError),
        (404, NotFoundError),
        (409, ConflictError),
        (429, RateLimitError),
        (500, ServerError),
    ],
)
def test_status_codes_map_to_exceptions(api: FakeAPI, status: int, exc: type) -> None:
    api.add(
        "POST",
        "/customers",
        json_response(
            {"error": {"name": "SomeError", "message": "Nope"}, "trackingId": "abc123"},
            status,
            headers={"X-Trace-Id": "trace-1"},
        ),
    )
    client = make_client(api, max_retries=0)
    with pytest.raises(exc) as info:
        client.customers.create({"is_company": True, "name": "X"})
    err = info.value
    assert err.status_code == status
    assert err.error_name == "SomeError"
    assert err.tracking_id == "abc123"
    assert err.trace_id == "trace-1"
    assert "Nope" in str(err) and "abc123" in str(err)
    assert isinstance(err, py24so.APIStatusError)


def test_validation_error_exposes_details(api: FakeAPI) -> None:
    api.add(
        "POST",
        "/customers",
        json_response(
            {
                "error": {
                    "name": "ValidationError",
                    "message": "Invalid request",
                    "payload": {
                        "validationErrors": [{"path": "customer.name", "keyword": "required"}]
                    },
                },
                "trackingId": "def456",
            },
            400,
        ),
    )
    client = make_client(api)
    with pytest.raises(ValidationError) as info:
        client.customers.create({"isCompany": True, "name": "X"})
    assert info.value.validation_errors == [{"path": "customer.name", "keyword": "required"}]
    assert "customer.name (required)" in str(info.value)
    assert isinstance(info.value, BadRequestError)


def test_bad_request_errors_payload(api: FakeAPI) -> None:
    api.add(
        "PATCH",
        "/salesorders/1",
        json_response(
            {
                "error": {
                    "name": "BadRequestError",
                    "payload": {
                        "errors": [{"type": "NoLines", "message": "No lines in the sales order"}]
                    },
                }
            },
            400,
        ),
    )
    client = make_client(api)
    with pytest.raises(BadRequestError, match="No lines in the sales order") as info:
        client.sales_orders.invoice(1)
    assert info.value.errors[0]["type"] == "NoLines"
    assert not isinstance(info.value, ValidationError)


def test_non_json_error_body(api: FakeAPI) -> None:
    api.add("GET", "/taxes", httpx.Response(502, text="<html>Bad gateway</html>"))
    client = make_client(api, max_retries=0)
    with pytest.raises(ServerError, match="Bad gateway"):
        client.taxes.list()


def test_invalid_json_success_body(api: FakeAPI) -> None:
    api.add("GET", "/taxes/1", httpx.Response(200, text="not json"))
    client = make_client(api)
    with pytest.raises(APIResponseValidationError) as info:
        client.taxes.get(1)
    assert info.value.body == "not json"


def test_unexpected_response_shape_keeps_body(api: FakeAPI) -> None:
    api.add("GET", "/taxes/1", json_response(["not", "an", "object"]))
    client = make_client(api)
    with pytest.raises(APIResponseValidationError) as info:
        client.taxes.get(1)
    assert info.value.body == ["not", "an", "object"]


def test_empty_body_where_model_expected(api: FakeAPI) -> None:
    api.add("GET", "/taxes/1", httpx.Response(200))
    client = make_client(api)
    with pytest.raises(APIResponseValidationError, match="body was empty"):
        client.taxes.get(1)


# --- retries -----------------------------------------------------------------------


def test_get_is_retried_on_server_errors(api: FakeAPI) -> None:
    api.add("GET", "/taxes", httpx.Response(500), httpx.Response(502), json_response([{"id": 1}]))
    client = make_client(api, max_retries=2)
    assert client.taxes.list()[0].id == 1
    assert len(api.requests) == 3


def test_retries_are_bounded(api: FakeAPI) -> None:
    api.add("GET", "/taxes", httpx.Response(503))
    client = make_client(api, max_retries=2)
    with pytest.raises(ServerError):
        client.taxes.list()
    assert len(api.requests) == 3


@pytest.mark.parametrize("status", [500, 502, 504])
def test_post_is_not_retried_when_it_may_have_been_processed(api: FakeAPI, status: int) -> None:
    api.add("POST", "/salesorders", httpx.Response(status))
    client = make_client(api, max_retries=3)
    with pytest.raises(ServerError):
        client.sales_orders.create({"customer": {"id": 1}})
    assert len(api.requests) == 1


def test_post_is_retried_on_429_honoring_retry_after(api: FakeAPI) -> None:
    api.add(
        "POST",
        "/salesorders",
        httpx.Response(429, headers={"Retry-After": "7"}),
        json_response({"id": 1}),
    )
    client = make_client(api, max_retries=2, max_retry_delay=30)
    sleeps: List[float] = []
    client._client._sleep = sleeps.append  # type: ignore[method-assign]
    assert client.sales_orders.create({"customer": {"id": 1}}).id == 1
    assert sleeps == [7.0]


def test_retry_after_is_capped(api: FakeAPI) -> None:
    api.add(
        "GET", "/taxes", httpx.Response(429, headers={"Retry-After": "3600"}), json_response([])
    )
    client = make_client(api, max_retry_delay=5)
    sleeps: List[float] = []
    client._client._sleep = sleeps.append  # type: ignore[method-assign]
    client.taxes.list()
    assert sleeps == [5.0]


def test_rate_limit_error_after_retries(api: FakeAPI) -> None:
    api.add("GET", "/taxes", httpx.Response(429, headers={"Retry-After": "2"}))
    client = make_client(api, max_retries=1)
    with pytest.raises(RateLimitError) as info:
        client.taxes.list()
    assert info.value.retry_after == 2.0


def test_exponential_backoff_with_jitter(api: FakeAPI) -> None:
    api.add("GET", "/taxes", httpx.Response(503))
    client = make_client(api, max_retries=3, retry_backoff=1.0, max_retry_delay=100)
    sleeps: List[float] = []
    client._client._sleep = sleeps.append  # type: ignore[method-assign]
    with pytest.raises(ServerError):
        client.taxes.list()
    assert len(sleeps) == 3
    for attempt, delay in enumerate(sleeps):
        assert 0.75 * 2**attempt <= delay <= 2**attempt


def _failing_transport(api: FakeAPI, exc: Exception, times: int) -> httpx.MockTransport:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) != TOKEN_URL and calls["n"] < times:
            calls["n"] += 1
            raise exc
        return api.handler(request)

    return httpx.MockTransport(handler)


def _client_with_transport(transport: httpx.MockTransport, **options: Any) -> Client24SO:
    http = httpx.Client(transport=transport)
    client = Client24SO("id", "secret", "1", FAST.model_copy(update=options), http_client=http)
    client._client._sleep = lambda seconds: None  # type: ignore[method-assign]
    return client


def test_connect_error_is_retried_even_for_post(api: FakeAPI) -> None:
    api.add("POST", "/salesorders", json_response({"id": 1}))
    client = _client_with_transport(_failing_transport(api, httpx.ConnectError("refused"), 1))
    assert client.sales_orders.create({"customer": {"id": 1}}).id == 1


def test_read_timeout_is_not_retried_for_post(api: FakeAPI) -> None:
    api.add("POST", "/salesorders", json_response({"id": 1}))
    client = _client_with_transport(_failing_transport(api, httpx.ReadTimeout("slow"), 1))
    with pytest.raises(APITimeoutError):
        client.sales_orders.create({"customer": {"id": 1}})
    assert api.requests == []


def test_read_timeout_is_retried_for_get(api: FakeAPI) -> None:
    api.add("GET", "/taxes", json_response([]))
    client = _client_with_transport(_failing_transport(api, httpx.ReadTimeout("slow"), 2))
    assert client.taxes.list() == []


def test_connection_error_after_retries(api: FakeAPI) -> None:
    client = _client_with_transport(
        _failing_transport(api, httpx.ConnectError("refused"), 99), max_retries=1
    )
    with pytest.raises(APIConnectionError, match="refused") as info:
        client.taxes.list()
    assert not isinstance(info.value, APITimeoutError)


# --- request details ---------------------------------------------------------------


def test_path_parameters_cannot_escape_their_segment(api: FakeAPI) -> None:
    # The fake router matches on the decoded path; the raw path is what goes on the wire.
    api.add("GET", "/customers/../salesorders?limit=1", json_response({"id": 1}))
    client = make_client(api)
    client.customers.get("../salesorders?limit=1")
    assert api.last.url.raw_path == b"/v1/customers/..%2Fsalesorders%3Flimit%3D1"
    assert api.last.url.query == b""


def test_raw_paths_cannot_leave_the_api_host(api: FakeAPI) -> None:
    client = make_client(api)
    for url in ("https://evil.example/x", "http://rest.api.24sevenoffice.com/v1/x"):
        with pytest.raises(APIConnectionError, match="foreign URL"):
            client.request("GET", url)
    assert api.requests == []
    # Scheme-relative tricks resolve onto the API host, never elsewhere.
    for path in ("https:/evil.example/x", "//evil.example/x"):
        with pytest.raises(NotFoundError):
            client.request("GET", path)
    assert {r.url.host for r in api.requests} == {"rest.api.24sevenoffice.com"}


@pytest.mark.parametrize("bad", ["", "   ", None, True, ".", ".."])
def test_invalid_path_parameters_are_rejected(api: FakeAPI, bad: Any) -> None:
    client = make_client(api)
    with pytest.raises((ValueError, TypeError)):
        client.customers.get(bad)


def test_default_headers(api: FakeAPI) -> None:
    api.add("GET", "/taxes", json_response([]))
    client = make_client(api, headers={"X-Custom": "yes"})
    client.taxes.list()
    headers = api.last.headers
    assert headers["user-agent"].startswith(f"py24so/{py24so.__version__} ")
    assert headers["accept"] == "application/json"
    assert headers["x-custom"] == "yes"


def test_raw_request_escape_hatch(api: FakeAPI) -> None:
    api.add("GET", "/customers", json_response([{"id": 1, "brandNew": True}]))
    client = make_client(api)
    assert client.request("GET", "/customers", params={"limit": 1}) == [{"id": 1, "brandNew": True}]
    assert dict(api.last.url.params) == {"limit": "1"}


def test_dict_bodies_accept_snake_and_camel_case(api: FakeAPI) -> None:
    api.add("POST", "/customers", json_response({"id": 1}))
    client = make_client(api)
    client.customers.create(
        {
            "is_company": True,
            "name": "A",
            "mobilePhone": "1",
            "organization_number": "9",
            "custom": 1,
        }
    )
    assert api.last_json() == {
        "isCompany": True,
        "name": "A",
        "mobilePhone": "1",
        "organizationNumber": "9",
        "custom": 1,
    }


def test_invalid_request_body_fails_before_sending(api: FakeAPI) -> None:
    import pydantic

    client = make_client(api)
    with pytest.raises(pydantic.ValidationError):
        client.customers.create({"is_company": False})  # a person needs `person`
    with pytest.raises(pydantic.ValidationError):
        client.sales_orders.create({"customer": {"id": 1}, "date": "2024-06-31"})
    assert api.requests == []


def test_client_side_rate_limit(api: FakeAPI) -> None:
    api.add("GET", "/taxes", json_response([]))
    client = make_client(api, rate_limit=60)
    sleeps: List[float] = []
    client._client._sleep = sleeps.append  # type: ignore[method-assign]
    client._client._rate_limiter._tokens = 1.0  # type: ignore[union-attr]
    client.taxes.list()
    client.taxes.list()
    assert sleeps[0] == 0
    assert sleeps[1] == pytest.approx(1.0, abs=0.05)


def test_own_http_client_is_not_closed(api: FakeAPI) -> None:
    http = httpx.Client(transport=httpx.MockTransport(api.handler))
    with Client24SO("id", "secret", "1", http_client=http):
        pass
    assert not http.is_closed
    http.close()


def test_owned_http_client_is_closed() -> None:
    client = Client24SO("id", "secret", "1")
    client.close()
    assert client._client._http.is_closed
    client.close()  # idempotent
