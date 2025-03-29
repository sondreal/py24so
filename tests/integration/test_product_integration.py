"""Integration tests for the product endpoint.

NOTE: These tests require API credentials to be set in the .env file or as environment variables.
"""

import os

import pytest
from dotenv import load_dotenv

from py24so import Client24SO
from py24so.models.config import ClientOptions
from py24so.models.product import PriceInfo, ProductCreate, ProductUpdate

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
def test_product_data():
    """Product data for testing."""
    return ProductCreate(
        name="Integration Test Product",
        description="Product for integration testing",
        sku=f"TEST-{os.urandom(4).hex()}",  # Create a unique SKU
        price_info=PriceInfo(price=199.99, currency="NOK", vat_rate=25.0, unit="pcs"),
        is_service=False,
        is_active=True,
    )


def test_product_crud(client, test_product_data):
    """Test basic CRUD operations on the product endpoint."""
    # Create a new product
    created_product = client.products.create(test_product_data)
    assert created_product.name == test_product_data.name
    assert created_product.description == test_product_data.description
    assert created_product.sku == test_product_data.sku
    assert created_product.id

    # Get the product
    product_id = created_product.id
    fetched_product = client.products.get(product_id)
    assert fetched_product.id == product_id
    assert fetched_product.name == test_product_data.name

    # Update the product
    update_data = ProductUpdate(
        name="Updated Integration Test Product",
        description="Updated description for integration testing",
    )
    updated_product = client.products.update(product_id, update_data)
    assert updated_product.id == product_id
    assert updated_product.name == update_data.name
    assert updated_product.description == update_data.description

    # Verify update by fetching again
    refetched_product = client.products.get(product_id)
    assert refetched_product.name == update_data.name

    # List products and verify our test product is in the list
    products = client.products.list(page=1, page_size=100)
    found = False
    for product in products:
        if product.id == product_id:
            found = True
            break
    assert found

    # Search for the product
    search_results = client.products.list(search=update_data.name)
    assert any(p.id == product_id for p in search_results)

    # Batch get products
    batch_results = client.products.batch_get([product_id])
    assert product_id in batch_results
    assert batch_results[product_id].name == update_data.name

    # Delete the product
    client.products.delete(product_id)

    # Verify product is gone (this should raise a NotFoundError)
    with pytest.raises(Exception):
        client.products.get(product_id)
