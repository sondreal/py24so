"""
Basic usage of py24so.

Set your credentials first:

    export PY24SO_CLIENT_ID=...
    export PY24SO_CLIENT_SECRET=...
    export PY24SO_ORGANIZATION_ID=...

    python examples/basic_usage.py            # read-only tour
    python examples/basic_usage.py --invoice  # also creates and invoices a sales order
"""

import asyncio
import logging
import sys

from py24so import AsyncClient24SO, BadRequestError, Client24SO, NotFoundError
from py24so import models as m


def read_only_tour(client: Client24SO) -> None:
    organization = client.organization.get()
    print(f"Connected to {organization.name} (id {organization.id})")

    print("\nVAT codes:")
    for tax in client.taxes.list():
        print(f"  {tax.number:>3}  {tax.rate:>5}%  {tax.name}")

    print("\nFirst 10 companies, sorted by name (pages are fetched as needed):")
    for customer in client.customers.list(is_company=True, sort_by="name:asc").to_list(10):
        print(f"  {customer.id:>8}  {customer.name}")

    print("\nDraft sales orders:")
    for order in client.sales_orders.list(status=m.SalesOrderStatus.DRAFT).to_list(5):
        print(
            f"  #{order.id}  {order.customer.name if order.customer else '?'}  {order.gross_amount}"
        )

    try:
        client.customers.get(2_000_000_000)
    except NotFoundError as err:
        print(f"\nMissing customers raise NotFoundError (tracking id: {err.tracking_id})")


def create_and_invoice(client: Client24SO) -> None:
    customer = client.customers.create(
        m.CustomerCreate(
            is_company=True,
            name="py24so Example AS",
            email=m.CustomerEmail(billing="invoice@example.com"),
        )
    )
    order = client.sales_orders.create(
        m.SalesOrderCreate(customer=m.SalesOrderCustomer(id=customer.id))
    )
    client.sales_orders.lines.create(
        order.id,
        m.SalesOrderLineCreate(
            type=m.LineType.TEXT, description="Consulting", quantity=2, price=1250
        ),
    )
    try:
        invoiced = client.sales_orders.invoice(order.id)
    except BadRequestError as err:
        print(f"Could not invoice: {err} {err.errors}")
        return
    print(f"Sales order {invoiced.id} is now {invoiced.status}")


async def async_example() -> None:
    async with AsyncClient24SO() as client:
        taxes, currencies = await asyncio.gather(client.taxes.list(), client.currencies.list())
        print(f"\n[async] {len(taxes)} VAT codes, {len(currencies)} currencies")
        async for product in client.products.list(page_size=50):
            print(f"[async] first product: {product.name}")
            break


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)  # DEBUG logs every request
    with Client24SO() as client:
        read_only_tour(client)
        if "--invoice" in sys.argv:
            create_and_invoice(client)
    asyncio.run(async_example())
