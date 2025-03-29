"""Integration tests for the invoice endpoint.

NOTE: These tests require API credentials to be set in the .env file or as environment variables.
"""

import os
import pytest
from datetime import date, timedelta
from dotenv import load_dotenv

from py24so import Client24SO
from py24so.models.config import ClientOptions
from py24so.models.customer import CustomerCreate, Address, Contact
from py24so.models.product import ProductCreate, PriceInfo
from py24so.models.invoice import InvoiceCreate, InvoiceUpdate, InvoiceLineItem, InvoiceStatus

# Load environment variables from .env file
load_dotenv()

# Skip all tests if credentials are not set
pytestmark = pytest.mark.skipif(
    not all([
        os.environ.get("CLIENT_ID"),
        os.environ.get("CLIENT_SECRET"),
        os.environ.get("ORGANIZATION_ID")
    ]),
    reason="API credentials not set. Set CLIENT_ID, CLIENT_SECRET, and ORGANIZATION_ID environment variables."
)


@pytest.fixture
def client():
    """Create a 24SevenOffice API client."""
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    organization_id = os.environ.get("ORGANIZATION_ID")
    
    options = ClientOptions(
        cache_enabled=False,  # Disable caching for testing
        rate_limit_rate=30,  # 30 requests per minute
    )
    
    with Client24SO(
        client_id=client_id,
        client_secret=client_secret,
        organization_id=organization_id,
        options=options,
    ) as client:
        yield client


@pytest.fixture
def test_customer(client):
    """Create a test customer for invoice testing."""
    # Create a unique customer name to avoid conflicts
    unique_suffix = os.urandom(4).hex()
    customer_data = CustomerCreate(
        name=f"Integration Test Customer {unique_suffix}",
        email=f"test{unique_suffix}@example.com",
        phone="123-456-7890",
        addresses=[
            Address(
                street="Test Street 123",
                city="Oslo",
                postal_code="0150",
                country="Norway",
                type="Billing"
            )
        ],
        contacts=[
            Contact(
                first_name="Test",
                last_name="Person",
                email=f"contact{unique_suffix}@example.com",
                phone="987-654-3210"
            )
        ]
    )
    
    # Create the customer
    customer = client.customers.create(customer_data)
    
    yield customer
    
    # Cleanup (delete the customer)
    try:
        client.customers.delete(customer.id)
    except Exception:
        pass


@pytest.fixture
def test_product(client):
    """Create a test product for invoice testing."""
    # Create a unique product name to avoid conflicts
    unique_suffix = os.urandom(4).hex()
    product_data = ProductCreate(
        name=f"Integration Test Product {unique_suffix}",
        description="Product for invoice testing",
        sku=f"INVTEST-{unique_suffix}",
        price_info=PriceInfo(
            price=299.99,
            currency="NOK",
            vat_rate=25.0,
            unit="pcs"
        ),
        is_service=False,
        is_active=True
    )
    
    # Create the product
    product = client.products.create(product_data)
    
    yield product
    
    # Cleanup (delete the product)
    try:
        client.products.delete(product.id)
    except Exception:
        pass


@pytest.fixture
def test_invoice_data(test_customer, test_product):
    """Invoice data for testing."""
    return InvoiceCreate(
        customer_id=test_customer.id,
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        line_items=[
            InvoiceLineItem(
                description=test_product.name,
                quantity=2,
                unit_price=test_product.price_info.price,
                vat_rate=test_product.price_info.vat_rate,
                product_id=test_product.id,
                unit=test_product.price_info.unit
            )
        ],
        currency="NOK",
        notes="Integration test invoice",
        payment_terms=30
    )


def test_invoice_crud(client, test_invoice_data):
    """Test basic CRUD operations on the invoice endpoint."""
    # Create a new invoice
    created_invoice = client.invoices.create(test_invoice_data)
    assert created_invoice.customer_id == test_invoice_data.customer_id
    assert len(created_invoice.line_items) == len(test_invoice_data.line_items)
    assert created_invoice.status == InvoiceStatus.DRAFT
    assert created_invoice.id
    
    # Get the invoice
    invoice_id = created_invoice.id
    fetched_invoice = client.invoices.get(invoice_id)
    assert fetched_invoice.id == invoice_id
    assert fetched_invoice.customer_id == test_invoice_data.customer_id
    
    # Update the invoice
    update_data = InvoiceUpdate(
        notes="Updated integration test invoice",
        reference="TEST-REF-123"
    )
    updated_invoice = client.invoices.update(invoice_id, update_data)
    assert updated_invoice.id == invoice_id
    assert updated_invoice.notes == update_data.notes
    assert updated_invoice.reference == update_data.reference
    
    # Verify update by fetching again
    refetched_invoice = client.invoices.get(invoice_id)
    assert refetched_invoice.notes == update_data.notes
    
    # List invoices and verify our test invoice is in the list
    invoices = client.invoices.list(page=1, page_size=100)
    found = False
    for invoice in invoices:
        if invoice.id == invoice_id:
            found = True
            break
    assert found
    
    # List invoices with filter
    filtered_invoices = client.invoices.list(
        status=InvoiceStatus.DRAFT,
        customer_id=test_invoice_data.customer_id
    )
    assert any(i.id == invoice_id for i in filtered_invoices)
    
    # Send the invoice
    sent_invoice = client.invoices.send(invoice_id)
    assert sent_invoice.status == InvoiceStatus.SENT
    
    # Mark as paid
    paid_invoice = client.invoices.mark_as_paid(
        invoice_id, 
        payment_date=date.today().isoformat()
    )
    assert paid_invoice.status == InvoiceStatus.PAID
    assert paid_invoice.payment_date
    
    # Batch get invoices
    batch_results = client.invoices.batch_get([invoice_id])
    assert invoice_id in batch_results
    assert batch_results[invoice_id].status == InvoiceStatus.PAID
    
    # Create a credit note
    credit_note = client.invoices.create_credit_note(invoice_id)
    assert credit_note.is_credit_note is True
    assert credit_note.credited_invoice_id == invoice_id
    
    # Delete the credit note
    client.invoices.delete(credit_note.id)
    
    # Delete the invoice
    client.invoices.delete(invoice_id)
    
    # Verify invoice is gone (this should raise a NotFoundError)
    with pytest.raises(Exception):
        client.invoices.get(invoice_id) 