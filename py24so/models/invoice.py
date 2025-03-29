from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class InvoiceStatus(str, Enum):
    """Invoice status enum."""

    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"
    CREDITED = "CREDITED"


class InvoiceLineItem(BaseModel):
    """Invoice line item model."""

    description: str
    quantity: float
    unit_price: float
    vat_rate: Optional[float] = None
    discount: Optional[float] = None
    product_id: Optional[str] = None
    unit: Optional[str] = None
    line_total: Optional[float] = None  # Calculated field
    custom_fields: Optional[Dict[str, Union[str, int, float, bool, None]]] = None


class InvoiceBase(BaseModel):
    """Base model for invoice data."""

    customer_id: str
    invoice_date: date = Field(default_factory=date.today)
    due_date: Optional[date] = None
    line_items: List[InvoiceLineItem]
    notes: Optional[str] = None
    payment_terms: Optional[int] = None  # Days
    currency: str = "NOK"
    reference: Optional[str] = None
    status: InvoiceStatus = InvoiceStatus.DRAFT
    custom_fields: Optional[Dict[str, Union[str, int, float, bool, None]]] = None


class InvoiceCreate(InvoiceBase):
    """Model for creating a new invoice."""

    pass


class InvoiceUpdate(BaseModel):
    """Model for updating an existing invoice."""

    customer_id: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    line_items: Optional[List[InvoiceLineItem]] = None
    notes: Optional[str] = None
    payment_terms: Optional[int] = None
    currency: Optional[str] = None
    reference: Optional[str] = None
    status: Optional[InvoiceStatus] = None
    custom_fields: Optional[Dict[str, Union[str, int, float, bool, None]]] = None


class InvoiceTotals(BaseModel):
    """Invoice totals model."""

    subtotal: float
    vat_amount: float
    discount_amount: Optional[float] = None
    total: float


class Invoice(InvoiceBase):
    """Invoice model with additional read-only fields."""

    id: str = Field(..., description="Unique invoice ID")
    invoice_number: str
    created_at: datetime
    updated_at: datetime
    totals: InvoiceTotals
    payment_date: Optional[date] = None
    is_credit_note: bool = False
    credited_invoice_id: Optional[str] = None
