from datetime import datetime
from enum import Enum
from typing import Optional

from py24so.models._base import Py24soModel, Timestamp
from py24so.models.common import CurrencyCode, NumberRef


class AccountNumberType(str, Enum):
    BBAN = "bban"
    IBAN = "iban"


class BankAccountContact(Py24soModel):
    name: Optional[str] = None
    email: Optional[str] = None


class BankAccountOwner(Py24soModel):
    name: Optional[str] = None
    organization_number: Optional[str] = None
    contact: Optional[BankAccountContact] = None


class BankAccountBalance(Py24soModel):
    amount: Optional[float] = None
    timestamp: Timestamp = None
    currency: Optional[CurrencyCode] = None


class BankAccountBalanceCreate(Py24soModel):
    """Payload for ``POST /bankaccounts/{id}/balances``."""

    amount: float
    timestamp: datetime
    currency: CurrencyCode


class _BankAccountFields(Py24soModel):
    number: Optional[str] = None
    bic: Optional[str] = None
    type: Optional[str] = None
    name: Optional[str] = None
    owner: Optional[BankAccountOwner] = None
    transaction_type: Optional[NumberRef] = None
    ledger_account: Optional[NumberRef] = None


class BankAccount(_BankAccountFields):
    """One of the organization's own bank accounts. ``type`` is an :class:`AccountNumberType`."""

    id: Optional[str] = None
    balance: Optional[BankAccountBalance] = None
    created_at: Timestamp = None
    modified_at: Timestamp = None


class BankAccountCreate(_BankAccountFields):
    """Payload for ``POST /bankaccounts``.

    The spec requires ``number``, ``bic``, ``type``, ``name`` and ``owner``.
    """


class BankTransactionType(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class PaymentReferenceType(str, Enum):
    TEXT = "text"
    OCR = "ocr"
    INVOICE_REF = "invoiceRef"


class BankAccountRef(Py24soModel):
    id: Optional[str] = None


class PaymentReference(Py24soModel):
    """``type`` is a :class:`PaymentReferenceType`, e.g. a KID/OCR number."""

    type: Optional[str] = None
    value: Optional[str] = None


class BankTransactionAmount(Py24soModel):
    value: Optional[float] = None
    currency: Optional[CurrencyCode] = None


class CounterpartyAccount(Py24soModel):
    number: Optional[str] = None
    type: Optional[str] = None


class BankTransactionCode(Py24soModel):
    """ISO 20022 bank transaction code."""

    domain_code: Optional[str] = None
    family_code: Optional[str] = None
    sub_family_code: Optional[str] = None


class _BankTransactionFields(Py24soModel):
    bank_transaction_reference: Optional[str] = None
    type: Optional[str] = None
    bank_account: Optional[BankAccountRef] = None
    payment_reference: Optional[PaymentReference] = None
    amount: Optional[BankTransactionAmount] = None
    date: Optional[str] = None
    from_bank_account: Optional[CounterpartyAccount] = None
    to_bank_account: Optional[CounterpartyAccount] = None
    bank_transaction_code: Optional[BankTransactionCode] = None


class BankTransaction(_BankTransactionFields):
    """A transaction on a bank account. ``type`` is a :class:`BankTransactionType`."""

    status: Optional[str] = None
    created_at: Timestamp = None
    modified_at: Timestamp = None


class BankTransactionCreate(_BankTransactionFields):
    """Payload for ``POST /banktransactions``. ``date`` is an ISO 8601 date string.

    The spec requires ``bank_transaction_reference``, ``type``, ``bank_account``,
    ``payment_reference``, ``amount`` and ``date``.
    """
