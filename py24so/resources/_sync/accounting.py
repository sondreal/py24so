# AUTO-GENERATED from py24so/resources/_async by scripts/unasync.py. DO NOT EDIT.

from datetime import date, datetime
from typing import Any, Iterable, List, Mapping, Optional, Union

from py24so._client import APIClient
from py24so._pagination import Paginator
from py24so._utils import path_param, serialize_body
from py24so.models.accounting import (
    Account,
    AccountBalance,
    Currency,
    Dimension,
    DimensionElement,
    FiscalPeriod,
    Tax,
    TransactionCreate,
    TransactionCreated,
    TransactionLine,
    TransactionType,
)
from py24so.resources._sync._resource import Resource

_DEFAULT_TRANSACTION_LINES_PAGE_SIZE = 50


class Accounts(Resource):
    """``/accounts``: the chart of accounts."""

    def list(self, *, query: Optional[str] = None) -> List[Account]:
        """List accounts, optionally filtered by a search ``query``."""
        response = self._client.send("GET", "/accounts", params={"query": query})
        return self._client.parse_list(response, Account)

    def get(self, account_id: Union[int, str]) -> Account:
        return self._client.request("GET", f"/accounts/{path_param(account_id)}", cast_to=Account)


class AccountBalances(Resource):
    """``/accountbalances``: opening/closing balances per account."""

    def list(
        self,
        *,
        date_from: Union[date, str],
        date_to: Union[date, str],
        account_id: Optional[Union[int, str]] = None,
        periods: Optional[Iterable[Union[date, str]]] = None,
        type: Optional[str] = None,
        keep_incoming: Optional[bool] = None,
    ) -> List[AccountBalance]:
        """Get balances for all accounts, or a single account when ``account_id`` is given.

        Args:
            date_from: Start of the reporting range (inclusive).
            date_to: End of the reporting range (inclusive).
            account_id: Only this account.
            periods: Break the balances down at these dates.
            type: A :class:`~py24so.models.BalanceType`: ``"Date"`` (default) or ``"Period"``.
            keep_incoming: Keep the incoming balance when aggregating periods.
        """
        path = "/accountbalances"
        if account_id is not None:
            path = f"{path}/{path_param(account_id)}"
        response = self._client.send(
            "GET",
            path,
            params={
                "dateFrom": date_from,
                "dateTo": date_to,
                "periods": list(periods) if periods is not None else None,
                "type": type,
                "keepIncoming": keep_incoming,
            },
        )
        return self._client.parse_list(response, AccountBalance)


class Currencies(Resource):
    """``/currencies``"""

    def list(self) -> List[Currency]:
        response = self._client.send("GET", "/currencies")
        return self._client.parse_list(response, Currency)


class Taxes(Resource):
    """``/taxes``: VAT codes."""

    def list(self) -> List[Tax]:
        response = self._client.send("GET", "/taxes")
        return self._client.parse_list(response, Tax)

    def get(self, tax_id: Union[int, str]) -> Tax:
        return self._client.request("GET", f"/taxes/{path_param(tax_id)}", cast_to=Tax)


class FiscalPeriods(Resource):
    """``/fiscalperiods``"""

    def list(self, *, type: Optional[str] = None) -> List[FiscalPeriod]:
        """List fiscal years and/or periods.

        Args:
            type: A :class:`~py24so.models.FiscalPeriodType`: ``"Year"`` (API default),
                ``"Period"`` or ``"All"``.
        """
        response = self._client.send("GET", "/fiscalperiods", params={"type": type})
        return self._client.parse_list(response, FiscalPeriod)


