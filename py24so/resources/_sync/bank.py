# AUTO-GENERATED from py24so/resources/_async by scripts/unasync.py. DO NOT EDIT.

from datetime import date
from typing import Any, List, Mapping, Optional, Union

from py24so._pagination import Paginator
from py24so._utils import path_param, serialize_body
from py24so.models.bank import (
    BankAccount,
    BankAccountBalance,
    BankAccountBalanceCreate,
    BankAccountCreate,
    BankTransaction,
    BankTransactionCreate,
)
from py24so.resources._sync._resource import Resource

_DEFAULT_BANK_TRANSACTIONS_PAGE_SIZE = 25


class BankAccounts(Resource):
    """``/bankaccounts``: the organization's own bank accounts."""

    def list(self, *, before: Optional[Union[date, str]] = None) -> List[BankAccount]:
        """List bank accounts, with balances as of ``before`` if given."""
        response = self._client.send("GET", "/bankaccounts", params={"before": before})
        return self._client.parse_list(response, BankAccount)

    def get(
        self, bank_account_id: str, *, before: Optional[Union[date, str]] = None
    ) -> BankAccount:
        return self._client.request(
            "GET",
            f"/bankaccounts/{path_param(bank_account_id)}",
            params={"before": before},
            cast_to=BankAccount,
        )

    def create(self, bank_account: Union[BankAccountCreate, Mapping[str, Any]]) -> BankAccount:
        return self._client.request(
            "POST",
            "/bankaccounts",
            json=serialize_body(bank_account, BankAccountCreate),
            cast_to=BankAccount,
        )

    def add_balance(
        self,
        bank_account_id: str,
        balance: Union[BankAccountBalanceCreate, Mapping[str, Any]],
    ) -> BankAccountBalance:
        """Register the account's balance at a point in time."""
        return self._client.request(
            "POST",
            f"/bankaccounts/{path_param(bank_account_id)}/balances",
            json=serialize_body(balance, BankAccountBalanceCreate),
            cast_to=BankAccountBalance,
        )


class BankTransactions(Resource):
    """``/banktransactions``"""

    def list(
        self,
        *,
        date_from: Union[date, str],
        date_to: Union[date, str],
        bank_account_id: Optional[str] = None,
        page_size: Optional[int] = None,
        start_page: Optional[int] = None,
        extra_params: Optional[Mapping[str, Any]] = None,
    ) -> Paginator[BankTransaction]:
        """Iterate over bank transactions in a date range, following pagination automatically.

        Args:
            date_from: First transaction date (inclusive).
            date_to: Last transaction date (inclusive).
            bank_account_id: Only transactions on this bank account.
            page_size: Transactions per request (the API's ``limit``, default 25, max 100).
            start_page: Page to start from (default 1).
            extra_params: Additional raw query parameters.
        """
        params = {
            "dateFrom": date_from,
            "dateTo": date_to,
            "bankAccountId": bank_account_id,
            "limit": page_size,
            "page": start_page,
            **(extra_params or {}),
        }
        return self._client.paginate(
            "/banktransactions",
            BankTransaction,
            params,
            page_param="page",
            page_size=page_size or _DEFAULT_BANK_TRANSACTIONS_PAGE_SIZE,
        )

    def get(self, bank_transaction_reference: str) -> BankTransaction:
        return self._client.request(
            "GET",
            f"/banktransactions/{path_param(bank_transaction_reference)}",
            cast_to=BankTransaction,
        )

    def create(
        self, transaction: Union[BankTransactionCreate, Mapping[str, Any]]
    ) -> BankTransaction:
        return self._client.request(
            "POST",
            "/banktransactions",
            json=serialize_body(transaction, BankTransactionCreate),
            cast_to=BankTransaction,
        )
