# AUTO-GENERATED from py24so/resources/_async by scripts/unasync.py. DO NOT EDIT.

from typing import Any, Mapping, Optional, Union

import httpx

from py24so._client import APIClient
from py24so._options import ClientOptions
from py24so.resources._sync.accounting import (
    AccountBalances,
    Accounts,
    Currencies,
    Dimensions,
    FiscalPeriods,
    Taxes,
    TransactionLines,
    Transactions,
    TransactionTypes,
)
from py24so.resources._sync.bank import BankAccounts, BankTransactions
from py24so.resources._sync.customers import Customers
from py24so.resources._sync.files import Documents, Files
from py24so.resources._sync.organization import Me, OrganizationResource
from py24so.resources._sync.products import (
    PriceLists,
    ProductCategories,
    Products,
    ProductUnits,
)
from py24so.resources._sync.sales_orders import (
    PaymentMethods,
    SalesOrders,
    SalesTypes,
)


class Client24SO:
    """Client for the 24SevenOffice REST API.

    Credentials default to the ``PY24SO_CLIENT_ID``, ``PY24SO_CLIENT_SECRET`` and
    ``PY24SO_ORGANIZATION_ID`` environment variables. Use it as a context manager
    (or call :meth:`close`) to release connections::

        with Client24SO(client_id, client_secret, organization_id) as client:
            for customer in client.customers.list(is_company=True):
                print(customer.name)

    Args:
        client_id: OAuth client id of your application.
        client_secret: OAuth client secret of your application.
        organization_id: The client organization to act on (``login_organization``).
        options: Timeouts, retries, rate limiting and other settings.
        http_client: Bring your own ``httpx.Client`` (for custom transports,
            proxies or testing). It is not closed by :meth:`close`.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        organization_id: Optional[Union[str, int]] = None,
        options: Optional[ClientOptions] = None,
        *,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self._client = APIClient(
            client_id, client_secret, organization_id, options, http_client=http_client
        )

        # Sales
        self.customers = Customers(self._client)
        self.sales_orders = SalesOrders(self._client)
        self.sales_types = SalesTypes(self._client)
        self.payment_methods = PaymentMethods(self._client)
        # Products
        self.products = Products(self._client)
        self.product_categories = ProductCategories(self._client)
        self.product_units = ProductUnits(self._client)
        self.price_lists = PriceLists(self._client)
        # Accounting
        self.accounts = Accounts(self._client)
        self.account_balances = AccountBalances(self._client)
        self.currencies = Currencies(self._client)
        self.taxes = Taxes(self._client)
        self.fiscal_periods = FiscalPeriods(self._client)
        self.transaction_lines = TransactionLines(self._client)
        self.transactions = Transactions(self._client)
        self.transaction_types = TransactionTypes(self._client)
        self.dimensions = Dimensions(self._client)
        # Bank
        self.bank_accounts = BankAccounts(self._client)
        self.bank_transactions = BankTransactions(self._client)
        # Documents & files
        self.files = Files(self._client)
        self.documents = Documents(self._client)
        # Organization & user
        self.organization = OrganizationResource(self._client)
        self.me = Me(self._client)

    @property
    def options(self) -> ClientOptions:
        return self._client.options

    @property
    def organization_id(self) -> str:
        return self._client.organization_id

    def get_access_token(self) -> str:
        """Return a valid access token, fetching or refreshing it if needed."""
        return self._client.get_access_token()

    def request(
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

            data = client.request("GET", "/customers", params={"limit": 5})
        """
        return self._client.request(method, path, params=params, json=json, headers=headers)

    def close(self) -> None:
        """Close network connections. Safe to call more than once."""
        self._client.close()

    def __enter__(self) -> "Client24SO":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(organization_id={self.organization_id!r})"
