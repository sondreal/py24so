from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, EmailStr, Field


class Address(BaseModel):
    """Customer address model."""

    street: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    type: Optional[str] = None  # "Shipping", "Billing", etc.


class Contact(BaseModel):
    """Customer contact person model."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    position: Optional[str] = None


class CustomerBase(BaseModel):
    """Base model for customer data."""

    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    tax_id: Optional[str] = None
    notes: Optional[str] = None
    customer_number: Optional[str] = None
    currency: Optional[str] = "NOK"
    payment_terms: Optional[int] = None  # Days
    addresses: Optional[List[Address]] = None
    contacts: Optional[List[Contact]] = None
    custom_fields: Optional[Dict[str, Union[str, int, float, bool, None]]] = None


class CustomerCreate(CustomerBase):
    """Model for creating a new customer."""

    pass


class CustomerUpdate(BaseModel):
    """Model for updating an existing customer."""

    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    tax_id: Optional[str] = None
    notes: Optional[str] = None
    currency: Optional[str] = None
    payment_terms: Optional[int] = None
    addresses: Optional[List[Address]] = None
    contacts: Optional[List[Contact]] = None
    custom_fields: Optional[Dict[str, Union[str, int, float, bool, None]]] = None


class Customer(CustomerBase):
    """Customer model with additional read-only fields."""

    id: str = Field(..., description="Unique customer ID")
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
