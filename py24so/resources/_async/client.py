from typing import Any, Mapping, Optional, Union

import httpx

from py24so._client import AsyncAPIClient
from py24so._options import ClientOptions
from py24so.resources._async.accounting import (
    AsyncAccountBalances,
    AsyncAccounts,
    AsyncCurrencies,
    AsyncDimensions,
    AsyncFiscalPeriods,
    AsyncTaxes,
    AsyncTransactionLines,
    AsyncTransactions,
    AsyncTransactionTypes,
)
from py24so.resources._async.bank import AsyncBankAccounts, AsyncBankTransactions
from py24so.resources._async.customers import AsyncCustomers
from py24so.resources._async.files import AsyncDocuments, AsyncFiles
from py24so.resources._async.organization import AsyncMe, AsyncOrganizationResource
from py24so.resources._async.products import (
    AsyncPriceLists,
    AsyncProductCategories,
    AsyncProducts,
    AsyncProductUnits,
)
from py24so.resources._async.sales_orders import (
    AsyncPaymentMethods,
    AsyncSalesOrders,
    AsyncSalesTypes,
)


class AsyncClient24SO:
    """Client for the 24SevenOffice REST API.

    Credentials default to the ``PY24SO_CLIENT_ID``, ``PY24SO_CLIENT_SECRET`` and
    ``PY24SO_ORGANIZATION_ID`` environment variables. Use it as a context manager
    (or call :meth:`close`) to release connections::

        async with AsyncClient24SO(client_id, client_secret, organization_id) as client:
            async for customer in client.customers.list(is_company=True):
                print(customer.name)

    Args:
        client_id: OAuth client id of your application.
        client_secret: OAuth client secret of your application.
        organization_id: The client organization to act on (``login_organization``).
        options: Timeouts, retries, rate limiting and other settings.
        http_client: Bring your own ``httpx.AsyncClient`` (for custom transports,
            proxies or testing). It is not closed by :meth:`close`.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        organization_id: Optional[Union[str, int]] = None,
        options: Optional[ClientOptions] = None,
        *,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self._client = AsyncAPIClient(
            client_id, client_secret, organization_id, options, http_client=http_client
        )

        # Sales
        self.customers = AsyncCustomers(self._client)
        self.sales_orders = AsyncSalesOrders(self._client)
        self.sales_types = AsyncSalesTypes(self._client)
        self.payment_methods = AsyncPaymentMethods(self._client)
        # Products
        self.products = AsyncProducts(self._client)
        self.product_categories = AsyncProductCategories(self._client)
        self.product_units = AsyncProductUnits(self._client)
        self.price_lists = AsyncPriceLists(self._client)
        # Accounting
        self.accounts = AsyncAccounts(self._client)
        self.account_balances = AsyncAccountBalances(self._client)
        self.currencies = AsyncCurrencies(self._client)
        self.taxes = AsyncTaxes(self._client)
        self.fiscal_periods = AsyncFiscalPeriods(self._client)
        self.transaction_lines = AsyncTransactionLines(self._client)
        self.transactions = AsyncTransactions(self._client)
        self.transaction_types = AsyncTransactionTypes(self._client)
        self.dimensions = AsyncDimensions(self._client)
        # Bank
        self.bank_accounts = AsyncBankAccounts(self._client)
        self.bank_transactions = AsyncBankTransactions(self._client)
        # Documents & files
        self.files = AsyncFiles(self._client)
        self.documents = AsyncDocuments(self._client)
        # Organization & user
        self.organization = AsyncOrganizationResource(self._client)
        self.me = AsyncMe(self._client)

    @property
    def options(self) -> ClientOptions:
        return self._client.options

    @property
    def organization_id(self) -> str:
        return self._client.organization_id

    async def get_access_token(self) -> str:
        """Return a valid access token, fetching or refreshing it if needed."""
        return await self._client.get_access_token()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        """Call any endpoint directly and get the decoded JSON back.

        Useful for endpoints this library does not wrap yet. Authentication,
        retries and error handling work exactly as for the typed methods::

            data = await client.request("GET", "/customers", params={"limit": 5})
        """
        return await self._client.request(method, path, params=params, json=json, headers=headers)

    async def close(self) -> None:
        """Close network connections. Safe to call more than once."""
        await self._client.close()

    async def __aenter__(self) -> "AsyncClient24SO":
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.close()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(organization_id={self.organization_id!r})"
