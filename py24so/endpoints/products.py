from typing import Any, Dict, List, Optional, Union, cast

import httpx

from py24so.core.batch import BatchRequest
from py24so.core.client import APIClient, AsyncAPIClient
from py24so.core.exceptions import NotFoundError
from py24so.models.product import Product, ProductCreate, ProductUpdate


class ProductEndpoint:
    """
    Product endpoint for the 24SevenOffice API.

    This class provides methods for working with products in the API.
    """

    def __init__(self, client: APIClient):
        """
        Initialize the product endpoint.

        Args:
            client: API client
        """
        self.client = client
        self.base_path = "/products"

    def list(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Product]:
        """
        List products.

        Args:
            page: Page number
            page_size: Number of items per page
            search: Search query
            **kwargs: Additional query parameters

        Returns:
            List of products
        """
        params = {
            "page": page,
            "pageSize": page_size,
            **kwargs,
        }

        if search:
            params["search"] = search

        response = self.client.get(self.base_path, params=params)
        return self.client.parse_response_list(response, Product)

    def get(self, product_id: str) -> Product:
        """
        Get a product by ID.

        Args:
            product_id: Product ID

        Returns:
            Product

        Raises:
            NotFoundError: If the product is not found
        """
        response = self.client.get(f"{self.base_path}/{product_id}")
        return self.client.parse_response(response, Product)

    def create(self, product: Union[Dict[str, Any], ProductCreate]) -> Product:
        """
        Create a new product.

        Args:
            product: Product data

        Returns:
            Created product
        """
        if isinstance(product, ProductCreate):
            data = product.model_dump(exclude_unset=True)
        else:
            data = product

        response = self.client.post(self.base_path, json=data)
        return self.client.parse_response(response, Product)

    def update(
        self,
        product_id: str,
        product: Union[Dict[str, Any], ProductUpdate],
    ) -> Product:
        """
        Update a product.

        Args:
            product_id: Product ID
            product: Product data

        Returns:
            Updated product

        Raises:
            NotFoundError: If the product is not found
        """
        if isinstance(product, ProductUpdate):
            data = product.model_dump(exclude_unset=True, exclude_none=True)
        else:
            data = product

        response = self.client.patch(f"{self.base_path}/{product_id}", json=data)
        return self.client.parse_response(response, Product)

    def delete(self, product_id: str) -> None:
        """
        Delete a product.

        Args:
            product_id: Product ID

        Raises:
            NotFoundError: If the product is not found
        """
        response = self.client.delete(f"{self.base_path}/{product_id}")
        if response.status_code != 204:
            # If not 204 No Content, then parse the response
            self.client.parse_response(response, dict)

    def batch_get(self, product_ids: List[str]) -> Dict[str, Product]:
        """
        Get multiple products in a single batch request.

        Args:
            product_ids: List of product IDs

        Returns:
            Dictionary mapping product IDs to product objects
        """
        batch = BatchRequest()

        for product_id in product_ids:
            batch.add(
                method="GET",
                path=f"{self.base_path}/{product_id}",
                request_id=product_id,
            )

        batch_response = self.client.send_batch_request(batch)

        # Process the responses
        products: Dict[str, Product] = {}
        for product_id in product_ids:
            if batch_response.is_successful(product_id):
                body = batch_response.get_body(product_id)
                if body:
                    products[product_id] = Product.model_validate(body)

        return products


class AsyncProductEndpoint:
    """
    Asynchronous product endpoint for the 24SevenOffice API.

    This class provides asynchronous methods for working with products in the API.
    """

    def __init__(self, client: AsyncAPIClient):
        """
        Initialize the async product endpoint.

        Args:
            client: Async API client
        """
        self.client = client
        self.base_path = "/products"

    async def list(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Product]:
        """
        List products asynchronously.

        Args:
            page: Page number
            page_size: Number of items per page
            search: Search query
            **kwargs: Additional query parameters

        Returns:
            List of products
        """
        params = {
            "page": page,
            "pageSize": page_size,
            **kwargs,
        }

        if search:
            params["search"] = search

        response = await self.client.get(self.base_path, params=params)
        return await self.client.parse_response_list(response, Product)

    async def get(self, product_id: str) -> Product:
        """
        Get a product by ID asynchronously.

        Args:
            product_id: Product ID

        Returns:
            Product

        Raises:
            NotFoundError: If the product is not found
        """
        response = await self.client.get(f"{self.base_path}/{product_id}")
        return await self.client.parse_response(response, Product)

    async def create(self, product: Union[Dict[str, Any], ProductCreate]) -> Product:
        """
        Create a new product asynchronously.

        Args:
            product: Product data

        Returns:
            Created product
        """
        if isinstance(product, ProductCreate):
            data = product.model_dump(exclude_unset=True)
        else:
            data = product

        response = await self.client.post(self.base_path, json=data)
        return await self.client.parse_response(response, Product)

    async def update(
        self,
        product_id: str,
        product: Union[Dict[str, Any], ProductUpdate],
    ) -> Product:
        """
        Update a product asynchronously.

        Args:
            product_id: Product ID
            product: Product data

        Returns:
            Updated product

        Raises:
            NotFoundError: If the product is not found
        """
        if isinstance(product, ProductUpdate):
            data = product.model_dump(exclude_unset=True, exclude_none=True)
        else:
            data = product

        response = await self.client.patch(f"{self.base_path}/{product_id}", json=data)
        return await self.client.parse_response(response, Product)

    async def delete(self, product_id: str) -> None:
        """
        Delete a product asynchronously.

        Args:
            product_id: Product ID

        Raises:
            NotFoundError: If the product is not found
        """
        response = await self.client.delete(f"{self.base_path}/{product_id}")
        if response.status_code != 204:
            # If not 204 No Content, then parse the response
            await self.client.parse_response(response, dict)

    async def batch_get(self, product_ids: List[str]) -> Dict[str, Product]:
        """
        Get multiple products in a single batch request asynchronously.

        Args:
            product_ids: List of product IDs

        Returns:
            Dictionary mapping product IDs to product objects
        """
        batch = BatchRequest()

        for product_id in product_ids:
            batch.add(
                method="GET",
                path=f"{self.base_path}/{product_id}",
                request_id=product_id,
            )

        batch_response = await self.client.send_batch_request(batch)

        # Process the responses
        products: Dict[str, Product] = {}
        for product_id in product_ids:
            if batch_response.is_successful(product_id):
                body = batch_response.get_body(product_id)
                if body:
                    products[product_id] = Product.model_validate(body)

        return products
