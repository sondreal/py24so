from typing import Any, Dict, List, Optional, Union, cast

import httpx

from py24so.core.batch import BatchRequest
from py24so.core.client import APIClient, AsyncAPIClient
from py24so.core.exceptions import NotFoundError
from py24so.models.invoice import Invoice, InvoiceCreate, InvoiceStatus, InvoiceUpdate


class InvoiceEndpoint:
    """
    Invoice endpoint for the 24SevenOffice API.

    This class provides methods for working with invoices in the API.
    """

    def __init__(self, client: APIClient):
        """
        Initialize the invoice endpoint.

        Args:
            client: API client
        """
        self.client = client
        self.base_path = "/invoices"

    def list(
        self,
        page: int = 1,
        page_size: int = 50,
        status: Optional[InvoiceStatus] = None,
        customer_id: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Invoice]:
        """
        List invoices.

        Args:
            page: Page number
            page_size: Number of items per page
            status: Filter by invoice status
            customer_id: Filter by customer ID
            **kwargs: Additional query parameters

        Returns:
            List of invoices
        """
        params = {
            "page": page,
            "pageSize": page_size,
            **kwargs,
        }

        if status:
            params["status"] = status

        if customer_id:
            params["customerId"] = customer_id

        response = self.client.get(self.base_path, params=params)
        return self.client.parse_response_list(response, Invoice)

    def get(self, invoice_id: str) -> Invoice:
        """
        Get an invoice by ID.

        Args:
            invoice_id: Invoice ID

        Returns:
            Invoice

        Raises:
            NotFoundError: If the invoice is not found
        """
        response = self.client.get(f"{self.base_path}/{invoice_id}")
        return self.client.parse_response(response, Invoice)

    def create(self, invoice: Union[Dict[str, Any], InvoiceCreate]) -> Invoice:
        """
        Create a new invoice.

        Args:
            invoice: Invoice data

        Returns:
            Created invoice
        """
        if isinstance(invoice, InvoiceCreate):
            data = invoice.model_dump(exclude_unset=True)
        else:
            data = invoice

        response = self.client.post(self.base_path, json=data)
        return self.client.parse_response(response, Invoice)

    def update(
        self,
        invoice_id: str,
        invoice: Union[Dict[str, Any], InvoiceUpdate],
    ) -> Invoice:
        """
        Update an invoice.

        Args:
            invoice_id: Invoice ID
            invoice: Invoice data

        Returns:
            Updated invoice

        Raises:
            NotFoundError: If the invoice is not found
        """
        if isinstance(invoice, InvoiceUpdate):
            data = invoice.model_dump(exclude_unset=True, exclude_none=True)
        else:
            data = invoice

        response = self.client.patch(f"{self.base_path}/{invoice_id}", json=data)
        return self.client.parse_response(response, Invoice)

    def delete(self, invoice_id: str) -> None:
        """
        Delete an invoice.

        Args:
            invoice_id: Invoice ID

        Raises:
            NotFoundError: If the invoice is not found
        """
        response = self.client.delete(f"{self.base_path}/{invoice_id}")
        if response.status_code != 204:
            # If not 204 No Content, then parse the response
            self.client.parse_response(response, dict)

    def send(self, invoice_id: str) -> Invoice:
        """
        Send an invoice to a customer.

        Args:
            invoice_id: Invoice ID

        Returns:
            Updated invoice with status SENT

        Raises:
            NotFoundError: If the invoice is not found
        """
        response = self.client.post(f"{self.base_path}/{invoice_id}/send")
        return self.client.parse_response(response, Invoice)

    def mark_as_paid(self, invoice_id: str, payment_date: Optional[str] = None) -> Invoice:
        """
        Mark an invoice as paid.

        Args:
            invoice_id: Invoice ID
            payment_date: Payment date (ISO format)

        Returns:
            Updated invoice with status PAID

        Raises:
            NotFoundError: If the invoice is not found
        """
        data = {}
        if payment_date:
            data["paymentDate"] = payment_date

        response = self.client.post(f"{self.base_path}/{invoice_id}/mark-paid", json=data)
        return self.client.parse_response(response, Invoice)

    def create_credit_note(self, invoice_id: str) -> Invoice:
        """
        Create a credit note for an invoice.

        Args:
            invoice_id: Invoice ID

        Returns:
            Created credit note invoice

        Raises:
            NotFoundError: If the invoice is not found
        """
        response = self.client.post(f"{self.base_path}/{invoice_id}/credit")
        return self.client.parse_response(response, Invoice)

    def batch_get(self, invoice_ids: List[str]) -> Dict[str, Invoice]:
        """
        Get multiple invoices in a single batch request.

        Args:
            invoice_ids: List of invoice IDs

        Returns:
            Dictionary mapping invoice IDs to invoice objects
        """
        batch = BatchRequest()

        for invoice_id in invoice_ids:
            batch.add(
                method="GET",
                path=f"{self.base_path}/{invoice_id}",
                request_id=invoice_id,
            )

        batch_response = self.client.send_batch_request(batch)

        # Process the responses
        invoices: Dict[str, Invoice] = {}
        for invoice_id in invoice_ids:
            if batch_response.is_successful(invoice_id):
                body = batch_response.get_body(invoice_id)
                if body:
                    invoices[invoice_id] = Invoice.model_validate(body)

        return invoices


