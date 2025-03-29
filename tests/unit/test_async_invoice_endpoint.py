"""Unit tests for the async invoice endpoint."""

import json
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import httpx
import pytest

from py24so.core.client import AsyncAPIClient
from py24so.endpoints.invoices import AsyncInvoiceEndpoint
from py24so.models.invoice import (
    Invoice, 
    InvoiceCreate, 
    InvoiceUpdate, 
    InvoiceStatus, 
    InvoiceLineItem,
    InvoiceTotals
)


@pytest.fixture
def mock_async_client():
    """Create a mock async API client."""
    client = MagicMock(spec=AsyncAPIClient)
    return client


@pytest.fixture
def async_invoice_endpoint(mock_async_client):
    """Create an async invoice endpoint with a mock client."""
    return AsyncInvoiceEndpoint(mock_async_client)


@pytest.fixture
def sample_invoice_data():
    """Return sample invoice data."""
    return {
        "id": "123456",
        "invoice_number": "INV-001",
        "customer_id": "CUST-001",
        "invoice_date": "2023-03-15",
        "due_date": "2023-04-15",
        "line_items": [
            {
                "description": "Test Product",
                "quantity": 2,
                "unit_price": 99.99,
                "vat_rate": 25.0,
                "product_id": "PROD-001",
                "unit": "pcs",
                "line_total": 199.98
            }
        ],
        "status": "DRAFT",
        "currency": "NOK",
        "totals": {
            "subtotal": 199.98,
            "vat_amount": 50.00,
            "total": 249.98
        },
        "created_at": "2023-03-15T12:00:00Z",
        "updated_at": "2023-03-15T12:00:00Z"
    }


@pytest.mark.asyncio
async def test_list_invoices(async_invoice_endpoint, mock_async_client, sample_invoice_data):
    """Test listing invoices asynchronously."""
    # Mock the response
    mock_response = MagicMock()
    mock_response.json.return_value = [sample_invoice_data, sample_invoice_data]
    mock_async_client.get.return_value = mock_response
    mock_async_client.parse_response_list.return_value = [
        Invoice.model_validate(sample_invoice_data),
        Invoice.model_validate(sample_invoice_data)
    ]

    # Call the method
    result = await async_invoice_endpoint.list(page=1, page_size=10)

    # Verify
    mock_async_client.get.assert_called_once_with(
        "/invoices",
        params={"page": 1, "pageSize": 10}
    )
    assert len(result) == 2
    assert isinstance(result[0], Invoice)
    assert result[0].id == "123456"
    assert result[0].invoice_number == "INV-001"


@pytest.mark.asyncio
async def test_list_invoices_with_filters(async_invoice_endpoint, mock_async_client, sample_invoice_data):
    """Test listing invoices with status and customer filters asynchronously."""
    # Mock the response
    mock_response = MagicMock()
    mock_response.json.return_value = [sample_invoice_data]
    mock_async_client.get.return_value = mock_response
    mock_async_client.parse_response_list.return_value = [
        Invoice.model_validate(sample_invoice_data)
    ]

    # Call the method
    result = await async_invoice_endpoint.list(
        page=1, 
        page_size=10,
        status=InvoiceStatus.DRAFT,
        customer_id="CUST-001"
    )

    # Verify
    mock_async_client.get.assert_called_once_with(
        "/invoices",
        params={
            "page": 1, 
            "pageSize": 10, 
            "status": InvoiceStatus.DRAFT,
            "customerId": "CUST-001"
        }
    )
    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_invoice(async_invoice_endpoint, mock_async_client, sample_invoice_data):
    """Test getting an invoice by ID asynchronously."""
    # Mock the response
    mock_response = MagicMock()
    mock_async_client.get.return_value = mock_response
    mock_async_client.parse_response.return_value = Invoice.model_validate(sample_invoice_data)

    # Call the method
    result = await async_invoice_endpoint.get("123456")

    # Verify
    mock_async_client.get.assert_called_once_with("/invoices/123456")
    assert isinstance(result, Invoice)
    assert result.id == "123456"
    assert result.invoice_number == "INV-001"


@pytest.mark.asyncio
async def test_create_invoice(async_invoice_endpoint, mock_async_client, sample_invoice_data):
    """Test creating an invoice asynchronously."""
    # Mock the response
    mock_response = MagicMock()
    mock_async_client.post.return_value = mock_response
    mock_async_client.parse_response.return_value = Invoice.model_validate(sample_invoice_data)

    # Create the input data
    invoice_create = InvoiceCreate(
        customer_id="CUST-001",
        invoice_date=date(2023, 3, 15),
        due_date=date(2023, 4, 15),
        line_items=[
            InvoiceLineItem(
                description="Test Product",
                quantity=2,
                unit_price=99.99,
                vat_rate=25.0,
                product_id="PROD-001",
                unit="pcs"
            )
        ],
        currency="NOK"
    )

    # Call the method
    result = await async_invoice_endpoint.create(invoice_create)

    # Verify
    mock_async_client.post.assert_called_once()
    assert isinstance(result, Invoice)
    assert result.id == "123456"
    assert result.invoice_number == "INV-001"


