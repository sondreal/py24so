from datetime import date
from enum import Enum
from typing import List, Optional, Union

from py24so.models._base import Date, Py24soModel, Timestamp
from py24so.models.common import DimensionValue, IdRef


class SalesOrderStatus(str, Enum):
    DRAFT = "Draft"
    WEB = "Web"
    PROPOSAL = "Proposal"
    CONFIRMED = "Confirmed"
    #: Setting this status on an order with lines puts it in the invoice queue.
    INVOICE = "Invoice"
    ADVANCE_INVOICE = "AdvanceInvoice"
    INACTIVE = "Inactive"


class DistributionMethod(str, Enum):
    NONE = ""
    MANUAL = "manualdistribution"
    EFAKTURA = "efakturadistribution"
    EHF = "ehfdistribution"
    POSTAL = "postaldistribution"
    PRINT = "printdistribution"
    EMAIL = "emaildistribution"


class PaymentTermsType(str, Enum):
    NUMBER_OF_DAYS = "NumberOfDays"
    OUT_MONTH_PLUS_DAYS = "OutMonthPlusDays"
    FIXED_DATE = "FixedDate"


class PaymentTerms(Py24soModel):
    """Payment terms: a number of days, end-of-month plus days, or a fixed date.

    ``value`` is an ``int`` for the first two types and a date for ``FixedDate``::

        PaymentTerms(type=PaymentTermsType.NUMBER_OF_DAYS, value=14)
    """

    type: Optional[str] = None
    value: Optional[Union[int, date, str]] = None


class SalesOrderCustomer(Py24soModel):
    """The invoiced customer. On create, ``{"id": ...}`` is enough."""

    id: Optional[int] = None
    organization_number: Optional[str] = None
    invoice_email_addresses: Optional[List[str]] = None
    gln: Optional[str] = None
    name: Optional[str] = None
    street: Optional[str] = None
    postal_code: Optional[str] = None
    postal_area: Optional[str] = None
    city: Optional[str] = None
    country_subdivision: Optional[str] = None
    country_code: Optional[str] = None


class DeliveryCustomer(Py24soModel):
    id: Optional[int] = None
    name: Optional[str] = None
    street: Optional[str] = None
    postal_code: Optional[str] = None
    postal_area: Optional[str] = None
    city: Optional[str] = None
    country_subdivision: Optional[str] = None
    country_code: Optional[str] = None


class SalesOrderCurrency(Py24soModel):
    code: Optional[str] = None
    rate: Optional[float] = None


class InvoiceTransaction(Py24soModel):
    id: Optional[str] = None


class SalesOrderInvoice(Py24soModel):
    """Invoice details of a sales order. ``distribution_method`` is a :class:`DistributionMethod`."""

    number: Optional[int] = None
    date: Date = None
    due_date: Date = None
    distribution_method: Optional[str] = None
    payment_terms: Optional[PaymentTerms] = None
    remittance_reference: Optional[str] = None
    transaction: Optional[InvoiceTransaction] = None


class Accrual(Py24soModel):
    """Accrual of revenue over ``length`` periods starting at ``start_date``."""

    start_date: Date = None
    length: Optional[int] = None


class YourReference(Py24soModel):
    id: Optional[int] = None
    name: Optional[str] = None


class _SalesOrderFields(Py24soModel):
    currency: Optional[SalesOrderCurrency] = None
    status: Optional[str] = None
    delivery_customer: Optional[DeliveryCustomer] = None
    delivery_date: Date = None
    invoice: Optional[SalesOrderInvoice] = None
    accrual: Optional[Accrual] = None
    date: Date = None
    internal_memo: Optional[str] = None
    memo: Optional[str] = None
    your_reference: Optional[YourReference] = None
    our_reference: Optional[IdRef] = None
    payment_method: Optional[IdRef] = None
    reference_number: Optional[str] = None
    sales_type: Optional[IdRef] = None


class SalesOrder(_SalesOrderFields):
    """A sales order. ``status`` is a :class:`SalesOrderStatus`.

    ``dimensions`` is only included when fetching a single order.
    """

    id: Optional[int] = None
    customer: Optional[SalesOrderCustomer] = None
    gross_amount: Optional[float] = None
    net_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    dimensions: Optional[List[DimensionValue]] = None
    created_at: Timestamp = None
    modified_at: Timestamp = None


class SalesOrderCreate(_SalesOrderFields):
    """Payload for ``POST /salesorders``::

    SalesOrderCreate(customer=SalesOrderCustomer(id=123), memo="Thanks!")
    """

    customer: SalesOrderCustomer
    dimensions: Optional[List[DimensionValue]] = None


class SalesOrderUpdate(_SalesOrderFields):
    """Payload for ``PATCH /salesorders/{id}``. Only fields you set are sent."""

    customer: Optional[SalesOrderCustomer] = None
    dimensions: Optional[List[DimensionValue]] = None


class LineType(str, Enum):
    PRODUCT = "product"
    TEXT = "text"


class LineProduct(Py24soModel):
    """The product on a line, as it was when the line was created."""

    id: Optional[int] = None
    number: Optional[str] = None


class LineTax(Py24soModel):
    id: Optional[int] = None
    number: Optional[int] = None
    rate: Optional[float] = None


class LineAccount(Py24soModel):
    id: Optional[int] = None
    number: Optional[int] = None
    name: Optional[str] = None


class _LineFields(Py24soModel):
    type: Optional[str] = None
    product: Optional[LineProduct] = None
    description: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    cost_price: Optional[float] = None
    discount_rate: Optional[float] = None
    tax: Optional[LineTax] = None
    account: Optional[LineAccount] = None
    is_hidden: Optional[bool] = None
    dimensions: Optional[List[DimensionValue]] = None
    accrual: Optional[Accrual] = None


class SalesOrderLine(_LineFields):
    """A sales order line. ``type`` is a :class:`LineType`."""

    id: Optional[int] = None


class SalesOrderLineCreate(_LineFields):
    """Payload for ``POST /salesorders/{id}/lines``::

    SalesOrderLineCreate(type="product", product=LineProduct(id=101), quantity=2, price=49.99)
    """


class SalesOrderLineUpdate(_LineFields):
    """Payload for ``PATCH /salesorders/{id}/lines/{line_id}``. Only fields you set are sent."""


class SalesOrderAttachment(Py24soModel):
    file_id: Optional[str] = None
    order_id: Optional[int] = None
    file_name: Optional[str] = None
    media_type: Optional[str] = None
    size: Optional[int] = None
    timestamp: Timestamp = None
    tags: Optional[List[str]] = None
