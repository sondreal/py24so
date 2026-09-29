# AUTO-GENERATED from py24so/resources/_async by scripts/unasync.py. DO NOT EDIT.

from typing import Any, Iterable, List, Mapping, Optional, Union

from py24so._client import APIClient
from py24so._pagination import Paginator
from py24so._utils import path_param, serialize_body
from py24so.models.products import (
    PriceList,
    PriceListPrice,
    Product,
    ProductCategory,
    ProductCategoryCreate,
    ProductCategoryUpdate,
    ProductCreate,
    ProductDimension,
    ProductSalesTypeOverride,
    ProductUnit,
    ProductUpdate,
)
from py24so.resources._sync._resource import Resource

_DEFAULT_PRODUCT_PAGE_SIZE = 25


class ProductDimensions(Resource):
    """``/products/{id}/dimensions``: dimension values (department, project, ...) on a product."""

    def list(self, product_id: Union[int, str]) -> List[ProductDimension]:
        response = self._client.send("GET", f"/products/{path_param(product_id)}/dimensions")
        return self._client.parse_list(response, ProductDimension)

    def set(
        self, product_id: Union[int, str], dimension_type: Union[int, str], value: str
    ) -> List[ProductDimension]:
        """Set the product's value for a dimension type. Returns all the product's dimensions."""
        response = self._client.send(
            "PUT",
            f"/products/{path_param(product_id)}/dimensions/{path_param(dimension_type)}",
            json={"value": value},
        )
        return self._client.parse_list(response, ProductDimension)

    def delete(self, product_id: Union[int, str], dimension_type: Union[int, str]) -> None:
        """Remove the product's value for a dimension type."""
        self._client.send(
            "DELETE",
            f"/products/{path_param(product_id)}/dimensions/{path_param(dimension_type)}",
        )


class ProductSalesTypeOverrides(Resource):
    """``/products/{id}/salestypeOverrides``: per-sales-type revenue accounts for a product."""

    def list(self, product_id: Union[int, str]) -> List[ProductSalesTypeOverride]:
        response = self._client.send(
            "GET", f"/products/{path_param(product_id)}/salestypeOverrides"
        )
        return self._client.parse_list(response, ProductSalesTypeOverride)

    def set(
        self,
        product_id: Union[int, str],
        sales_type_id: Union[int, str],
        account_number: Optional[int],
    ) -> Optional[ProductSalesTypeOverride]:
        """Use ``account_number`` for this product when sold with ``sales_type_id``.

        Pass ``None`` to reset to the sales type's default account.
        """
        response = self._client.send(
            "PUT",
            f"/products/{path_param(product_id)}/salestypeOverrides/{path_param(sales_type_id)}",
            json={"accountNumber": account_number},
        )
        # 200 returns the override; 204 (no body) means it was reset to the default.
        result: Optional[ProductSalesTypeOverride] = self._client.parse(
            response, ProductSalesTypeOverride
        )
        return result

    def delete(self, product_id: Union[int, str], sales_type_id: Union[int, str]) -> None:
        self._client.send(
            "DELETE",
            f"/products/{path_param(product_id)}/salestypeOverrides/{path_param(sales_type_id)}",
        )