class AsyncInvoiceEndpoint:
    """
    Asynchronous invoice endpoint for the 24SevenOffice API.

    This class provides asynchronous methods for working with invoices in the API.
    """

    def __init__(self, client: AsyncAPIClient):
        """
        Initialize the async invoice endpoint.

        Args:
            client: Async API client
        """
        self.client = client
        self.base_path = "/invoices"

    async def list(
        self,
        page: int = 1,
        page_size: int = 50,
        status: Optional[InvoiceStatus] = None,
        customer_id: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Invoice]:
        """
        List invoices asynchronously.

        Args:
            page: Page number
            page_size: Number of items per page
            status: Filter by invoice status
            customer_id: Filter by customer ID
            **kwargs: Additional query parameters

        Returns:
            List of invoices
        """
        params = {
            "page": page,
            "pageSize": page_size,
            **kwargs,
        }

        if status:
            params["status"] = status

        if customer_id:
            params["customerId"] = customer_id

        response = await self.client.get(self.base_path, params=params)
        return await self.client.parse_response_list(response, Invoice)

    async def get(self, invoice_id: str) -> Invoice:
        """
        Get an invoice by ID asynchronously.

        Args:
            invoice_id: Invoice ID

        Returns:
            Invoice

        Raises:
            NotFoundError: If the invoice is not found
        """
        response = await self.client.get(f"{self.base_path}/{invoice_id}")
        return await self.client.parse_response(response, Invoice)

    async def create(self, invoice: Union[Dict[str, Any], InvoiceCreate]) -> Invoice:
        """
        Create a new invoice asynchronously.

        Args:
            invoice: Invoice data

        Returns:
            Created invoice
        """
        if isinstance(invoice, InvoiceCreate):
            data = invoice.model_dump(exclude_unset=True)
        else:
            data = invoice

        response = await self.client.post(self.base_path, json=data)
        return await self.client.parse_response(response, Invoice)

    async def update(
        self,
        invoice_id: str,
        invoice: Union[Dict[str, Any], InvoiceUpdate],
    ) -> Invoice:
        """
        Update an invoice asynchronously.

        Args:
            invoice_id: Invoice ID
            invoice: Invoice data

        Returns:
            Updated invoice

        Raises:
            NotFoundError: If the invoice is not found
        """
        if isinstance(invoice, InvoiceUpdate):
            data = invoice.model_dump(exclude_unset=True, exclude_none=True)
        else:
            data = invoice

        response = await self.client.patch(f"{self.base_path}/{invoice_id}", json=data)
        return await self.client.parse_response(response, Invoice)

    async def delete(self, invoice_id: str) -> None:
        """
        Delete an invoice asynchronously.

        Args:
            invoice_id: Invoice ID

        Raises:
            NotFoundError: If the invoice is not found
        """
        response = await self.client.delete(f"{self.base_path}/{invoice_id}")
        if response.status_code != 204:
            # If not 204 No Content, then parse the response
            await self.client.parse_response(response, dict)

    async def send(self, invoice_id: str) -> Invoice:
        """
        Send an invoice to a customer asynchronously.

        Args:
            invoice_id: Invoice ID

        Returns:
            Updated invoice with status SENT

        Raises:
            NotFoundError: If the invoice is not found
        """
        response = await self.client.post(f"{self.base_path}/{invoice_id}/send")
        return await self.client.parse_response(response, Invoice)

    async def mark_as_paid(self, invoice_id: str, payment_date: Optional[str] = None) -> Invoice:
        """
        Mark an invoice as paid asynchronously.

        Args:
            invoice_id: Invoice ID
            payment_date: Payment date (ISO format)

        Returns:
            Updated invoice with status PAID

        Raises:
            NotFoundError: If the invoice is not found
        """
        data = {}
        if payment_date:
            data["paymentDate"] = payment_date

        response = await self.client.post(f"{self.base_path}/{invoice_id}/mark-paid", json=data)
        return await self.client.parse_response(response, Invoice)

    async def create_credit_note(self, invoice_id: str) -> Invoice:
        """
        Create a credit note for an invoice asynchronously.

        Args:
            invoice_id: Invoice ID

        Returns:
            Created credit note invoice

        Raises:
            NotFoundError: If the invoice is not found
        """
        response = await self.client.post(f"{self.base_path}/{invoice_id}/credit")
        return await self.client.parse_response(response, Invoice)

    async def batch_get(self, invoice_ids: List[str]) -> Dict[str, Invoice]:
        """
        Get multiple invoices in a single batch request asynchronously.

        Args:
            invoice_ids: List of invoice IDs

        Returns:
            Dictionary mapping invoice IDs to invoice objects
        """
        batch = BatchRequest()

        for invoice_id in invoice_ids:
            batch.add(
                method="GET",
                path=f"{self.base_path}/{invoice_id}",
                request_id=invoice_id,
            )

        batch_response = await self.client.send_batch_request(batch)

        # Process the responses
        invoices: Dict[str, Invoice] = {}
        for invoice_id in invoice_ids:
            if batch_response.is_successful(invoice_id):
                body = batch_response.get_body(invoice_id)
                if body:
                    invoices[invoice_id] = Invoice.model_validate(body)

        return invoices
