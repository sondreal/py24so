from typing import List, Optional, Union

from py24so._client import AsyncAPIClient
from py24so._utils import path_param
from py24so.models.organization import (
    Identifier,
    License,
    LicenseOrganization,
    Organization,
    Person,
    Profile,
)
from py24so.resources._async._resource import AsyncResource


class AsyncIdentifiers(AsyncResource):
    """``/me/identifiers``: e-mail addresses and phone numbers of the current user."""

    async def list(
        self, *, type: Optional[str] = None, status: Optional[str] = None
    ) -> List[Identifier]:
        response = await self._client.send(
            "GET", "/me/identifiers", params={"type": type, "status": status}
        )
        return self._client.parse_list(response, Identifier)

    async def get(self, identifier_id: str) -> Identifier:
        return await self._client.request(
            "GET", f"/me/identifiers/{path_param(identifier_id)}", cast_to=Identifier
        )


class AsyncLicenses(AsyncResource):
    """``/me/licenses``: the organizations the current user has access to."""

    async def list(
        self, *, organization_id: Optional[int] = None, person_id: Optional[int] = None
    ) -> List[License]:
        response = await self._client.send(
            "GET",
            "/me/licenses",
            params={"organizationId": organization_id, "personId": person_id},
        )
        return self._client.parse_list(response, License)

    async def organization(self, license_id: str) -> LicenseOrganization:
        """Get the organization a license belongs to."""
        return await self._client.request(
            "GET",
            f"/me/licenses/{path_param(license_id)}/organization",
            cast_to=LicenseOrganization,
        )


class AsyncMe(AsyncResource):
    """``/me``: the user the access token was issued for."""

    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.identifiers = AsyncIdentifiers(client)
        self.licenses = AsyncLicenses(client)

    async def get(
        self,
        *,
        thumb: Optional[bool] = None,
        bigthumb: Optional[bool] = None,
        max_age: Optional[int] = None,
    ) -> Profile:
        return await self._client.request(
            "GET",
            "/me",
            params={"thumb": thumb, "bigthumb": bigthumb, "maxAge": max_age},
            cast_to=Profile,
        )


class AsyncPeople(AsyncResource):
    """``/organization/people``"""

    async def list(self, *, person_type: Optional[str] = None) -> List[Person]:
        """List people. ``person_type`` is a :class:`~py24so.models.PersonType`."""
        response = await self._client.send(
            "GET", "/organization/people", params={"personType": person_type}
        )
        return self._client.parse_list(response, Person)

    async def get(self, person_id: Union[int, str], *, person_type: Optional[str] = None) -> Person:
        return await self._client.request(
            "GET",
            f"/organization/people/{path_param(person_id)}",
            params={"personType": person_type},
            cast_to=Person,
        )


class AsyncOrganizationResource(AsyncResource):
    """``/organization``: the organization (client) the access token belongs to."""

    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.people = AsyncPeople(client)

    async def get(self) -> Organization:
        """Get the organization's name, address, settings and contact details."""
        return await self._client.request("GET", "/organization/information", cast_to=Organization)