class Products(Resource):
    """``/products``"""

    def __init__(self, client: APIClient) -> None:
        super().__init__(client)
        self.dimensions = ProductDimensions(client)
        self.sales_type_overrides = ProductSalesTypeOverrides(client)

    def list(
        self,
        *,
        search: Optional[str] = None,
        category_ids: Optional[Iterable[int]] = None,
        supplier_ids: Optional[Iterable[int]] = None,
        product_number: Optional[str] = None,
        ean: Optional[str] = None,
        page_size: Optional[int] = None,
        start_page: Optional[int] = None,
        extra_params: Optional[Mapping[str, Any]] = None,
    ) -> Paginator[Product]:
        """Iterate over products, following pagination automatically.

        Args:
            search: Free-text product search (the API's ``productSearch``).
            category_ids: Only products in these categories.
            supplier_ids: Only products from these suppliers.
            product_number: Only the product with this product number.
            ean: Only products with this EAN/barcode.
            page_size: Products per request (the API's ``limit``, default 25).
            start_page: Page to start from (default 1).
            extra_params: Additional raw query parameters.
        """
        params = {
            "productSearch": search,
            "categoryIds": list(category_ids) if category_ids is not None else None,
            "supplierIds": list(supplier_ids) if supplier_ids is not None else None,
            "productNumber": product_number,
            "ean": ean,
            "limit": page_size,
            "page": start_page,
            **(extra_params or {}),
        }
        return self._client.paginate(
            "/products",
            Product,
            params,
            page_param="page",
            page_size=page_size or _DEFAULT_PRODUCT_PAGE_SIZE,
        )

    def get(self, product_id: Union[int, str]) -> Product:
        return self._client.request("GET", f"/products/{path_param(product_id)}", cast_to=Product)

    def create(self, product: Union[ProductCreate, Mapping[str, Any]]) -> Product:
        return self._client.request(
            "POST", "/products", json=serialize_body(product, ProductCreate), cast_to=Product
        )

    def update(
        self, product_id: Union[int, str], product: Union[ProductUpdate, Mapping[str, Any]]
    ) -> Product:
        """Update a product. Only fields that are set on ``product`` are changed."""
        return self._client.request(
            "PATCH",
            f"/products/{path_param(product_id)}",
            json=serialize_body(product, ProductUpdate),
            cast_to=Product,
        )

    def delete(self, product_id: Union[int, str]) -> None:
        self._client.send("DELETE", f"/products/{path_param(product_id)}")


class ProductCategories(Resource):
    """``/productcategories``"""

    def list(
        self, *, extra_params: Optional[Mapping[str, Any]] = None
    ) -> Paginator[ProductCategory]:
        """Iterate over all product categories, following pagination automatically."""
        return self._client.paginate("/productcategories", ProductCategory, extra_params)

    def get(self, category_id: Union[int, str]) -> ProductCategory:
        return self._client.request(
            "GET", f"/productcategories/{path_param(category_id)}", cast_to=ProductCategory
        )

    def create(self, category: Union[ProductCategoryCreate, Mapping[str, Any]]) -> ProductCategory:
        return self._client.request(
            "POST",
            "/productcategories",
            json=serialize_body(category, ProductCategoryCreate),
            cast_to=ProductCategory,
        )

    def update(
        self,
        category_id: Union[int, str],
        category: Union[ProductCategoryUpdate, Mapping[str, Any]],
    ) -> ProductCategory:
        """Update a category. Only fields that are set on ``category`` are changed."""
        return self._client.request(
            "PATCH",
            f"/productcategories/{path_param(category_id)}",
            json=serialize_body(category, ProductCategoryUpdate),
            cast_to=ProductCategory,
        )

    def delete(self, category_id: Union[int, str]) -> None:
        self._client.send("DELETE", f"/productcategories/{path_param(category_id)}")


class ProductUnits(Resource):
    """``/productunits``"""

    def list(self) -> List[ProductUnit]:
        response = self._client.send("GET", "/productunits")
        return self._client.parse_list(response, ProductUnit)


class PriceLists(Resource):
    """``/pricelists``"""

    def list(self) -> List[PriceList]:
        response = self._client.send("GET", "/pricelists")
        return self._client.parse_list(response, PriceList)

    def get(self, price_list_id: Union[int, str]) -> PriceList:
        return self._client.request(
            "GET", f"/pricelists/{path_param(price_list_id)}", cast_to=PriceList
        )

    def prices(
        self,
        price_list_id: Union[int, str],
        *,
        product_ids: Optional[Iterable[int]] = None,
    ) -> List[PriceListPrice]:
        """Get the prices in a price list, optionally only for some products."""
        response = self._client.send(
            "GET",
            f"/pricelists/{path_param(price_list_id)}/prices",
            params={"productIds": list(product_ids) if product_ids is not None else None},
        )
        return self._client.parse_list(response, PriceListPrice)
