"""
Basic usage example for the 24SevenOffice API client.

This example demonstrates how to use the client to interact with the API.
"""

import os
from dotenv import load_dotenv

from py24so import Client24SO, AsyncClient24SO
from py24so.models.config import ClientOptions
from py24so.models.customer import CustomerCreate, Address, Contact
from py24so.models.invoice import InvoiceCreate, InvoiceLineItem
from py24so.models.product import ProductCreate, PriceInfo

# Load environment variables from .env file
load_dotenv()

# Get API credentials from environment variables
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
organization_id = os.getenv("ORGANIZATION_ID")

# Configure client options
options = ClientOptions(
    cache_enabled=True,
    rate_limit_rate=30,  # 30 requests per minute
)


def sync_example():
    """Synchronous API client example."""
    
    # Create client
    with Client24SO(
        client_id=client_id,
        client_secret=client_secret,
        organization_id=organization_id,
        options=options,
    ) as client:
        # Create a new customer
        new_customer = CustomerCreate(
            name="Acme Inc.",
            email="info@acme.com",
            phone="123-456-7890",
            addresses=[
                Address(
                    street="123 Main St",
                    city="Oslo",
                    postal_code="0150",
                    country="Norway",
                    type="Billing",
                ),
            ],
            contacts=[
                Contact(
                    first_name="John",
                    last_name="Doe",
                    email="john.doe@acme.com",
                    phone="123-456-7891",
                ),
            ],
        )
        
        customer = client.customers.create(new_customer)
        print(f"Created customer: {customer.name} (ID: {customer.id})")
        
        # Create a new product
        new_product = ProductCreate(
            name="Widget Pro",
            description="Professional grade widget",
            price_info=PriceInfo(
                price=99.99,
                vat_rate=25.0,
                unit="pcs",
            ),
        )
        
        product = client.products.create(new_product)
        print(f"Created product: {product.name} (ID: {product.id})")
        
        # Create an invoice for the customer
        new_invoice = InvoiceCreate(
            customer_id=customer.id,
            line_items=[
                InvoiceLineItem(
                    description=product.name,
                    quantity=2,
                    unit_price=product.price_info.price,
                    vat_rate=product.price_info.vat_rate,
                    product_id=product.id,
                    unit=product.price_info.unit,
                ),
            ],
        )
        
        invoice = client.invoices.create(new_invoice)
        print(f"Created invoice: {invoice.invoice_number} (ID: {invoice.id})")
        
        # Send the invoice to the customer
        sent_invoice = client.invoices.send(invoice.id)
        print(f"Sent invoice {sent_invoice.invoice_number} to {customer.name}")
        
        # Fetch a list of customers
        customers = client.customers.list(page=1, page_size=10)
        print(f"Found {len(customers)} customers")
        
        # Fetch a list of products
        products = client.products.list(page=1, page_size=10)
        print(f"Found {len(products)} products")
        
        # Fetch a list of invoices
        invoices = client.invoices.list(page=1, page_size=10)
        print(f"Found {len(invoices)} invoices")


async def async_example():
    """Asynchronous API client example."""
    import asyncio
    
    # Create client
    async with AsyncClient24SO(
        client_id=client_id,
        client_secret=client_secret,
        organization_id=organization_id,
        options=options,
    ) as client:
        # Fetch a list of customers
        customers = await client.customers.list(page=1, page_size=10)
        print(f"[Async] Found {len(customers)} customers")
        
        # Fetch a list of products
        products = await client.products.list(page=1, page_size=10)
        print(f"[Async] Found {len(products)} products")
        
        # Fetch a list of invoices
        invoices = await client.invoices.list(page=1, page_size=10)
        print(f"[Async] Found {len(invoices)} invoices")
        
        # Fetch multiple resources concurrently
        customer_task = client.customers.get(customers[0].id if customers else "123")
        product_task = client.products.get(products[0].id if products else "456")
        invoice_task = client.invoices.get(invoices[0].id if invoices else "789")
        
        # Wait for all tasks to complete
        results = await asyncio.gather(
            customer_task, 
            product_task, 
            invoice_task,
            return_exceptions=True,
        )
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                print(f"[Async] Error: {result}")
            else:
                print(f"[Async] Retrieved: {result}")


if __name__ == "__main__":
    # Run synchronous example
    print("\n=== Running synchronous example ===\n")
    sync_example()
    
    # Run asynchronous example
    print("\n=== Running asynchronous example ===\n")
    import asyncio
    asyncio.run(async_example()) 