class TransactionLines(Resource):
    """``/transactionlines``: posted general ledger lines."""

    def list(
        self,
        *,
        date_from: Union[date, str],
        date_to: Union[date, str],
        created_from: Optional[Union[datetime, str]] = None,
        created_after: Optional[Union[datetime, str]] = None,
        modified_from: Optional[Union[datetime, str]] = None,
        modified_after: Optional[Union[datetime, str]] = None,
        transaction_id: Optional[str] = None,
        transaction_number: Optional[int] = None,
        transaction_type_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        account_id: Optional[int] = None,
        account_number: Optional[int] = None,
        invoice_number: Optional[str] = None,
        currency_code: Optional[str] = None,
        include_dimensions: Optional[bool] = None,
        page_size: Optional[int] = None,
        start_page: Optional[int] = None,
        extra_params: Optional[Mapping[str, Any]] = None,
    ) -> Paginator[TransactionLine]:
        """Iterate over transaction lines in a date range, following pagination automatically.

        Args:
            date_from: First transaction date (inclusive).
            date_to: Last transaction date (inclusive).
            created_from: Created at or after this time.
            created_after: Created strictly after this time.
            modified_from: Modified at or after this time.
            modified_after: Modified strictly after this time.
            transaction_id: Only lines of this transaction (voucher) id.
            transaction_number: Only lines of this transaction (voucher) number.
            transaction_type_id: Only lines of this transaction type.
            customer_id: Only lines for this customer.
            account_id: Only lines on this account id.
            account_number: Only lines on this account number.
            invoice_number: Only lines with this invoice number.
            currency_code: Only lines in this currency.
            include_dimensions: Include dimension values on each line.
            page_size: Lines per request (the API's ``limit``, default 50).
            start_page: Page to start from (default 1).
            extra_params: Additional raw query parameters.
        """
        params = {
            "dateFrom": date_from,
            "dateTo": date_to,
            "createdFrom": created_from,
            "createdAfter": created_after,
            "modifiedFrom": modified_from,
            "modifiedAfter": modified_after,
            "transactionId": transaction_id,
            "transactionNumber": transaction_number,
            "transactionTypeId": transaction_type_id,
            "customerId": customer_id,
            "accountId": account_id,
            "accountNumber": account_number,
            "invoiceNumber": invoice_number,
            "currencyCode": currency_code,
            "includeDimensions": include_dimensions,
            "limit": page_size,
            "page": start_page,
            **(extra_params or {}),
        }
        return self._client.paginate(
            "/transactionlines",
            TransactionLine,
            params,
            page_param="page",
            page_size=page_size or _DEFAULT_TRANSACTION_LINES_PAGE_SIZE,
        )

    def get(self, line_id: str) -> TransactionLine:
        return self._client.request(
            "GET", f"/transactionlines/{path_param(line_id)}", cast_to=TransactionLine
        )


class Transactions(Resource):
    """``/transactions``: register vouchers in the general ledger."""

    def create(
        self, transaction: Union[TransactionCreate, Mapping[str, Any]]
    ) -> TransactionCreated:
        """Register a voucher. The line amounts must balance to zero."""
        return self._client.request(
            "POST",
            "/transactions",
            json=serialize_body(transaction, TransactionCreate),
            cast_to=TransactionCreated,
        )


class TransactionTypes(Resource):
    """``/transactiontypes``"""

    def list(self) -> List[TransactionType]:
        response = self._client.send("GET", "/transactiontypes")
        return self._client.parse_list(response, TransactionType)


class DimensionElements(Resource):
    """``/dimensions/{dimensionType}/elements``"""

    def list(
        self,
        dimension_type: Union[int, str],
        *,
        page_size: Optional[int] = None,
        extra_params: Optional[Mapping[str, Any]] = None,
    ) -> Paginator[DimensionElement]:
        """Iterate over the active elements of a dimension, following pagination automatically."""
        return self._client.paginate(
            f"/dimensions/{path_param(dimension_type)}/elements",
            DimensionElement,
            {"limit": page_size, **(extra_params or {})},
        )

    def get(self, dimension_type: Union[int, str], value: str) -> DimensionElement:
        return self._client.request(
            "GET",
            f"/dimensions/{path_param(dimension_type)}/elements/{path_param(value)}",
            cast_to=DimensionElement,
        )


class Dimensions(Resource):
    """``/dimensions``: department, project and custom dimensions."""

    def __init__(self, client: APIClient) -> None:
        super().__init__(client)
        self.elements = DimensionElements(client)

    def list(self) -> List[Dimension]:
        response = self._client.send("GET", "/dimensions")
        return self._client.parse_list(response, Dimension)

    def get(self, dimension_type: Union[int, str]) -> Dimension:
        return self._client.request(
            "GET", f"/dimensions/{path_param(dimension_type)}", cast_to=Dimension
        )
