from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import Field

from py24so.models._base import Date, Py24soModel, StrId, Timestamp
from py24so.models.common import DimensionValue, IdRef


class Account(Py24soModel):
    """A general ledger account."""

    id: Optional[int] = None
    number: Optional[int] = None
    name: Optional[str] = None
    tax_id: Optional[int] = None


class BalanceAmount(Py24soModel):
    date: Date = None
    opening: Optional[float] = None
    closing: Optional[float] = None
    change: Optional[float] = None


class AccountBalance(Py24soModel):
    """Opening, closing and change amounts for one account, per date or period."""

    account: Optional[Account] = None
    balances: List[BalanceAmount] = Field(default_factory=list)


class BalanceType(str, Enum):
    DATE = "Date"
    PERIOD = "Period"


class Currency(Py24soModel):
    code: Optional[str] = None
    rate: Optional[float] = None


class Tax(Py24soModel):
    """A VAT code."""

    id: Optional[int] = None
    number: Optional[int] = None
    name: Optional[str] = None
    rate: Optional[float] = None


class FiscalPeriodType(str, Enum):
    YEAR = "Year"
    PERIOD = "Period"
    ALL = "All"


class FiscalPeriod(Py24soModel):
    id: Optional[str] = None
    type: Optional[str] = None
    starting_date: Date = None
    ending_date: Date = None


class Voucher(Py24soModel):
    id: Optional[str] = None
    number: Optional[int] = None


class TransactionLineTax(Py24soModel):
    id: Optional[int] = None
    rate: Optional[float] = None


class TransactionLineCurrency(Py24soModel):
    code: Optional[str] = None
    rate: Optional[float] = None


class TransactionLineInvoice(Py24soModel):
    number: Optional[str] = None
    due_date: Date = None
    remittance_reference: Optional[str] = None


class TransactionLine(Py24soModel):
    """A posted general ledger line."""

    id: Optional[str] = None
    transaction: Optional[Voucher] = None
    account: Optional[Account] = None
    transaction_type: Optional[IdRef] = None
    tax: Optional[TransactionLineTax] = None
    amount: Optional[float] = None
    currency: Optional[TransactionLineCurrency] = None
    date: Date = None
    invoice: Optional[TransactionLineInvoice] = None
    customer: Optional[IdRef] = None
    dimensions: Optional[List[DimensionValue]] = None
    comment: Optional[str] = None
    period_date: Date = None
    document_id: Optional[int] = None
    created_at: Timestamp = None
    modified_at: Timestamp = None


class TransactionCreateTax(Py24soModel):
    number: int
    amount: Optional[float] = None
    base_rate: Optional[int] = None
    specification_number: Optional[int] = None


class TransactionCreateCurrency(Py24soModel):
    code: str
    rate: float


class TransactionCreateDimension(Py24soModel):
    dimension_type: int
    value: str


class TransactionCreateInvoice(Py24soModel):
    due_date: Date = None
    number: Optional[str] = None
    remittance_reference: Optional[str] = None
    bank_account: Optional[str] = None


class TransactionCreateLine(Py24soModel):
    """One line of a voucher. The amounts of all lines must balance to zero."""

    account_number: int
    amount: float
    tax: TransactionCreateTax
    comment: Optional[str] = None
    date: Date = None
    period_date: Date = None
    currency: Optional[TransactionCreateCurrency] = None
    dimensions: Optional[List[TransactionCreateDimension]] = None
    invoice: Optional[TransactionCreateInvoice] = None


class TransactionCreate(Py24soModel):
    """Payload for ``POST /transactions`` (register a voucher)."""

    transaction_type_number: int
    date: date
    lines: List[TransactionCreateLine]
    comment: Optional[str] = None
    document_id: Optional[int] = None


class TransactionCreated(Py24soModel):
    transaction_id: Optional[str] = None


class TransactionType(Py24soModel):
    id: Optional[int] = None
    number: Optional[int] = None
    name: Optional[str] = None


class PaymentMethod(Py24soModel):
    id: Optional[int] = None
    name: Optional[str] = None
    account: Optional[IdRef] = None


class SalesType(Py24soModel):
    id: Optional[int] = None
    name: Optional[str] = None
    account: Optional[IdRef] = None


class Dimension(Py24soModel):
    """A dimension type, e.g. department or project."""

    id: Optional[int] = None
    name: Optional[str] = None


class DimensionElement(Py24soModel):
    dimension_type: Optional[int] = None
    value: Optional[str] = None
    name: Optional[str] = None


class DocumentPage(Py24soModel):
    sequence_number: Optional[int] = None
    thumbnail_url: Optional[str] = None
    preview_url: Optional[str] = None


class Document(Py24soModel):
    """An archived document. ``download_url`` is a short-lived link."""

    document_id: Optional[int] = None
    content_type: Optional[str] = None
    download_url: Optional[str] = None
    pages: Optional[List[DocumentPage]] = None


class FileUpload(Py24soModel):
    """Where to upload a file: send its bytes with ``upload_method`` to ``upload_url``."""

    upload_method: Optional[str] = None
    upload_url: Optional[str] = None
    file_id: StrId = None


class FileUploadStatus(Py24soModel):
    """Processing status of an uploaded file (e.g. ``Pending``, ``Completed``, ``Failed``).

    ``document_id`` is set once the file has been archived.
    """

    file_id: StrId = None
    status: Optional[str] = None
    document_id: Optional[int] = None