@pytest.mark.asyncio
async def test_update_invoice(async_invoice_endpoint, mock_async_client, sample_invoice_data):
    """Test updating an invoice asynchronously."""
    # Mock the response
    mock_response = MagicMock()
    mock_async_client.patch.return_value = mock_response
    mock_async_client.parse_response.return_value = Invoice.model_validate(sample_invoice_data)

    # Create the input data
    invoice_update = InvoiceUpdate(
        notes="Updated notes",
        reference="PO-12345"
    )

    # Call the method
    result = await async_invoice_endpoint.update("123456", invoice_update)

    # Verify
    mock_async_client.patch.assert_called_once()
    assert isinstance(result, Invoice)
    assert result.id == "123456"


@pytest.mark.asyncio
async def test_delete_invoice(async_invoice_endpoint, mock_async_client):
    """Test deleting an invoice asynchronously."""
    # Mock the response
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_async_client.delete.return_value = mock_response

    # Call the method
    await async_invoice_endpoint.delete("123456")

    # Verify
    mock_async_client.delete.assert_called_once_with("/invoices/123456")


@pytest.mark.asyncio
async def test_send_invoice(async_invoice_endpoint, mock_async_client, sample_invoice_data):
    """Test sending an invoice asynchronously."""
    # Update sample data
    sent_invoice = sample_invoice_data.copy()
    sent_invoice["status"] = "SENT"
    
    # Mock the response
    mock_response = MagicMock()
    mock_async_client.post.return_value = mock_response
    mock_async_client.parse_response.return_value = Invoice.model_validate(sent_invoice)

    # Call the method
    result = await async_invoice_endpoint.send("123456")

    # Verify
    mock_async_client.post.assert_called_once_with("/invoices/123456/send")
    assert isinstance(result, Invoice)
    assert result.id == "123456"
    assert result.status == InvoiceStatus.SENT


@pytest.mark.asyncio
async def test_mark_as_paid(async_invoice_endpoint, mock_async_client, sample_invoice_data):
    """Test marking an invoice as paid asynchronously."""
    # Update sample data
    paid_invoice = sample_invoice_data.copy()
    paid_invoice["status"] = "PAID"
    paid_invoice["payment_date"] = "2023-03-20"
    
    # Mock the response
    mock_response = MagicMock()
    mock_async_client.post.return_value = mock_response
    mock_async_client.parse_response.return_value = Invoice.model_validate(paid_invoice)

    # Call the method with payment date
    result = await async_invoice_endpoint.mark_as_paid("123456", payment_date="2023-03-20")

    # Verify
    mock_async_client.post.assert_called_once_with(
        "/invoices/123456/mark-paid", 
        json={"paymentDate": "2023-03-20"}
    )
    assert isinstance(result, Invoice)
    assert result.id == "123456"
    assert result.status == InvoiceStatus.PAID


@pytest.mark.asyncio
async def test_create_credit_note(async_invoice_endpoint, mock_async_client, sample_invoice_data):
    """Test creating a credit note asynchronously."""
    # Update sample data
    credit_note = sample_invoice_data.copy()
    credit_note["id"] = "CREDIT-001"
    credit_note["is_credit_note"] = True
    credit_note["credited_invoice_id"] = "123456"
    
    # Mock the response
    mock_response = MagicMock()
    mock_async_client.post.return_value = mock_response
    mock_async_client.parse_response.return_value = Invoice.model_validate(credit_note)

    # Call the method
    result = await async_invoice_endpoint.create_credit_note("123456")

    # Verify
    mock_async_client.post.assert_called_once_with("/invoices/123456/credit")
    assert isinstance(result, Invoice)
    assert result.id == "CREDIT-001"
    assert result.is_credit_note is True
    assert result.credited_invoice_id == "123456"


@pytest.mark.asyncio
async def test_batch_get_invoices(async_invoice_endpoint, mock_async_client, sample_invoice_data):
    """Test batch getting invoices asynchronously."""
    # Mock the response
    mock_batch_response = MagicMock()
    mock_batch_response.is_successful.return_value = True
    mock_batch_response.get_body.return_value = sample_invoice_data
    mock_async_client.send_batch_request.return_value = mock_batch_response

    # Call the method
    result = await async_invoice_endpoint.batch_get(["123456", "789012"])

    # Verify
    mock_async_client.send_batch_request.assert_called_once()
    assert len(result) == 2
    assert "123456" in result
    assert "789012" in result
    assert isinstance(result["123456"], Invoice) 