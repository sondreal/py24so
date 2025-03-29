"""Endpoints for the 24SevenOffice API client."""

from py24so.endpoints.customers import AsyncCustomerEndpoint, CustomerEndpoint
from py24so.endpoints.invoices import AsyncInvoiceEndpoint, InvoiceEndpoint
from py24so.endpoints.product_categories import AsyncProductCategoryEndpoint, ProductCategoryEndpoint
from py24so.endpoints.products import AsyncProductEndpoint, ProductEndpoint

__all__ = [
    "CustomerEndpoint",
    "AsyncCustomerEndpoint",
    "InvoiceEndpoint",
    "AsyncInvoiceEndpoint",
    "ProductEndpoint",
    "AsyncProductEndpoint",
    "ProductCategoryEndpoint",
    "AsyncProductCategoryEndpoint",
]
