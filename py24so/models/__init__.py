"""Models for the 24SevenOffice API client."""

from py24so.models.config import ClientOptions
from py24so.models.customer import (
    Address,
    Contact,
    Customer,
    CustomerBase,
    CustomerCreate,
    CustomerUpdate,
)
from py24so.models.invoice import (
    Invoice,
    InvoiceBase,
    InvoiceCreate,
    InvoiceLineItem,
    InvoiceStatus,
    InvoiceTotals,
    InvoiceUpdate,
)
from py24so.models.product import (
    PriceInfo,
    Product,
    ProductBase,
    ProductCreate,
    ProductUpdate,
    StockInfo,
)
from py24so.models.product_category import (
    ProductCategory,
    ProductCategoryCreate,
    ProductCategoryUpdate,
)

__all__ = [
    "ClientOptions",
    # Customer models
    "Address",
    "Contact",
    "Customer",
    "CustomerBase",
    "CustomerCreate",
    "CustomerUpdate",
    # Invoice models
    "Invoice",
    "InvoiceBase",
    "InvoiceCreate",
    "InvoiceUpdate",
    "InvoiceLineItem",
    "InvoiceStatus",
    "InvoiceTotals",
    # Product models
    "Product",
    "ProductBase",
    "ProductCreate",
    "ProductUpdate",
    "PriceInfo",
    "StockInfo",
    # Product Category models
    "ProductCategory",
    "ProductCategoryCreate",
    "ProductCategoryUpdate",
]
