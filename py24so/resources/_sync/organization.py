# AUTO-GENERATED from py24so/resources/_async by scripts/unasync.py. DO NOT EDIT.

from typing import List, Optional, Union

from py24so._client import APIClient
from py24so._utils import path_param
from py24so.models.organization import (
    Identifier,
    License,
    LicenseOrganization,
    Organization,
    Person,
    Profile,
)
from py24so.resources._sync._resource import Resource


class Identifiers(Resource):
    """``/me/identifiers``: e-mail addresses and phone numbers of the current user."""

    def list(self, *, type: Optional[str] = None, status: Optional[str] = None) -> List[Identifier]:
        response = self._client.send(
            "GET", "/me/identifiers", params={"type": type, "status": status}
        )
        return self._client.parse_list(response, Identifier)

    def get(self, identifier_id: str) -> Identifier:
        return self._client.request(
            "GET", f"/me/identifiers/{path_param(identifier_id)}", cast_to=Identifier
        )


class Licenses(Resource):
    """``/me/licenses``: the organizations the current user has access to."""

    def list(
        self, *, organization_id: Optional[int] = None, person_id: Optional[int] = None
    ) -> List[License]:
        response = self._client.send(
            "GET",
            "/me/licenses",
            params={"organizationId": organization_id, "personId": person_id},
        )
        return self._client.parse_list(response, License)

    def organization(self, license_id: str) -> LicenseOrganization:
        """Get the organization a license belongs to."""
        return self._client.request(
            "GET",
            f"/me/licenses/{path_param(license_id)}/organization",
            cast_to=LicenseOrganization,
        )


class Me(Resource):
    """``/me``: the user the access token was issued for."""

    def __init__(self, client: APIClient) -> None:
        super().__init__(client)
        self.identifiers = Identifiers(client)
        self.licenses = Licenses(client)

    def get(
        self,
        *,
        thumb: Optional[bool] = None,
        bigthumb: Optional[bool] = None,
        max_age: Optional[int] = None,
    ) -> Profile:
        return self._client.request(
            "GET",
            "/me",
            params={"thumb": thumb, "bigthumb": bigthumb, "maxAge": max_age},
            cast_to=Profile,
        )


class People(Resource):
    """``/organization/people``"""

    def list(self, *, person_type: Optional[str] = None) -> List[Person]:
        """List people. ``person_type`` is a :class:`~py24so.models.PersonType`."""
        response = self._client.send(
            "GET", "/organization/people", params={"personType": person_type}
        )
        return self._client.parse_list(response, Person)

    def get(self, person_id: Union[int, str], *, person_type: Optional[str] = None) -> Person:
        return self._client.request(
            "GET",
            f"/organization/people/{path_param(person_id)}",
            params={"personType": person_type},
            cast_to=Person,
        )


class OrganizationResource(Resource):
    """``/organization``: the organization (client) the access token belongs to."""

    def __init__(self, client: APIClient) -> None:
        super().__init__(client)
        self.people = People(client)

    def get(self) -> Organization:
        """Get the organization's name, address, settings and contact details."""
        return self._client.request("GET", "/organization/information", cast_to=Organization)
