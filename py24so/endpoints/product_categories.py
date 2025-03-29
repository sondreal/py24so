from typing import Any, Dict, List, Optional, Union, cast

import httpx

from py24so.core.batch import BatchRequest
from py24so.core.client import APIClient, AsyncAPIClient
from py24so.core.exceptions import NotFoundError
from py24so.models.product_category import (
    ProductCategory,
    ProductCategoryCreate,
    ProductCategoryUpdate,
)


class ProductCategoryEndpoint:
    """
    Product Category endpoint for the 24SevenOffice API.

    This class provides methods for working with product categories in the API.
    """

    def __init__(self, client: APIClient):
        """
        Initialize the product category endpoint.

        Args:
            client: API client
        """
        self.client = client
        self.base_path = "/productcategories"

    def list(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        **kwargs: Any,
    ) -> List[ProductCategory]:
        """
        List product categories.

        Args:
            page: Page number
            page_size: Number of items per page
            search: Search query
            **kwargs: Additional query parameters

        Returns:
            List of product categories
        """
        params = {
            "page": page,
            "pageSize": page_size,
            **kwargs,
        }

        if search:
            params["search"] = search

        response = self.client.get(self.base_path, params=params)
        return self.client.parse_response_list(response, ProductCategory)

    def get(self, category_id: str) -> ProductCategory:
        """
        Get a product category by ID.

        Args:
            category_id: Product Category ID

        Returns:
            Product Category

        Raises:
            NotFoundError: If the product category is not found
        """
        response = self.client.get(f"{self.base_path}/{category_id}")
        return self.client.parse_response(response, ProductCategory)

    def create(self, category: Union[Dict[str, Any], ProductCategoryCreate]) -> ProductCategory:
        """
        Create a new product category.

        Args:
            category: Product Category data

        Returns:
            Created product category
        """
        if isinstance(category, ProductCategoryCreate):
            data = category.model_dump(exclude_unset=True)
        else:
            data = category

        response = self.client.post(self.base_path, json=data)
        return self.client.parse_response(response, ProductCategory)

    def update(
        self,
        category_id: str,
        category: Union[Dict[str, Any], ProductCategoryUpdate],
    ) -> ProductCategory:
        """
        Update a product category.

        Args:
            category_id: Product Category ID
            category: Product Category data

        Returns:
            Updated product category

        Raises:
            NotFoundError: If the product category is not found
        """
        if isinstance(category, ProductCategoryUpdate):
            data = category.model_dump(exclude_unset=True, exclude_none=True)
        else:
            data = category

        response = self.client.patch(f"{self.base_path}/{category_id}", json=data)
        return self.client.parse_response(response, ProductCategory)

    def delete(self, category_id: str) -> None:
        """
        Delete a product category.

        Args:
            category_id: Product Category ID

        Raises:
            NotFoundError: If the product category is not found
        """
        response = self.client.delete(f"{self.base_path}/{category_id}")
        if response.status_code != 204:
            # If not 204 No Content, then parse the response
            self.client.parse_response(response, dict)

    def batch_get(self, category_ids: List[str]) -> Dict[str, ProductCategory]:
        """
        Get multiple product categories in a single batch request.

        Args:
            category_ids: List of product category IDs

        Returns:
            Dictionary mapping product category IDs to product category objects
        """
        batch = BatchRequest()

        for category_id in category_ids:
            batch.add(
                method="GET",
                path=f"{self.base_path}/{category_id}",
                request_id=category_id,
            )

        batch_response = self.client.send_batch_request(batch)

        # Process the responses
        categories: Dict[str, ProductCategory] = {}
        for category_id in category_ids:
            if batch_response.is_successful(category_id):
                body = batch_response.get_body(category_id)
                if body:
                    categories[category_id] = ProductCategory.model_validate(body)

        return categories


class AsyncProductCategoryEndpoint:
    """
    Asynchronous product category endpoint for the 24SevenOffice API.

    This class provides asynchronous methods for working with product categories in the API.
    """

    def __init__(self, client: AsyncAPIClient):
        """
        Initialize the async product category endpoint.

        Args:
            client: Async API client
        """
        self.client = client
        self.base_path = "/productcategories"

    async def list(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        **kwargs: Any,
    ) -> List[ProductCategory]:
        """
        List product categories asynchronously.

        Args:
            page: Page number
            page_size: Number of items per page
            search: Search query
            **kwargs: Additional query parameters

        Returns:
            List of product categories
        """
        params = {
            "page": page,
            "pageSize": page_size,
            **kwargs,
        }

        if search:
            params["search"] = search

        response = await self.client.get(self.base_path, params=params)
        return await self.client.parse_response_list(response, ProductCategory)

    async def get(self, category_id: str) -> ProductCategory:
        """
        Get a product category by ID asynchronously.

        Args:
            category_id: Product Category ID

        Returns:
            Product Category

        Raises:
            NotFoundError: If the product category is not found
        """
        response = await self.client.get(f"{self.base_path}/{category_id}")
        return await self.client.parse_response(response, ProductCategory)

    async def create(
        self, category: Union[Dict[str, Any], ProductCategoryCreate]
    ) -> ProductCategory:
        """
        Create a new product category asynchronously.

        Args:
            category: Product Category data

        Returns:
            Created product category
        """
        if isinstance(category, ProductCategoryCreate):
            data = category.model_dump(exclude_unset=True)
        else:
            data = category

        response = await self.client.post(self.base_path, json=data)
        return await self.client.parse_response(response, ProductCategory)

    async def update(
        self,
        category_id: str,
        category: Union[Dict[str, Any], ProductCategoryUpdate],
    ) -> ProductCategory:
        """
        Update a product category asynchronously.

        Args:
            category_id: Product Category ID
            category: Product Category data

        Returns:
            Updated product category

        Raises:
            NotFoundError: If the product category is not found
        """
        if isinstance(category, ProductCategoryUpdate):
            data = category.model_dump(exclude_unset=True, exclude_none=True)
        else:
            data = category

        response = await self.client.patch(f"{self.base_path}/{category_id}", json=data)
        return await self.client.parse_response(response, ProductCategory)

    async def delete(self, category_id: str) -> None:
        """
        Delete a product category asynchronously.

        Args:
            category_id: Product Category ID

        Raises:
            NotFoundError: If the product category is not found
        """
        response = await self.client.delete(f"{self.base_path}/{category_id}")
        if response.status_code != 204:
            # If not 204 No Content, then parse the response
            await self.client.parse_response(response, dict)

    async def batch_get(self, category_ids: List[str]) -> Dict[str, ProductCategory]:
        """
        Get multiple product categories in a single batch request asynchronously.

        Args:
            category_ids: List of product category IDs

        Returns:
            Dictionary mapping product category IDs to product category objects
        """
        batch = BatchRequest()

        for category_id in category_ids:
            batch.add(
                method="GET",
                path=f"{self.base_path}/{category_id}",
                request_id=category_id,
            )

        batch_response = await self.client.send_batch_request(batch)

        # Process the responses
        categories: Dict[str, ProductCategory] = {}
        for category_id in category_ids:
            if batch_response.is_successful(category_id):
                body = batch_response.get_body(category_id)
                if body:
                    categories[category_id] = ProductCategory.model_validate(body)

        return categories
