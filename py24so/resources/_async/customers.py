from datetime import date, datetime
from typing import Any, List, Mapping, Optional, Union

from py24so._client import AsyncAPIClient
from py24so._pagination import AsyncPaginator
from py24so._utils import path_param, serialize_body
from py24so.models.customers import (
    Customer,
    CustomerBankAccount,
    CustomerCreate,
    CustomerUpdate,
)
from py24so.resources._async._resource import AsyncResource


class AsyncCustomerBankAccounts(AsyncResource):
    """``/customers/{customerId}/bankaccounts``"""

    async def list(self, customer_id: Union[int, str]) -> List[CustomerBankAccount]:
        """List the bank accounts registered on a customer."""
        response = await self._client.send(
            "GET", f"/customers/{path_param(customer_id)}/bankaccounts"
        )
        return self._client.parse_list(response, CustomerBankAccount)

    async def get(self, customer_id: Union[int, str], account_number: str) -> CustomerBankAccount:
        """Get one of a customer's bank accounts by account number."""
        return await self._client.request(
            "GET",
            f"/customers/{path_param(customer_id)}/bankaccounts/{path_param(account_number)}",
            cast_to=CustomerBankAccount,
        )

    async def create(
        self,
        customer_id: Union[int, str],
        bank_account: Union[CustomerBankAccount, Mapping[str, Any]],
    ) -> CustomerBankAccount:
        """Add a bank account to a customer (``number``, ``type`` and ``is_default`` are required)."""
        return await self._client.request(
            "POST",
            f"/customers/{path_param(customer_id)}/bankaccounts",
            json=serialize_body(bank_account, CustomerBankAccount),
            cast_to=CustomerBankAccount,
        )

    async def update(
        self,
        customer_id: Union[int, str],
        account_number: str,
        bank_account: Union[CustomerBankAccount, Mapping[str, Any]],
    ) -> CustomerBankAccount:
        """Update one of a customer's bank accounts."""
        return await self._client.request(
            "PATCH",
            f"/customers/{path_param(customer_id)}/bankaccounts/{path_param(account_number)}",
            json=serialize_body(bank_account, CustomerBankAccount),
            cast_to=CustomerBankAccount,
        )


class AsyncCustomers(AsyncResource):
    """``/customers``: customers and suppliers in the CRM."""

    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.bank_accounts = AsyncCustomerBankAccounts(client)

    def list(
        self,
        *,
        organization_number: Optional[str] = None,
        is_company: Optional[bool] = None,
        is_supplier: Optional[bool] = None,
        email: Optional[str] = None,
        external_reference: Optional[str] = None,
        modified_from: Optional[Union[datetime, date, str]] = None,
        created_from: Optional[Union[datetime, date, str]] = None,
        sort_by: Optional[str] = None,
        page_size: Optional[int] = None,
        extra_params: Optional[Mapping[str, Any]] = None,
    ) -> AsyncPaginator[Customer]:
        """Iterate over customers, following pagination automatically.

        Args:
            organization_number: Only customers with this organization number.
            is_company: ``True`` for companies, ``False`` for private persons.
            is_supplier: Filter on whether the customer is also a supplier.
            email: Only customers with this e-mail address.
            external_reference: Only customers with this external reference.
            modified_from: Only customers modified at or after this time.
            created_from: Only customers created at or after this time.
            sort_by: ``"<field>:<asc|desc>"`` where field is one of
                :class:`~py24so.models.CustomerSortField`, e.g. ``"name:asc"``.
            page_size: Customers per request (the API's ``limit``, default 25, max 100).
            extra_params: Additional raw query parameters.
        """
        params = {
            "organizationNumber": organization_number,
            "isCompany": is_company,
            "isSupplier": is_supplier,
            "email": email,
            "externalReference": external_reference,
            "modifiedFrom": modified_from,
            "createdFrom": created_from,
            "sortBy": sort_by,
            "limit": page_size,
            **(extra_params or {}),
        }
        return self._client.paginate("/customers", Customer, params)

    async def get(self, customer_id: Union[int, str]) -> Customer:
        """Get a customer by id. Raises :class:`~py24so.NotFoundError` if it does not exist."""
        return await self._client.request(
            "GET", f"/customers/{path_param(customer_id)}", cast_to=Customer
        )

    async def create(self, customer: Union[CustomerCreate, Mapping[str, Any]]) -> Customer:
        """Create a company or private person customer. See :class:`~py24so.models.CustomerCreate`."""
        return await self._client.request(
            "POST",
            "/customers",
            json=serialize_body(customer, CustomerCreate),
            cast_to=Customer,
        )

    async def update(
        self, customer_id: Union[int, str], customer: Union[CustomerUpdate, Mapping[str, Any]]
    ) -> Customer:
        """Update a customer. Only fields that are set on ``customer`` are changed."""
        return await self._client.request(
            "PATCH",
            f"/customers/{path_param(customer_id)}",
            json=serialize_body(customer, CustomerUpdate),
            cast_to=Customer,
        )

    async def delete(self, customer_id: Union[int, str]) -> None:
        """Delete a customer."""
        await self._client.send("DELETE", f"/customers/{path_param(customer_id)}")
