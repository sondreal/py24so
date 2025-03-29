"""Unit tests for the product endpoint."""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from py24so.core.client import APIClient
from py24so.endpoints.products import ProductEndpoint
from py24so.models.product import Product, ProductCreate, ProductUpdate, PriceInfo


@pytest.fixture
def mock_client():
    """Create a mock API client."""
    client = MagicMock(spec=APIClient)
    return client


@pytest.fixture
def product_endpoint(mock_client):
    """Create a product endpoint with a mock client."""
    return ProductEndpoint(mock_client)


@pytest.fixture
def sample_product_data():
    """Return sample product data."""
    return {
        "id": "123456",
        "name": "Test Product",
        "description": "Product for testing",
        "sku": "TEST-001",
        "price_info": {
            "price": 99.99,
            "currency": "NOK",
            "vat_rate": 25.0
        },
        "is_active": True,
        "created_at": "2023-03-15T12:00:00Z",
        "updated_at": "2023-03-15T12:00:00Z"
    }


def test_list_products(product_endpoint, mock_client, sample_product_data):
    """Test listing products."""
    # Mock the response
    mock_response = MagicMock()
    mock_response.json.return_value = [sample_product_data, sample_product_data]
    mock_client.get.return_value = mock_response
    mock_client.parse_response_list.return_value = [
        Product.model_validate(sample_product_data),
        Product.model_validate(sample_product_data)
    ]

    # Call the method
    result = product_endpoint.list(page=1, page_size=10)

    # Verify
    mock_client.get.assert_called_once_with(
        "/products",
        params={"page": 1, "pageSize": 10}
    )
    assert len(result) == 2
    assert isinstance(result[0], Product)
    assert result[0].id == "123456"
    assert result[0].name == "Test Product"


def test_get_product(product_endpoint, mock_client, sample_product_data):
    """Test getting a product by ID."""
    # Mock the response
    mock_response = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.parse_response.return_value = Product.model_validate(sample_product_data)

    # Call the method
    result = product_endpoint.get("123456")

    # Verify
    mock_client.get.assert_called_once_with("/products/123456")
    assert isinstance(result, Product)
    assert result.id == "123456"
    assert result.name == "Test Product"


def test_create_product(product_endpoint, mock_client, sample_product_data):
    """Test creating a product."""
    # Mock the response
    mock_response = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.parse_response.return_value = Product.model_validate(sample_product_data)

    # Create the input data
    product_create = ProductCreate(
        name="Test Product",
        description="Product for testing",
        sku="TEST-001",
        price_info=PriceInfo(
            price=99.99,
            currency="NOK",
            vat_rate=25.0
        )
    )

    # Call the method
    result = product_endpoint.create(product_create)

    # Verify
    mock_client.post.assert_called_once()
    assert isinstance(result, Product)
    assert result.id == "123456"
    assert result.name == "Test Product"


def test_update_product(product_endpoint, mock_client, sample_product_data):
    """Test updating a product."""
    # Mock the response
    mock_response = MagicMock()
    mock_client.patch.return_value = mock_response
    mock_client.parse_response.return_value = Product.model_validate(sample_product_data)

    # Create the input data
    product_update = ProductUpdate(
        name="Updated Product",
        description="Updated description"
    )

    # Call the method
    result = product_endpoint.update("123456", product_update)

    # Verify
    mock_client.patch.assert_called_once()
    assert isinstance(result, Product)
    assert result.id == "123456"


def test_delete_product(product_endpoint, mock_client):
    """Test deleting a product."""
    # Mock the response
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_client.delete.return_value = mock_response

    # Call the method
    product_endpoint.delete("123456")

    # Verify
    mock_client.delete.assert_called_once_with("/products/123456")


def test_batch_get_products(product_endpoint, mock_client, sample_product_data):
    """Test batch getting products."""
    # Mock the response
    mock_batch_response = MagicMock()
    mock_batch_response.is_successful.return_value = True
    mock_batch_response.get_body.return_value = sample_product_data
    mock_client.send_batch_request.return_value = mock_batch_response

    # Call the method
    result = product_endpoint.batch_get(["123456", "789012"])

    # Verify
    mock_client.send_batch_request.assert_called_once()
    assert len(result) == 2
    assert "123456" in result
    assert "789012" in result
    assert isinstance(result["123456"], Product) 