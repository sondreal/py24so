from enum import Enum
from typing import Optional

from py24so.models._base import Py24soModel, Timestamp
from py24so.models.common import IdRef


class ProductType(str, Enum):
    DEFAULT = "default"
    STRUCTURE = "structure"


class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ProductStock(Py24soModel):
    is_managed: Optional[bool] = None
    quantity: Optional[float] = None
    location: Optional[str] = None


class SupplierProduct(Py24soModel):
    """The supplier's own identifiers and price for a product."""

    item_code: Optional[str] = None
    number: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None


class ProductUnit(Py24soModel):
    """A unit of measure, e.g. ``{"id": 1, "name": "Piece", "symbol": "pcs"}``."""

    id: Optional[int] = None
    name: Optional[str] = None
    symbol: Optional[str] = None


class ProductCategoryRef(Py24soModel):
    id: Optional[int] = None
    name: Optional[str] = None


class ProductSupplier(Py24soModel):
    id: Optional[int] = None
    name: Optional[str] = None


class _ProductFields(Py24soModel):
    name: Optional[str] = None
    number: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    cost_price: Optional[float] = None
    sales_price: Optional[float] = None
    indirect_cost: Optional[float] = None
    webshop_enabled: Optional[bool] = None
    stock: Optional[ProductStock] = None
    ean: Optional[str] = None
    ean_alternative: Optional[str] = None
    supplier_product: Optional[SupplierProduct] = None


class Product(_ProductFields):
    """A product. ``type`` is a :class:`ProductType`, ``status`` a :class:`ProductStatus`."""

    id: Optional[int] = None
    units: Optional[ProductUnit] = None
    category: Optional[ProductCategoryRef] = None
    supplier: Optional[ProductSupplier] = None
    created_at: Timestamp = None
    modified_at: Timestamp = None


class ProductCreate(_ProductFields):
    """Payload for ``POST /products``. The spec requires ``name`` and ``category``.

    ``units``, ``category`` and ``supplier`` reference existing objects by id::

        ProductCreate(name="Coffee", sales_price=49.0, category=IdRef(id=12))
    """

    name: str
    units: Optional[IdRef] = None
    category: Optional[IdRef] = None
    supplier: Optional[IdRef] = None


class ProductUpdate(_ProductFields):
    """Payload for ``PATCH /products/{id}``. Only fields you set are sent."""

    units: Optional[IdRef] = None
    category: Optional[IdRef] = None
    supplier: Optional[IdRef] = None


class ProductDimension(Py24soModel):
    dimension_type: Optional[int] = None
    dimension_type_name: Optional[str] = None
    value: Optional[str] = None
    name: Optional[str] = None


class ProductSalesTypeOverride(Py24soModel):
    """Overrides the revenue account used for a product with a given sales type."""

    product_id: Optional[int] = None
    sales_type_id: Optional[int] = None
    account_number: Optional[int] = None


class ProductCategory(Py24soModel):
    id: Optional[int] = None
    name: Optional[str] = None
    alternative_reference: Optional[str] = None
    parent_id: Optional[int] = None
    modified_at: Timestamp = None


class ProductCategoryCreate(Py24soModel):
    """Payload for ``POST /productcategories``. ``parent_id=0`` means top level."""

    name: str
    alternative_reference: Optional[str] = None
    parent_id: Optional[int] = None


class ProductCategoryUpdate(Py24soModel):
    """Payload for ``PATCH /productcategories/{id}``. Only fields you set are sent."""

    name: Optional[str] = None
    alternative_reference: Optional[str] = None
    parent_id: Optional[int] = None


class PriceList(Py24soModel):
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    currency_code: Optional[str] = None
    is_inclusive_tax: Optional[bool] = None


class PriceListPrice(Py24soModel):
    product_id: Optional[int] = None
    price: Optional[float] = None
