from typing import Any, Dict, List

import httpx
import pytest

from py24so import APIConnectionError, Page
from py24so import models as m
from tests.conftest import FakeAPI, json_response


def customers(*ids: int) -> List[Dict[str, Any]]:
    return [{"id": i, "name": f"Customer {i}"} for i in ids]


def link(url: str, rel: str = "next") -> Dict[str, str]:
    return {"Link": f'<{url}>; rel="{rel}"'}


def test_follows_link_header_across_pages(api: FakeAPI, client: Any) -> None:
    api.add(
        "GET",
        "/customers",
        json_response(customers(1, 2), headers=link("/v1/customers?limit=2&page=2")),
        json_response(
            customers(3, 4),
            headers=link("https://rest.api.24sevenoffice.com/v1/customers?limit=2&page=3"),
        ),
        json_response(customers(5)),
    )
    result = client.customers.list(page_size=2, is_company=True).to_list()
    assert [c.id for c in result] == [1, 2, 3, 4, 5]
    assert [dict(r.url.params) for r in api.requests] == [
        {"limit": "2", "isCompany": "true"},
        {"limit": "2", "page": "2"},
        {"limit": "2", "page": "3"},
    ]


def test_link_header_with_multiple_relations(api: FakeAPI, client: Any) -> None:
    api.add(
        "GET",
        "/salesorders",
        json_response(
            [{"id": 1}],
            headers={
                "Link": '</v1/salesorders?limit=1>; rel="first", '
                '</v1/salesorders?limit=1&continuationToken=abc%3D>; rel="next"'
            },
        ),
        json_response([{"id": 2}]),
    )
    assert [o.id for o in client.sales_orders.list(page_size=1)] == [1, 2]
    assert dict(api.last.url.params) == {"limit": "1", "continuationToken": "abc="}


def test_iteration_is_lazy(api: FakeAPI, client: Any) -> None:
    api.add(
        "GET",
        "/customers",
        json_response(customers(1, 2), headers=link("/v1/customers?page=2")),
        json_response(customers(3, 4)),
    )
    iterator = iter(client.customers.list())
    assert next(iterator).id == 1
    assert len(api.requests) == 1


def test_to_list_max_items_stops_early(api: FakeAPI, client: Any) -> None:
    api.add(
        "GET",
        "/customers",
        json_response(customers(1, 2), headers=link("/v1/customers?page=2")),
        json_response(customers(3, 4), headers=link("/v1/customers?page=3")),
    )
    assert [c.id for c in client.customers.list().to_list(max_items=3)] == [1, 2, 3]
    assert len(api.requests) == 2
    assert client.customers.list().to_list(max_items=0) == []


def test_first_page_and_pages(api: FakeAPI, client: Any) -> None:
    api.add(
        "GET",
        "/customers",
        json_response(customers(1, 2), headers=link("/v1/customers?page=2")),
        json_response(customers(3)),
    )
    page = client.customers.list().first_page()
    assert isinstance(page, Page)
    assert [c.id for c in page] == [1, 2] and len(page) == 2
    assert page.has_next and page.next_url == "/v1/customers?page=2"
    assert isinstance(page.items[0], m.Customer)


def test_refuses_to_follow_links_to_other_hosts(api: FakeAPI, client: Any) -> None:
    api.add(
        "GET",
        "/customers",
        json_response(customers(1), headers=link("https://evil.example/steal")),
    )
    with pytest.raises(APIConnectionError, match="foreign URL"):
        client.customers.list().to_list()
    assert all(r.url.host == "rest.api.24sevenoffice.com" for r in api.requests)


def test_stops_on_link_loop(api: FakeAPI, client: Any) -> None:
    api.add(
        "GET",
        "/customers",
        json_response(customers(1), headers=link("/v1/customers?page=2")),
        json_response(customers(2), headers=link("/v1/customers?page=2")),
    )
    assert [c.id for c in client.customers.list()] == [1, 2]
    assert len(api.requests) == 2


def test_stops_on_repeated_empty_pages(api: FakeAPI, client: Any) -> None:
    api.add("GET", "/customers", json_response([], headers=link("/v1/customers?page=2")))
    assert client.customers.list().to_list() == []
    assert len(api.requests) == 2  # the identical second page stops the loop


