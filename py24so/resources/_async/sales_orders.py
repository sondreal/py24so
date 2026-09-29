from datetime import date, datetime
from typing import Any, List, Mapping, Optional, Union

from py24so._client import AsyncAPIClient
from py24so._pagination import AsyncPaginator
from py24so._utils import FileInput, content_disposition, path_param, read_file, serialize_body
from py24so.models.accounting import PaymentMethod, SalesType
from py24so.models.sales_orders import (
    SalesOrder,
    SalesOrderAttachment,
    SalesOrderCreate,
    SalesOrderLine,
    SalesOrderLineCreate,
    SalesOrderLineUpdate,
    SalesOrderStatus,
    SalesOrderUpdate,
)
from py24so.resources._async._resource import AsyncResource


class AsyncSalesOrderLines(AsyncResource):
    """``/salesorders/{id}/lines``"""

    async def list(self, order_id: Union[int, str]) -> List[SalesOrderLine]:
        response = await self._client.send("GET", f"/salesorders/{path_param(order_id)}/lines")
        return self._client.parse_list(response, SalesOrderLine)

    async def get(self, order_id: Union[int, str], line_id: Union[int, str]) -> SalesOrderLine:
        return await self._client.request(
            "GET",
            f"/salesorders/{path_param(order_id)}/lines/{path_param(line_id)}",
            cast_to=SalesOrderLine,
        )

    async def create(
        self,
        order_id: Union[int, str],
        line: Union[SalesOrderLineCreate, Mapping[str, Any]],
    ) -> SalesOrderLine:
        """Add a line to a sales order."""
        return await self._client.request(
            "POST",
            f"/salesorders/{path_param(order_id)}/lines",
            json=serialize_body(line, SalesOrderLineCreate),
            cast_to=SalesOrderLine,
        )

    async def update(
        self,
        order_id: Union[int, str],
        line_id: Union[int, str],
        line: Union[SalesOrderLineUpdate, Mapping[str, Any]],
    ) -> SalesOrderLine:
        """Update a line. Only fields that are set on ``line`` are changed."""
        return await self._client.request(
            "PATCH",
            f"/salesorders/{path_param(order_id)}/lines/{path_param(line_id)}",
            json=serialize_body(line, SalesOrderLineUpdate),
            cast_to=SalesOrderLine,
        )

    async def delete(self, order_id: Union[int, str], line_id: Union[int, str]) -> None:
        await self._client.send(
            "DELETE", f"/salesorders/{path_param(order_id)}/lines/{path_param(line_id)}"
        )


