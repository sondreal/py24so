"""Integration tests for the product category endpoint.

NOTE: These tests require API credentials to be set in the .env file or as environment variables.
"""

import os

import pytest
from dotenv import load_dotenv

from py24so import Client24SO
from py24so.models.config import ClientOptions
from py24so.models.product_category import ProductCategoryCreate, ProductCategoryUpdate

# Load environment variables from .env file
load_dotenv()

# Skip all tests if credentials are not set
pytestmark = pytest.mark.skipif(
    not all(
        [
            os.environ.get("CLIENT_ID"),
            os.environ.get("CLIENT_SECRET"),
            os.environ.get("ORGANIZATION_ID"),
        ]
    ),
    reason="API credentials not set. Set CLIENT_ID, CLIENT_SECRET, and ORGANIZATION_ID environment variables.",
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
def test_category_data():
    """Product category data for testing."""
    unique_id = os.urandom(4).hex()
    return ProductCategoryCreate(
        name=f"Integration Test Category {unique_id}",  # Create a unique name
        parentId="0",
        alternativeReference=f"test-ref-{unique_id}"
    )


def test_category_crud(client, test_category_data):
    """Test basic CRUD operations on the product category endpoint."""
    # Create a new product category
    created_category = client.product_categories.create(test_category_data)
    assert created_category.name == test_category_data.name
    assert created_category.id

    # Get the product category
    category_id = created_category.id
    fetched_category = client.product_categories.get(category_id)
    assert fetched_category.id == category_id
    assert fetched_category.name == test_category_data.name

    # Update the product category
    update_data = ProductCategoryUpdate(
        name=f"Updated {test_category_data.name}",
        alternativeReference=f"updated-ref"
    )
    updated_category = client.product_categories.update(category_id, update_data)
    assert updated_category.id == category_id
    assert updated_category.name == update_data.name

    # Verify update by fetching again
    refetched_category = client.product_categories.get(category_id)
    assert refetched_category.name == update_data.name

    # List categories and verify our test category is in the list
    categories = client.product_categories.list(page=1, page_size=100)
    found = False
    for category in categories:
        if category.id == category_id:
            found = True
            break
    assert found

    # Search for the category
    search_results = client.product_categories.list(search=update_data.name)
    assert any(p.id == category_id for p in search_results)

    # Batch get categories
    batch_results = client.product_categories.batch_get([category_id])
    assert category_id in batch_results
    assert batch_results[category_id].name == update_data.name

    # Delete the product category
    client.product_categories.delete(category_id)

    # Verify category is gone (this should raise a NotFoundError)
    with pytest.raises(Exception):
        client.product_categories.get(category_id) 