from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ProductCategory(BaseModel):
    """
    Model representing a product category in the 24SevenOffice API.
    """

    id: str = Field(..., description="The unique identifier for the product category")
    name: str = Field(..., description="The name of the product category")
    parent_id: Optional[int] = Field(
        0, alias="parentId", description="The ID of the parent category"
    )
    alternative_reference: Optional[str] = Field(
        None, alias="alternativeReference", description="An alternative reference for the category"
    )
    modified_at: Optional[str] = Field(
        None, alias="modifiedAt", description="Timestamp when the category was last modified"
    )


class ProductCategoryCreate(BaseModel):
    """
    Model for creating a new product category.
    """

    name: str = Field(..., description="The name of the product category")
    parent_id: Optional[str] = Field(
        "0", alias="parentId", description="The ID of the parent category"
    )
    alternative_reference: Optional[str] = Field(
        None, alias="alternativeReference", description="An alternative reference for the category"
    )


class ProductCategoryUpdate(BaseModel):
    """
    Model for updating an existing product category.
    """

    name: Optional[str] = Field(None, description="The name of the product category")
    parent_id: Optional[str] = Field(
        None, alias="parentId", description="The ID of the parent category"
    )
    alternative_reference: Optional[str] = Field(
        None, alias="alternativeReference", description="An alternative reference for the category"
    )