class AsyncSalesOrderAttachments(AsyncResource):
    """``/salesorders/{id}/attachments``"""

    async def list(self, order_id: Union[int, str]) -> List[SalesOrderAttachment]:
        response = await self._client.send(
            "GET", f"/salesorders/{path_param(order_id)}/attachments"
        )
        return self._client.parse_list(response, SalesOrderAttachment)

    async def upload(
        self,
        order_id: Union[int, str],
        file: FileInput,
        *,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> SalesOrderAttachment:
        """Attach a PDF or PNG to a sales order.

        Args:
            order_id: The sales order.
            file: Raw bytes, a file path, or a file object opened in binary mode.
            filename: Name shown in 24SevenOffice. Defaults to the file's name.
            content_type: ``application/pdf`` or ``image/png``. Guessed from the
                filename when omitted.
        """
        content, name, media_type = read_file(file, filename, content_type)
        return await self._client.request(
            "POST",
            f"/salesorders/{path_param(order_id)}/attachments",
            content=content,
            headers={"Content-Type": media_type, "Content-Disposition": content_disposition(name)},
            cast_to=SalesOrderAttachment,
        )


class AsyncSalesOrders(AsyncResource):
    """``/salesorders``: sales orders, which become invoices.

    To invoice: create an order, add at least one line, then call :meth:`invoice`
    (or update ``status`` to ``"Invoice"``). The order is then put in the invoice
    queue and sent according to the organization's settings.
    """

    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.lines = AsyncSalesOrderLines(client)
        self.attachments = AsyncSalesOrderAttachments(client)

    def list(
        self,
        *,
        status: Optional[str] = None,
        customer_id: Optional[Union[int, str]] = None,
        date: Optional[Union[date, str]] = None,
        date_from: Optional[Union[date, str]] = None,
        date_to: Optional[Union[date, str]] = None,
        invoice_number: Optional[str] = None,
        reference_number: Optional[str] = None,
        created_from: Optional[Union[datetime, str]] = None,
        created_to: Optional[Union[datetime, str]] = None,
        modified_from: Optional[Union[datetime, str]] = None,
        modified_to: Optional[Union[datetime, str]] = None,
        page_size: Optional[int] = None,
        extra_params: Optional[Mapping[str, Any]] = None,
    ) -> AsyncPaginator[SalesOrder]:
        """Iterate over sales orders, following pagination automatically.

        Args:
            status: A :class:`~py24so.models.SalesOrderStatus`, e.g. ``"Draft"``.
            customer_id: Only orders for this customer.
            date: Only orders with exactly this order date.
            date_from: Only orders dated on or after this date.
            date_to: Only orders dated on or before this date.
            invoice_number: Only the order with this invoice number.
            reference_number: Only orders with this reference number.
            created_from: Created at or after this time.
            created_to: Created at or before this time.
            modified_from: Modified at or after this time.
            modified_to: Modified at or before this time.
            page_size: Orders per request (the API's ``limit``).
            extra_params: Additional raw query parameters.
        """
        params = {
            "status": status,
            "customerId": customer_id,
            "date": date,
            "dateFrom": date_from,
            "dateTo": date_to,
            "invoiceNumber": invoice_number,
            "referenceNumber": reference_number,
            "createdFrom": created_from,
            "createdTo": created_to,
            "modifiedFrom": modified_from,
            "modifiedTo": modified_to,
            "limit": page_size,
            **(extra_params or {}),
        }
        return self._client.paginate("/salesorders", SalesOrder, params)

    async def get(self, order_id: Union[int, str]) -> SalesOrder:
        return await self._client.request(
            "GET", f"/salesorders/{path_param(order_id)}", cast_to=SalesOrder
        )

    async def create(self, order: Union[SalesOrderCreate, Mapping[str, Any]]) -> SalesOrder:
        """Create a sales order (status ``Draft`` unless given). Add lines with ``lines.create``."""
        return await self._client.request(
            "POST",
            "/salesorders",
            json=serialize_body(order, SalesOrderCreate),
            cast_to=SalesOrder,
        )

    async def update(
        self, order_id: Union[int, str], order: Union[SalesOrderUpdate, Mapping[str, Any]]
    ) -> SalesOrder:
        """Update a sales order. Only fields that are set on ``order`` are changed."""
        return await self._client.request(
            "PATCH",
            f"/salesorders/{path_param(order_id)}",
            json=serialize_body(order, SalesOrderUpdate),
            cast_to=SalesOrder,
        )

    async def invoice(self, order_id: Union[int, str]) -> SalesOrder:
        """Invoice a sales order by setting its status to ``Invoice``.

        The order must have at least one line, otherwise the API responds with a
        :class:`~py24so.BadRequestError` of type ``NoLines``.
        """
        return await self.update(order_id, SalesOrderUpdate(status=SalesOrderStatus.INVOICE))

    async def delete(self, order_id: Union[int, str]) -> None:
        await self._client.send("DELETE", f"/salesorders/{path_param(order_id)}")


class AsyncSalesTypes(AsyncResource):
    """``/salestypes``"""

    async def list(self) -> List[SalesType]:
        response = await self._client.send("GET", "/salestypes")
        return self._client.parse_list(response, SalesType)

    async def get(self, sales_type_id: Union[int, str]) -> SalesType:
        return await self._client.request(
            "GET", f"/salestypes/{path_param(sales_type_id)}", cast_to=SalesType
        )


class AsyncPaymentMethods(AsyncResource):
    """``/paymentmethods``"""

    async def list(self) -> List[PaymentMethod]:
        response = await self._client.send("GET", "/paymentmethods")
        return self._client.parse_list(response, PaymentMethod)
