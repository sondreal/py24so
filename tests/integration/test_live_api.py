"""Tests against the real 24SevenOffice API.

Skipped unless credentials are configured::

    export PY24SO_CLIENT_ID=...
    export PY24SO_CLIENT_SECRET=...
    export PY24SO_ORGANIZATION_ID=...
    pytest tests/integration

Only read-only endpoints are called by default. Tests that create (and then
delete) data additionally require ``PY24SO_ALLOW_WRITES=1``; only point them at a
test/demo organization.
"""

import os
import uuid

import pytest

from py24so import AsyncClient24SO, Client24SO, NotFoundError
from py24so import models as m

pytestmark = pytest.mark.skipif(
    not all(
        os.environ.get(var)
        for var in ("PY24SO_CLIENT_ID", "PY24SO_CLIENT_SECRET", "PY24SO_ORGANIZATION_ID")
    ),
    reason="PY24SO_CLIENT_ID / PY24SO_CLIENT_SECRET / PY24SO_ORGANIZATION_ID not set",
)
writes = pytest.mark.skipif(
    os.environ.get("PY24SO_ALLOW_WRITES") != "1", reason="set PY24SO_ALLOW_WRITES=1 to run"
)


@pytest.fixture(scope="module")
def client() -> Client24SO:
    with Client24SO() as c:
        yield c


def test_authentication_and_organization(client: Client24SO) -> None:
    assert client.get_access_token()
    organization = client.organization.get()
    assert organization.id is not None


def test_reference_data(client: Client24SO) -> None:
    assert all(isinstance(t, m.Tax) for t in client.taxes.list())
    assert all(isinstance(c, m.Currency) for c in client.currencies.list())
    assert all(isinstance(t, m.TransactionType) for t in client.transaction_types.list())
    assert all(isinstance(a, m.Account) for a in client.accounts.list())


def test_paginated_lists(client: Client24SO) -> None:
    for paginator in (
        client.customers.list(page_size=5),
        client.products.list(page_size=5),
        client.sales_orders.list(page_size=5),
        client.product_categories.list(),
    ):
        items = paginator.to_list(max_items=12)  # crosses page boundaries
        assert len(items) <= 12


def test_not_found(client: Client24SO) -> None:
    with pytest.raises(NotFoundError) as info:
        client.customers.get(2_000_000_000)
    assert info.value.status_code == 404


async def test_async_client() -> None:
    async with AsyncClient24SO() as client:
        taxes = await client.taxes.list()
        customers = await client.customers.list(page_size=2).to_list(max_items=3)
    assert isinstance(taxes, list) and isinstance(customers, list)


@writes
def test_product_category_round_trip(client: Client24SO) -> None:
    name = f"py24so-test-{uuid.uuid4().hex[:8]}"
    category = client.product_categories.create(m.ProductCategoryCreate(name=name, parent_id=0))
    assert category.id is not None
    try:
        updated = client.product_categories.update(category.id, {"name": name + "-renamed"})
        assert updated.name == name + "-renamed"
        assert client.product_categories.get(category.id).name == name + "-renamed"
    finally:
        client.product_categories.delete(category.id)


@writes
def test_customer_round_trip(client: Client24SO) -> None:
    customer = client.customers.create(
        m.CustomerCreate(
            is_company=False,
            person=m.CustomerPerson(first_name="Py24so", last_name=uuid.uuid4().hex[:8]),
            note="Created by py24so integration tests",
        )
    )
    assert customer.id is not None
    try:
        updated = client.customers.update(customer.id, m.CustomerUpdate(phone="12345678"))
        assert updated.phone == "12345678"
    finally:
        client.customers.delete(customer.id)
