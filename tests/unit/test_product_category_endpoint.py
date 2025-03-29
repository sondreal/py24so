"""Unit tests for the product category endpoint."""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from py24so.core.client import APIClient
from py24so.endpoints.product_categories import ProductCategoryEndpoint
from py24so.models.product_category import (
    ProductCategory,
    ProductCategoryCreate,
    ProductCategoryUpdate,
)


@pytest.fixture
def mock_client():
    """Create a mock API client."""
    client = MagicMock(spec=APIClient)
    return client


@pytest.fixture
def category_endpoint(mock_client):
    """Create a product category endpoint with a mock client."""
    return ProductCategoryEndpoint(mock_client)


@pytest.fixture
def sample_category_data():
    """Return sample product category data."""
    return {
        "id": "12",
        "name": "Shoe accessories",
        "alternativeReference": "dk-45-34",
        "parentId": 0,
        "modifiedAt": "2023-12-31 18:00:00.000Z",
    }


def test_list_categories(category_endpoint, mock_client, sample_category_data):
    """Test listing product categories."""
    # Mock the response
    mock_response = MagicMock()
    mock_response.json.return_value = [sample_category_data, sample_category_data]
    mock_client.get.return_value = mock_response
    mock_client.parse_response_list.return_value = [
        ProductCategory.model_validate(sample_category_data),
        ProductCategory.model_validate(sample_category_data),
    ]

    # Call the method
    result = category_endpoint.list(page=1, page_size=10)

    # Verify
    mock_client.get.assert_called_once_with(
        "/productcategories", params={"page": 1, "pageSize": 10}
    )
    assert len(result) == 2
    assert isinstance(result[0], ProductCategory)
    assert result[0].id == "12"
    assert result[0].name == "Shoe accessories"
    assert result[0].alternative_reference == "dk-45-34"
    assert result[0].parent_id == 0


def test_get_category(category_endpoint, mock_client, sample_category_data):
    """Test getting a product category by ID."""
    # Mock the response
    mock_response = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.parse_response.return_value = ProductCategory.model_validate(sample_category_data)

    # Call the method
    result = category_endpoint.get("12")

    # Verify
    mock_client.get.assert_called_once_with("/productcategories/12")
    assert isinstance(result, ProductCategory)
    assert result.id == "12"
    assert result.name == "Shoe accessories"
    assert result.alternative_reference == "dk-45-34"


def test_create_category(category_endpoint, mock_client, sample_category_data):
    """Test creating a product category."""
    # Mock the response
    mock_response = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.parse_response.return_value = ProductCategory.model_validate(sample_category_data)

    # Create the input data
    category_create = ProductCategoryCreate(
        name="Shoe accessories", parentId="0", alternativeReference="dk-45-34"
    )

    # Call the method
    result = category_endpoint.create(category_create)

    # Verify
    mock_client.post.assert_called_once()
    assert isinstance(result, ProductCategory)
    assert result.id == "12"
    assert result.name == "Shoe accessories"
    assert result.alternative_reference == "dk-45-34"


def test_update_category(category_endpoint, mock_client, sample_category_data):
    """Test updating a product category."""
    # Mock the response
    mock_response = MagicMock()
    mock_client.patch.return_value = mock_response
    mock_client.parse_response.return_value = ProductCategory.model_validate(sample_category_data)

    # Create the input data
    category_update = ProductCategoryUpdate(name="Updated Category Name")

    # Call the method
    result = category_endpoint.update("12", category_update)

    # Verify
    mock_client.patch.assert_called_once()
    assert isinstance(result, ProductCategory)
    assert result.id == "12"


def test_delete_category(category_endpoint, mock_client):
    """Test deleting a product category."""
    # Mock the response
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_client.delete.return_value = mock_response

    # Call the method
    category_endpoint.delete("12")

    # Verify
    mock_client.delete.assert_called_once_with("/productcategories/12")


def test_batch_get_categories(category_endpoint, mock_client, sample_category_data):
    """Test batch getting product categories."""
    # Mock the response
    mock_batch_response = MagicMock()
    mock_batch_response.is_successful.return_value = True
    mock_batch_response.get_body.return_value = sample_category_data
    mock_client.send_batch_request.return_value = mock_batch_response

    # Call the method
    result = category_endpoint.batch_get(["12", "15"])

    # Verify
    mock_client.send_batch_request.assert_called_once()
    assert len(result) == 2
    assert "12" in result
    assert "15" in result
    assert isinstance(result["12"], ProductCategory)
