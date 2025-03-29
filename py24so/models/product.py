from datetime import datetime
from typing import Dict, List, Optional, Union, Any

from pydantic import BaseModel, Field


class PriceInfo(BaseModel):
    """Product price information model."""
    
    price: float
    currency: str = "NOK"
    vat_rate: Optional[float] = None
    discount: Optional[float] = None
    unit: Optional[str] = None


class StockInfo(BaseModel):
    """Product stock information model."""
    
    quantity: int = 0
    reorder_point: Optional[int] = None
    location: Optional[str] = None


class ProductBase(BaseModel):
    """Base model for product data."""
    
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    price_info: Optional[PriceInfo] = None
    stock_info: Optional[StockInfo] = None
    tax_code: Optional[str] = None
    is_service: bool = False
    is_active: bool = True
    custom_fields: Optional[Dict[str, Union[str, int, float, bool, None]]] = None


class ProductCreate(ProductBase):
    """Model for creating a new product."""
    
    pass


class ProductUpdate(BaseModel):
    """Model for updating an existing product."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    price_info: Optional[PriceInfo] = None
    stock_info: Optional[StockInfo] = None
    tax_code: Optional[str] = None
    is_service: Optional[bool] = None
    is_active: Optional[bool] = None
    custom_fields: Optional[Dict[str, Union[str, int, float, bool, None]]] = None


class Product(ProductBase):
    """Product model with additional read-only fields."""
    
    id: str = Field(..., description="Unique product ID")
    created_at: datetime
    updated_at: datetime 