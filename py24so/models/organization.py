from enum import Enum
from typing import Optional

from py24so.models._base import Py24soModel


class Profile(Py24soModel):
    """The user (identity) that the access token was issued for."""

    id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    time_zone: Optional[str] = None
    country_code: Optional[str] = None
    language: Optional[str] = None
    culture: Optional[str] = None


class Identifier(Py24soModel):
    """An e-mail address or phone number attached to the profile."""

    id: Optional[str] = None
    type: Optional[str] = None
    value: Optional[str] = None
    status: Optional[str] = None


class License(Py24soModel):
    id: Optional[str] = None
    name: Optional[str] = None
    organization_id: Optional[int] = None
    identity_id: Optional[str] = None
    person_id: Optional[int] = None


class LicenseOrganization(Py24soModel):
    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None


class OrganizationAddress(Py24soModel):
    street: Optional[str] = None
    city: Optional[str] = None
    postal_area: Optional[str] = None
    postal_code: Optional[str] = None
    country_subdivision: Optional[str] = None
    country_code: Optional[str] = None


class OrganizationSettings(Py24soModel):
    currency_code: Optional[str] = None


class OrganizationContact(Py24soModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    language: Optional[str] = None


class Organization(Py24soModel):
    """The organization (client) the access token belongs to."""

    id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[str] = None
    invoice_email: Optional[str] = None
    address: Optional[OrganizationAddress] = None
    status: Optional[str] = None
    settings: Optional[OrganizationSettings] = None
    contact: Optional[OrganizationContact] = None


class PersonType(str, Enum):
    ORGANIZATION = "Organization"
    EXTERNAL = "External"
    BASIC = "Basic"
    CLIENT = "Client"


class Person(Py24soModel):
    """A person (user or contact) in the organization."""

    id: Optional[int] = None
    identity_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    person_type: Optional[str] = None
    has_license: Optional[bool] = None
