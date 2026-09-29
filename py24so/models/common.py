from typing import Optional

from py24so.models._base import Py24soModel


class IdRef(Py24soModel):
    """A reference to another object by id, e.g. ``{"id": 3}``."""

    id: Optional[int] = None


class NumberRef(Py24soModel):
    """A reference to another object by number, e.g. ``{"number": 1920}``."""

    number: Optional[int] = None


class CurrencyCode(Py24soModel):
    """A currency given only by its ISO 4217 code, e.g. ``{"code": "NOK"}``."""

    code: Optional[str] = None


class DimensionValue(Py24soModel):
    """A dimension (department, project, ...) value attached to an object."""

    dimension_type: Optional[int] = None
    value: Optional[str] = None
    name: Optional[str] = None
    dimension_type_name: Optional[str] = None