def test_page_number_fallback_without_link_header(api: FakeAPI, client: Any) -> None:
    api.add(
        "GET",
        "/products",
        json_response([{"id": 1}, {"id": 2}]),
        json_response([{"id": 3}, {"id": 4}]),
        json_response([{"id": 5}]),
    )
    assert [p.id for p in client.products.list(page_size=2)] == [1, 2, 3, 4, 5]
    assert [r.url.params.get("page") for r in api.requests] == [None, "2", "3"]


def test_page_number_fallback_stops_if_api_ignores_page(api: FakeAPI, client: Any) -> None:
    api.add("GET", "/products", json_response([{"id": 1}, {"id": 2}]))
    assert [p.id for p in client.products.list(page_size=2)] == [1, 2]
    assert len(api.requests) == 2


def test_page_number_fallback_starts_at_start_page(api: FakeAPI, client: Any) -> None:
    api.add("GET", "/products", json_response([{"id": 1}]), json_response([]))
    client.products.list(page_size=1, start_page=5).to_list()
    assert [r.url.params["page"] for r in api.requests] == ["5", "6"]


def test_malformed_link_header_is_ignored(api: FakeAPI, client: Any) -> None:
    api.add("GET", "/customers", json_response(customers(1), headers={"Link": "garbage"}))
    assert [c.id for c in client.customers.list()] == [1]


async def test_async_pagination(api: FakeAPI, aclient: Any) -> None:
    def two_pages() -> None:
        api.routes.clear()
        api.add(
            "GET",
            "/customers",
            json_response(customers(1, 2), headers=link("/v1/customers?page=2")),
            json_response(customers(3)),
        )

    two_pages()
    assert [c.id async for c in aclient.customers.list()] == [1, 2, 3]

    two_pages()
    assert (await aclient.customers.list().first_page()).has_next

    two_pages()
    assert [len(page) async for page in aclient.customers.list().pages()] == [2, 1]

    two_pages()
    assert [c.id for c in await aclient.customers.list().to_list(max_items=1)] == [1]


def test_list_endpoint_accepts_enveloped_responses(api: FakeAPI, client: Any) -> None:
    api.add("GET", "/taxes", json_response({"items": [{"id": 1}]}))
    assert client.taxes.list()[0].id == 1


def test_link_resolution(client: Any) -> None:
    resolve = client._client.resolve_link
    base = "https://rest.api.24sevenoffice.com/v1"
    assert resolve("/v1/customers?page=2") == f"{base}/customers?page=2"
    assert resolve("customers?page=2") == f"{base}/customers?page=2"
    assert resolve(f"{base}/customers?page=2") == f"{base}/customers?page=2"
    for bad in (
        "http://rest.api.24sevenoffice.com/v1/x",
        "https://rest.api.24sevenoffice.com:8443/v1/x",
    ):
        with pytest.raises(APIConnectionError):
            resolve(bad)


def test_paginators_are_reusable(api: FakeAPI, client: Any) -> None:
    api.add("GET", "/productcategories", json_response([{"id": 1}]))
    paginator = client.product_categories.list()
    assert [c.id for c in paginator] == [1]
    assert [c.id for c in paginator] == [1]


def test_http_error_mid_pagination_raises(api: FakeAPI, client: Any) -> None:
    api.add(
        "GET",
        "/customers",
        json_response(customers(1), headers=link("/v1/customers?page=2")),
        httpx.Response(404, json={"error": {"message": "gone"}}),
    )
    from py24so import NotFoundError

    with pytest.raises(NotFoundError, match="gone"):
        client.customers.list().to_list()


def test_relative_links_resolve_against_the_request_url(api: FakeAPI, client: Any) -> None:
    api.add(
        "GET",
        "/dimensions/1/elements",
        json_response(
            [{"dimensionType": 1, "value": "a"}], headers=link("elements?continuationToken=x")
        ),
        json_response([{"dimensionType": 1, "value": "b"}]),
    )
    assert [e.value for e in client.dimensions.elements.list(1)] == ["a", "b"]
    assert api.last.url.path == "/v1/dimensions/1/elements"
    assert dict(api.last.url.params) == {"continuationToken": "x"}


def test_empty_page_with_next_link_is_followed(api: FakeAPI, client: Any) -> None:
    api.add(
        "GET",
        "/salesorders",
        json_response([], headers=link("/v1/salesorders?continuationToken=a")),
        json_response([{"id": 7}]),
    )
    assert [o.id for o in client.sales_orders.list()] == [7]
