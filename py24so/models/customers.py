from enum import Enum
from typing import Optional

from pydantic import model_validator

from py24so.models._base import Py24soModel, Timestamp


class Address(Py24soModel):
    """A postal address. ``name`` is only used for billing and delivery addresses."""

    name: Optional[str] = None
    street: Optional[str] = None
    postal_code: Optional[str] = None
    postal_area: Optional[str] = None
    country_subdivision: Optional[str] = None
    country_code: Optional[str] = None


class CustomerAddresses(Py24soModel):
    visit: Optional[Address] = None
    postal: Optional[Address] = None
    billing: Optional[Address] = None
    delivery: Optional[Address] = None


class CustomerEmail(Py24soModel):
    contact: Optional[str] = None
    billing: Optional[str] = None


class CustomerPerson(Py24soModel):
    """Name of a customer that is a private person (``is_company=False``)."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None


class Customer(Py24soModel):
    """A customer (or supplier) in the CRM."""

    id: Optional[int] = None
    name: Optional[str] = None
    external_reference: Optional[str] = None
    pricelist_id: Optional[int] = None
    person: Optional[CustomerPerson] = None
    is_company: Optional[bool] = None
    is_supplier: Optional[bool] = None
    organization_number: Optional[str] = None
    address: Optional[CustomerAddresses] = None
    email: Optional[CustomerEmail] = None
    phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    note: Optional[str] = None
    created_at: Timestamp = None
    modified_at: Timestamp = None


class _CustomerWritable(Py24soModel):
    external_reference: Optional[str] = None
    is_supplier: Optional[bool] = None
    address: Optional[CustomerAddresses] = None
    email: Optional[CustomerEmail] = None
    phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    note: Optional[str] = None


class CustomerCreate(_CustomerWritable):
    """Payload for ``POST /customers``.

    A company needs ``is_company=True`` and a ``name``; a private person needs
    ``is_company=False`` and a ``person``::

        CustomerCreate(is_company=True, name="Acme AS", organization_number="999999999")
        CustomerCreate(is_company=False, person=CustomerPerson(first_name="Kari", last_name="Nordmann"))
    """

    is_company: bool
    name: Optional[str] = None
    organization_number: Optional[str] = None
    person: Optional[CustomerPerson] = None
    id: Optional[int] = None

    @model_validator(mode="after")
    def _check_kind(self) -> "CustomerCreate":
        if self.is_company and not self.name:
            raise ValueError("a company customer (is_company=True) requires a name")
        if not self.is_company and self.person is None:
            raise ValueError("a person customer (is_company=False) requires person")
        return self


class CustomerUpdate(_CustomerWritable):
    """Payload for ``PATCH /customers/{id}``. Only fields you set are sent."""

    name: Optional[str] = None
    organization_number: Optional[str] = None
    person: Optional[CustomerPerson] = None


class BankAccountType(str, Enum):
    BBAN = "bban"
    IBAN = "iban"
    BANKGIRO = "bankgiro"
    PLUSGIRO = "plusgiro"


class CustomerBankAccount(Py24soModel):
    """A bank account belonging to a customer or supplier.

    ``type`` is one of :class:`BankAccountType`.
    """

    number: Optional[str] = None
    type: Optional[str] = None
    is_default: Optional[bool] = None
    name: Optional[str] = None
    country_code: Optional[str] = None
    address: Optional[str] = None
    bsc: Optional[str] = None
    bic: Optional[str] = None


class CustomerSortField(str, Enum):
    """Fields accepted by ``customers.list(sort_by=...)``."""

    NAME = "name"
    CREATED_AT = "createdAt"
    MODIFIED_AT = "modifiedAt"
    ORGANIZATION_NUMBER = "organizationNumber"
    ID = "id"
