"""Unit tests for the async product endpoint."""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from py24so.core.client import AsyncAPIClient
from py24so.endpoints.products import AsyncProductEndpoint
from py24so.models.product import PriceInfo, Product, ProductCreate, ProductUpdate


@pytest.fixture
def mock_async_client():
    """Create a mock async API client."""
    client = MagicMock(spec=AsyncAPIClient)
    return client


@pytest.fixture
def async_product_endpoint(mock_async_client):
    """Create an async product endpoint with a mock client."""
    return AsyncProductEndpoint(mock_async_client)


@pytest.fixture
def sample_product_data():
    """Return sample product data."""
    return {
        "id": "123456",
        "name": "Test Product",
        "description": "Product for testing",
        "sku": "TEST-001",
        "price_info": {"price": 99.99, "currency": "NOK", "vat_rate": 25.0},
        "is_active": True,
        "created_at": "2023-03-15T12:00:00Z",
        "updated_at": "2023-03-15T12:00:00Z",
    }


@pytest.mark.asyncio
async def test_list_products(async_product_endpoint, mock_async_client, sample_product_data):
    """Test listing products asynchronously."""
    # Mock the response
    mock_response = MagicMock()
    mock_response.json.return_value = [sample_product_data, sample_product_data]
    mock_async_client.get.return_value = mock_response
    mock_async_client.parse_response_list.return_value = [
        Product.model_validate(sample_product_data),
        Product.model_validate(sample_product_data),
    ]

    # Call the method
    result = await async_product_endpoint.list(page=1, page_size=10)

    # Verify
    mock_async_client.get.assert_called_once_with("/products", params={"page": 1, "pageSize": 10})
    assert len(result) == 2
    assert isinstance(result[0], Product)
    assert result[0].id == "123456"
    assert result[0].name == "Test Product"


@pytest.mark.asyncio
async def test_get_product(async_product_endpoint, mock_async_client, sample_product_data):
    """Test getting a product by ID asynchronously."""
    # Mock the response
    mock_response = MagicMock()
    mock_async_client.get.return_value = mock_response
    mock_async_client.parse_response.return_value = Product.model_validate(sample_product_data)

    # Call the method
    result = await async_product_endpoint.get("123456")

    # Verify
    mock_async_client.get.assert_called_once_with("/products/123456")
    assert isinstance(result, Product)
    assert result.id == "123456"
    assert result.name == "Test Product"


@pytest.mark.asyncio
async def test_create_product(async_product_endpoint, mock_async_client, sample_product_data):
    """Test creating a product asynchronously."""
    # Mock the response
    mock_response = MagicMock()
    mock_async_client.post.return_value = mock_response
    mock_async_client.parse_response.return_value = Product.model_validate(sample_product_data)

    # Create the input data
    product_create = ProductCreate(
        name="Test Product",
        description="Product for testing",
        sku="TEST-001",
        price_info=PriceInfo(price=99.99, currency="NOK", vat_rate=25.0),
    )

    # Call the method
    result = await async_product_endpoint.create(product_create)

    # Verify
    mock_async_client.post.assert_called_once()
    assert isinstance(result, Product)
    assert result.id == "123456"
    assert result.name == "Test Product"


@pytest.mark.asyncio
async def test_update_product(async_product_endpoint, mock_async_client, sample_product_data):
    """Test updating a product asynchronously."""
    # Mock the response
    mock_response = MagicMock()
    mock_async_client.patch.return_value = mock_response
    mock_async_client.parse_response.return_value = Product.model_validate(sample_product_data)

    # Create the input data
    product_update = ProductUpdate(name="Updated Product", description="Updated description")

    # Call the method
    result = await async_product_endpoint.update("123456", product_update)

    # Verify
    mock_async_client.patch.assert_called_once()
    assert isinstance(result, Product)
    assert result.id == "123456"


@pytest.mark.asyncio
async def test_delete_product(async_product_endpoint, mock_async_client):
    """Test deleting a product asynchronously."""
    # Mock the response
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_async_client.delete.return_value = mock_response

    # Call the method
    await async_product_endpoint.delete("123456")

    # Verify
    mock_async_client.delete.assert_called_once_with("/products/123456")


@pytest.mark.asyncio
async def test_batch_get_products(async_product_endpoint, mock_async_client, sample_product_data):
    """Test batch getting products asynchronously."""
    # Mock the response
    mock_batch_response = MagicMock()
    mock_batch_response.is_successful.return_value = True
    mock_batch_response.get_body.return_value = sample_product_data
    mock_async_client.send_batch_request.return_value = mock_batch_response

    # Call the method
    result = await async_product_endpoint.batch_get(["123456", "789012"])

    # Verify
    mock_async_client.send_batch_request.assert_called_once()
    assert len(result) == 2
    assert "123456" in result
    assert "789012" in result
    assert isinstance(result["123456"], Product)
