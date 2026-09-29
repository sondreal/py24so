"""Every operation in the OpenAPI spec, exercised through both clients.

Each case checks that the wrapper sends the right method, path, query string
and JSON body, and parses the response into the right model. The coverage test
at the bottom fails if the spec gains an operation that no case exercises.
"""

import inspect
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import httpx
import pytest

from py24so import AsyncPaginator, Paginator
from py24so import models as m
from tests.conftest import FakeAPI, json_response

SPEC = json.loads((Path(__file__).parents[2] / "openapi" / "openapi.json").read_text())

CUSTOMER = {
    "id": 12345,
    "name": "ABC Corporation",
    "isCompany": True,
    "isSupplier": False,
    "organizationNumber": "123456789",
    "address": {"visit": {"street": "Main 1", "postalCode": "0150", "countryCode": "NO"}},
    "email": {"contact": "contact@example.com", "billing": "billing@example.com"},
    "createdAt": "2022-01-01 18:00:00.000Z",
    "modifiedAt": "2023-12-31T18:00:00.000Z",
}
PRODUCT = {
    "id": 101,
    "name": "Leather handbag",
    "number": "PROD-001",
    "type": "default",
    "status": "active",
    "salesPrice": 49.99,
    "stock": {"isManaged": True, "quantity": 3},
    "category": {"id": 12, "name": "Bags"},
    "units": {"id": 1, "name": "Piece", "symbol": "pcs"},
}
CATEGORY = {"id": 12, "name": "Shoe accessories", "alternativeReference": "dk-45", "parentId": 0}
ORDER = {
    "id": 1234,
    "customer": {"id": 12345, "name": "ABC Corporation"},
    "status": "Draft",
    "date": "2024-06-01",
    "currency": {"code": "NOK", "rate": 1},
    "invoice": {"paymentTerms": {"type": "NumberOfDays", "value": 14}},
    "grossAmount": 124.99,
    "netAmount": 99.99,
    "taxAmount": 25,
}
LINE = {
    "id": 1,
    "type": "product",
    "product": {"id": 101},
    "description": "Leather handbag",
    "quantity": 2,
    "price": 49.99,
    "discountRate": 10,
    "tax": {"id": 3, "number": 3, "rate": 25},
}
BANK_ACCOUNT = {
    "id": "0b4a4a4e-1d5b-4b8e-9d1a-7f6b3b1f0c11",
    "number": "12345678903",
    "type": "bban",
    "balance": {
        "amount": 10.5,
        "timestamp": "2024-06-02T12:00:00.000Z",
        "currency": {"code": "NOK"},
    },
}
BANK_TX = {
    "bankTransactionReference": "ref-1",
    "type": "inbound",
    "bankAccount": {"id": BANK_ACCOUNT["id"]},
    "amount": {"value": 100, "currency": {"code": "NOK"}},
    "status": "created",
}
TX_LINE = {
    "id": "l1",
    "transaction": {"id": "t1", "number": 10},
    "account": {"id": 1, "number": 1920, "name": "Bank"},
    "amount": 100,
    "date": "2024-01-15",
}


@dataclass
class Case:
    op: str  # "METHOD /spec/{template}"
    path: str  # concrete path the call must hit
    call: Callable[[Any], Any]
    response: Any = None
    status: int = 200
    params: Optional[Dict[str, str]] = None
    body: Any = None
    check: Callable[[Any], Any] = field(default=lambda result: None)

    @property
    def method(self) -> str:
        return self.op.split(" ", 1)[0]

    @property
    def id(self) -> str:
        return self.op


CASES = [
    # --- accounting ---------------------------------------------------------
    Case(
        "GET /accountbalances",
        "/accountbalances",
        lambda c: c.account_balances.list(
            date_from=date(2024, 1, 1),
            date_to="2024-12-31",
            periods=[date(2024, 6, 30), date(2024, 12, 31)],
            type=m.BalanceType.PERIOD,
            keep_incoming=True,
        ),
        response=[
            {
                "account": {"id": 1, "number": 1920, "name": "Bank"},
                "balances": [{"date": "2024-06-30", "opening": 0, "closing": 10, "change": 10}],
            }
        ],
        params={
            "dateFrom": "2024-01-01",
            "dateTo": "2024-12-31",
            "periods": "2024-06-30,2024-12-31",
            "type": "Period",
            "keepIncoming": "true",
        },
        check=lambda r: r[0].balances[0].closing == 10 and r[0].account.number == 1920,
    ),
    Case(
        "GET /accountbalances/{id}",
        "/accountbalances/7",
        lambda c: c.account_balances.list(
            date_from="2024-01-01", date_to="2024-01-31", account_id=7
        ),
        response=[{"account": {"id": 7}, "balances": []}],
        params={"dateFrom": "2024-01-01", "dateTo": "2024-01-31"},
        check=lambda r: r[0].account.id == 7,
    ),
    Case(
        "GET /accounts",
        "/accounts",
        lambda c: c.accounts.list(query="bank"),
        response=[{"id": 1, "number": 1920, "name": "Bank", "taxId": 0}],
        params={"query": "bank"},
        check=lambda r: isinstance(r[0], m.Account) and r[0].tax_id == 0,
    ),
    Case(
        "GET /accounts/{id}",
        "/accounts/1",
        lambda c: c.accounts.get(1),
        response={"id": 1, "number": 1920},
        check=lambda r: r.number == 1920,
    ),
    Case(
        "GET /currencies",
        "/currencies",
        lambda c: c.currencies.list(),
        response=[{"code": "EUR", "rate": 11.5}],
        check=lambda r: r[0].rate == 11.5,
    ),
    Case(
        "GET /documents/{documentId}",
        "/documents/99",
        lambda c: c.documents.get(99),
        response={
            "documentId": 99,
            "contentType": "application/pdf",
            "downloadUrl": "https://files.example/99",
            "pages": [{"sequenceNumber": 1, "thumbnailUrl": "t", "previewUrl": "p"}],
        },
        check=lambda r: r.pages[0].sequence_number == 1,
    ),
    Case(
        "GET /fiscalperiods",
        "/fiscalperiods",
        lambda c: c.fiscal_periods.list(type=m.FiscalPeriodType.ALL),
        response=[
            {"id": "2024", "type": "Year", "startingDate": "2024-01-01", "endingDate": "2024-12-31"}
        ],
        params={"type": "All"},
        check=lambda r: r[0].ending_date == date(2024, 12, 31),
    ),
    Case(
        "GET /taxes",
        "/taxes",
        lambda c: c.taxes.list(),
        response=[{"id": 3, "number": 3, "name": "Utgående mva", "rate": 25}],
        check=lambda r: r[0].rate == 25,
    ),
    Case("GET /taxes/{id}", "/taxes/3", lambda c: c.taxes.get(3), response={"id": 3}),
    Case(
        "GET /transactionlines",
        "/transactionlines",
        lambda c: c.transaction_lines.list(
            date_from="2024-01-01",
            date_to="2024-01-31",
            account_number=1920,
            include_dimensions=True,
            page_size=50,
        ),
        response=[TX_LINE],
        params={
            "dateFrom": "2024-01-01",
            "dateTo": "2024-01-31",
            "accountNumber": "1920",
            "includeDimensions": "true",
            "limit": "50",
        },
        check=lambda r: r[0].transaction.number == 10 and r[0].date == date(2024, 1, 15),
    ),
    Case(
        "GET /transactionlines/{id}",
        "/transactionlines/l1",
        lambda c: c.transaction_lines.get("l1"),
        response=TX_LINE,
        check=lambda r: r.amount == 100,
    ),
    Case(
        "POST /transactions",
        "/transactions",
        lambda c: c.transactions.create(
            m.TransactionCreate(
                transaction_type_number=1,
                date=date(2024, 1, 15),
                comment="Opening balance",
                lines=[
                    m.TransactionCreateLine(
                        account_number=1920, amount=100, tax=m.TransactionCreateTax(number=0)
                    ),
                    m.TransactionCreateLine(
                        account_number=2050, amount=-100, tax=m.TransactionCreateTax(number=0)
                    ),
                ],
            )
        ),
        response={"transactionId": "t1"},
        status=201,
        body={
            "transactionTypeNumber": 1,
            "date": "2024-01-15",
            "comment": "Opening balance",
            "lines": [
                {"accountNumber": 1920, "amount": 100.0, "tax": {"number": 0}},
                {"accountNumber": 2050, "amount": -100.0, "tax": {"number": 0}},
            ],
        },
        check=lambda r: r.transaction_id == "t1",
    ),
    Case(
        "POST /fileUpload",
        "/fileUpload",
        lambda c: c.files.create_upload("application/pdf"),
        response={"uploadMethod": "PUT", "uploadUrl": "https://upload.example/f1", "fileId": "f1"},
        body={"contentType": "application/pdf"},
        check=lambda r: r.file_id == "f1",
    ),
    Case(
        "GET /fileUpload/{fileId}",
        "/fileUpload/f1",
        lambda c: c.files.get_status("f1"),
        response={"fileId": "f1", "status": "Processed", "documentId": 99},
        check=lambda r: r.document_id == 99,
    ),
    Case(
        "GET /transactiontypes",
        "/transactiontypes",
        lambda c: c.transaction_types.list(),
        response=[{"id": 1, "number": 1, "name": "Utgående faktura"}],
    ),
    # --- bank ---------------------------------------------------------------
    Case(
        "GET /bankaccounts",
        "/bankaccounts",
        lambda c: c.bank_accounts.list(before=date(2024, 7, 1)),
        response=[BANK_ACCOUNT],
        params={"before": "2024-07-01"},
        check=lambda r: r[0].balance.currency.code == "NOK",
    ),
    Case(
        "POST /bankaccounts",
        "/bankaccounts",
        lambda c: c.bank_accounts.create(
            {"number": "12345678903", "type": "bban", "ledger_account": {"number": 1920}}
        ),
        response=BANK_ACCOUNT,
        status=201,
        body={"number": "12345678903", "type": "bban", "ledgerAccount": {"number": 1920}},
    ),
    Case(
        "GET /bankaccounts/{id}",
        f"/bankaccounts/{BANK_ACCOUNT['id']}",
        lambda c: c.bank_accounts.get(BANK_ACCOUNT["id"]),
        response=BANK_ACCOUNT,
        check=lambda r: r.id == BANK_ACCOUNT["id"],
    ),
    Case(
        "POST /bankaccounts/{id}/balances",
        f"/bankaccounts/{BANK_ACCOUNT['id']}/balances",
        lambda c: c.bank_accounts.add_balance(
            BANK_ACCOUNT["id"],
            m.BankAccountBalanceCreate(
                amount=10.5, timestamp="2024-06-02T12:00:00Z", currency=m.CurrencyCode(code="NOK")
            ),
        ),
        response=BANK_ACCOUNT["balance"],
        status=201,
        body={"amount": 10.5, "timestamp": "2024-06-02T12:00:00Z", "currency": {"code": "NOK"}},
    ),
    Case(
        "GET /banktransactions",
        "/banktransactions",
        lambda c: c.bank_transactions.list(
            date_from="2024-01-01", date_to="2024-01-31", bank_account_id=BANK_ACCOUNT["id"]
        ),
        response=[BANK_TX],
        params={
            "dateFrom": "2024-01-01",
            "dateTo": "2024-01-31",
            "bankAccountId": BANK_ACCOUNT["id"],
        },
        check=lambda r: r[0].amount.value == 100,
    ),
    Case(
        "POST /banktransactions",
        "/banktransactions",
        lambda c: c.bank_transactions.create(
            m.BankTransactionCreate(
                bank_transaction_reference="ref-1",
                type=m.BankTransactionType.INBOUND,
                payment_reference=m.PaymentReference(type="ocr", value="1234567890"),
            )
        ),
        response=BANK_TX,
        status=201,
        body={
            "bankTransactionReference": "ref-1",
            "type": "inbound",
            "paymentReference": {"type": "ocr", "value": "1234567890"},
        },
    ),
    Case(
        "GET /banktransactions/{bankTransactionReference}",
        "/banktransactions/ref-1",
        lambda c: c.bank_transactions.get("ref-1"),
        response=BANK_TX,
    ),
    # --- customers ------------------------------------------------------------
    Case(
        "GET /customers",
        "/customers",
        lambda c: c.customers.list(is_company=True, sort_by="name:asc", page_size=10),
        response=[CUSTOMER],
        params={"isCompany": "true", "sortBy": "name:asc", "limit": "10"},
        check=lambda r: r[0].email.billing == "billing@example.com"
        and r[0].created_at.year == 2022,
    ),
    Case(
        "POST /customers",
        "/customers",
        lambda c: c.customers.create(
            m.CustomerCreate(
                is_company=True,
                name="ABC Corporation",
                email=m.CustomerEmail(contact="contact@example.com"),
                mobile_phone="+4799999999",
            )
        ),
        response=CUSTOMER,
        body={
            "isCompany": True,
            "name": "ABC Corporation",
            "email": {"contact": "contact@example.com"},
            "mobilePhone": "+4799999999",
        },
        check=lambda r: r.id == 12345,
    ),
    Case(
        "GET /customers/{customerId}",
        "/customers/12345",
        lambda c: c.customers.get(12345),
        response=CUSTOMER,
        check=lambda r: r.address.visit.postal_code == "0150",
    ),
    Case(
        "PATCH /customers/{customerId}",
        "/customers/12345",
        lambda c: c.customers.update(12345, {"note": None, "phone": "123"}),
        response=CUSTOMER,
        body={"note": None, "phone": "123"},
    ),
    Case(
        "DELETE /customers/{customerId}",
        "/customers/12345",
        lambda c: c.customers.delete(12345),
        status=204,
        check=lambda r: r is None,
    ),
    Case(
        "GET /customers/{customerId}/bankaccounts",
        "/customers/12345/bankaccounts",
        lambda c: c.customers.bank_accounts.list(12345),
        response=[{"number": "12345678903", "type": "bban", "isDefault": True}],
        check=lambda r: r[0].is_default is True,
    ),
    Case(
        "POST /customers/{customerId}/bankaccounts",
        "/customers/12345/bankaccounts",
        lambda c: c.customers.bank_accounts.create(
            12345, m.CustomerBankAccount(number="12345678903", type="bban", is_default=True)
        ),
        response={"number": "12345678903", "type": "bban", "isDefault": True},
        status=201,
        body={"number": "12345678903", "type": "bban", "isDefault": True},
    ),
    Case(
        "GET /customers/{customerId}/bankaccounts/{accountNumber}",
        "/customers/12345/bankaccounts/12345678903",
        lambda c: c.customers.bank_accounts.get(12345, "12345678903"),
        response={"number": "12345678903"},
    ),
    Case(
        "PATCH /customers/{customerId}/bankaccounts/{accountNumber}",
        "/customers/12345/bankaccounts/12345678903",
        lambda c: c.customers.bank_accounts.update(12345, "12345678903", {"isDefault": False}),
        response={"number": "12345678903", "isDefault": False},
        body={"isDefault": False},
    ),
    # --- dimensions -------------------------------------------------------------
    Case(
        "GET /dimensions",
        "/dimensions",
        lambda c: c.dimensions.list(),
        response=[{"id": 1, "name": "Department"}],
    ),
    Case(
        "GET /dimensions/{dimensionType}",
        "/dimensions/1",
        lambda c: c.dimensions.get(1),
        response={"id": 1, "name": "Department"},
    ),
    Case(
        "GET /dimensions/{dimensionType}/elements",
        "/dimensions/1/elements",
        lambda c: c.dimensions.elements.list(1, page_size=100),
        response=[{"dimensionType": 1, "value": "10", "name": "Sales"}],
        params={"limit": "100"},
        check=lambda r: r[0].name == "Sales",
    ),
    Case(
        "GET /dimensions/{dimensionType}/elements/{value}",
        "/dimensions/1/elements/10",
        lambda c: c.dimensions.elements.get(1, "10"),
        response={"dimensionType": 1, "value": "10", "name": "Sales"},
    ),
    # --- sales orders -------------------------------------------------------------
    Case(
        "POST /salesorders",
        "/salesorders",
        lambda c: c.sales_orders.create(
            m.SalesOrderCreate(
                customer=m.SalesOrderCustomer(id=12345),
                date=date(2024, 6, 1),
                invoice=m.SalesOrderInvoice(
                    payment_terms=m.PaymentTerms(type=m.PaymentTermsType.NUMBER_OF_DAYS, value=14)
                ),
            )
        ),
        response=ORDER,
        body={
            "customer": {"id": 12345},
            "date": "2024-06-01",
            "invoice": {"paymentTerms": {"type": "NumberOfDays", "value": 14}},
        },
        check=lambda r: r.invoice.payment_terms.value == 14,
    ),
    Case(
        "GET /salesorders",
        "/salesorders",
        lambda c: c.sales_orders.list(status=m.SalesOrderStatus.DRAFT, customer_id=12345),
        response=[ORDER],
        params={"status": "Draft", "customerId": "12345"},
        check=lambda r: r[0].gross_amount == 124.99,
    ),
    Case(
        "GET /salesorders/{id}",
        "/salesorders/1234",
        lambda c: c.sales_orders.get(1234),
        response={**ORDER, "dimensions": [{"dimensionType": 1, "value": "10", "name": "Sales"}]},
        check=lambda r: r.dimensions[0].value == "10",
    ),
    Case(
        "PATCH /salesorders/{id}",
        "/salesorders/1234",
        lambda c: c.sales_orders.invoice(1234),
        response={**ORDER, "status": "Invoice"},
        body={"status": "Invoice"},
        check=lambda r: r.status == m.SalesOrderStatus.INVOICE,
    ),
    Case(
        "DELETE /salesorders/{id}",
        "/salesorders/1234",
        lambda c: c.sales_orders.delete(1234),
        status=204,
    ),
    Case(
        "GET /salesorders/{id}/attachments",
        "/salesorders/1234/attachments",
        lambda c: c.sales_orders.attachments.list(1234),
        response=[{"fileId": "f1", "orderId": 1234, "fileName": "a.pdf", "size": 3}],
        check=lambda r: r[0].file_name == "a.pdf",
    ),
    Case(
        "POST /salesorders/{id}/attachments",
        "/salesorders/1234/attachments",
        lambda c: c.sales_orders.attachments.upload(1234, b"%PDF", filename="Kvittering ø.pdf"),
        response={"fileId": "f1", "orderId": 1234, "fileName": "Kvittering ø.pdf"},
        status=201,
        check=lambda r: r.file_id == "f1",
    ),
    Case(
        "GET /salesorders/{id}/lines",
        "/salesorders/1234/lines",
        lambda c: c.sales_orders.lines.list(1234),
        response=[LINE],
        check=lambda r: r[0].tax.rate == 25,
    ),
    Case(
        "POST /salesorders/{id}/lines",
        "/salesorders/1234/lines",
        lambda c: c.sales_orders.lines.create(
            1234,
            m.SalesOrderLineCreate(
                type=m.LineType.PRODUCT, product=m.LineProduct(id=101), quantity=2, price=49.99
            ),
        ),
        response=LINE,
        body={"type": "product", "product": {"id": 101}, "quantity": 2.0, "price": 49.99},
    ),
    Case(
        "GET /salesorders/{id}/lines/{lineId}",
        "/salesorders/1234/lines/1",
        lambda c: c.sales_orders.lines.get(1234, 1),
        response=LINE,
    ),
    Case(
        "PATCH /salesorders/{id}/lines/{lineId}",
        "/salesorders/1234/lines/1",
        lambda c: c.sales_orders.lines.update(1234, 1, {"quantity": 3}),
        response={**LINE, "quantity": 3},
        body={"quantity": 3.0},
    ),
    Case(
        "DELETE /salesorders/{id}/lines/{lineId}",
        "/salesorders/1234/lines/1",
        lambda c: c.sales_orders.lines.delete(1234, 1),
        status=204,
    ),
    Case(
        "GET /paymentmethods",
        "/paymentmethods",
        lambda c: c.payment_methods.list(),
        response=[{"id": 1, "name": "Vipps", "account": {"id": 1920}}],
        check=lambda r: r[0].account.id == 1920,
    ),
    Case(
        "GET /salestypes",
        "/salestypes",
        lambda c: c.sales_types.list(),
        response=[{"id": 1, "name": "Standard", "account": {"id": 3000}}],
    ),
    Case(
        "GET /salestypes/{id}", "/salestypes/1", lambda c: c.sales_types.get(1), response={"id": 1}
    ),
    # --- me & organization -----------------------------------------------------------
    Case(
        "GET /me",
        "/me",
        lambda c: c.me.get(thumb=True, max_age=60),
        response={"id": "u1", "firstName": "Kari", "lastName": "Nordmann"},
        params={"thumb": "true", "maxAge": "60"},
        check=lambda r: r.first_name == "Kari",
    ),
    Case(
        "GET /me/identifiers",
        "/me/identifiers",
        lambda c: c.me.identifiers.list(status="Confirmed"),
        response=[
            {"id": "i1", "type": "email", "value": "kari@example.com", "status": "Confirmed"}
        ],
        params={"status": "Confirmed"},
    ),
    Case(
        "GET /me/identifiers/{id}",
        "/me/identifiers/i1",
        lambda c: c.me.identifiers.get("i1"),
        response={"id": "i1"},
    ),
    Case(
        "GET /me/licenses",
        "/me/licenses",
        lambda c: c.me.licenses.list(organization_id=12345),
        response=[{"id": "l1", "name": "Acme", "organizationId": 12345}],
        params={"organizationId": "12345"},
    ),
    Case(
        "GET /me/licenses/{id}/organization",
        "/me/licenses/l1/organization",
        lambda c: c.me.licenses.organization("l1"),
        response={"id": "o1", "name": "Acme"},
    ),
    Case(
        "GET /organization/information",
        "/organization/information",
        lambda c: c.organization.get(),
        response={"id": 12345, "name": "Acme AS", "settings": {"currencyCode": "NOK"}},
        check=lambda r: r.settings.currency_code == "NOK",
    ),
    Case(
        "GET /organization/people",
        "/organization/people",
        lambda c: c.organization.people.list(person_type=m.PersonType.ORGANIZATION),
        response=[{"id": 1, "firstName": "Kari", "personType": "Organization", "hasLicense": True}],
        params={"personType": "Organization"},
    ),
    Case(
        "GET /organization/people/{id}",
        "/organization/people/1",
        lambda c: c.organization.people.get(1),
        response={"id": 1},
    ),
    # --- products ------------------------------------------------------------------
    Case(
        "GET /pricelists",
        "/pricelists",
        lambda c: c.price_lists.list(),
        response=[{"id": 1, "name": "Retail", "currencyCode": "NOK", "isInclusiveTax": True}],
    ),
    Case(
        "GET /pricelists/{listId}",
        "/pricelists/1",
        lambda c: c.price_lists.get(1),
        response={"id": 1},
    ),
    Case(
        "GET /pricelists/{listId}/prices",
        "/pricelists/1/prices",
        lambda c: c.price_lists.prices(1, product_ids=[101, 102]),
        response=[{"productId": 101, "price": 45.0}],
        params={"productIds": "101,102"},
        check=lambda r: r[0].price == 45.0,
    ),
    Case(
        "GET /productcategories",
        "/productcategories",
        lambda c: c.product_categories.list(),
        response=[CATEGORY],
        check=lambda r: r[0].alternative_reference == "dk-45",
    ),
    Case(
        "POST /productcategories",
        "/productcategories",
        lambda c: c.product_categories.create(m.ProductCategoryCreate(name="Shoes", parent_id=0)),
        response=CATEGORY,
        status=201,
        body={"name": "Shoes", "parentId": 0},
    ),
    Case(
        "GET /productcategories/{id}",
        "/productcategories/12",
        lambda c: c.product_categories.get(12),
        response=CATEGORY,
    ),
    Case(
        "PATCH /productcategories/{id}",
        "/productcategories/12",
        lambda c: c.product_categories.update(12, m.ProductCategoryUpdate(name="Boots")),
        response=CATEGORY,
        body={"name": "Boots"},
    ),
    Case(
        "DELETE /productcategories/{id}",
        "/productcategories/12",
        lambda c: c.product_categories.delete(12),
        status=204,
    ),
    Case(
        "GET /productunits",
        "/productunits",
        lambda c: c.product_units.list(),
        response=[{"id": 1, "name": "Piece", "symbol": "pcs"}],
    ),
    Case(
        "GET /products",
        "/products",
        lambda c: c.products.list(search="bag", category_ids=[12, 13], page_size=25),
        response=[PRODUCT],
        params={"productSearch": "bag", "categoryIds": "12,13", "limit": "25"},
        check=lambda r: r[0].stock.is_managed is True and r[0].category.name == "Bags",
    ),
    Case(
        "POST /products",
        "/products",
        lambda c: c.products.create(
            m.ProductCreate(name="Leather handbag", sales_price=49.99, category=m.IdRef(id=12))
        ),
        response=PRODUCT,
        status=201,
        body={"name": "Leather handbag", "salesPrice": 49.99, "category": {"id": 12}},
    ),
    Case("GET /products/{id}", "/products/101", lambda c: c.products.get(101), response=PRODUCT),
    Case(
        "PATCH /products/{id}",
        "/products/101",
        lambda c: c.products.update(101, {"status": "inactive"}),
        response={**PRODUCT, "status": "inactive"},
        body={"status": "inactive"},
    ),
    Case("DELETE /products/{id}", "/products/101", lambda c: c.products.delete(101), status=204),
    Case(
        "GET /products/{id}/dimensions",
        "/products/101/dimensions",
        lambda c: c.products.dimensions.list(101),
        response=[
            {"dimensionType": 1, "dimensionTypeName": "Department", "value": "10", "name": "Sales"}
        ],
        check=lambda r: r[0].dimension_type_name == "Department",
    ),
    Case(
        "PUT /products/{id}/dimensions/{dimensionId}",
        "/products/101/dimensions/1",
        lambda c: c.products.dimensions.set(101, 1, "10"),
        response=[{"dimensionType": 1, "value": "10", "name": "Sales"}],
        body={"value": "10"},
    ),
    Case(
        "DELETE /products/{id}/dimensions/{dimensionId}",
        "/products/101/dimensions/1",
        lambda c: c.products.dimensions.delete(101, 1),
        status=204,
    ),
    Case(
        "GET /products/{id}/salestypeOverrides",
        "/products/101/salestypeOverrides",
        lambda c: c.products.sales_type_overrides.list(101),
        response=[{"productId": 101, "salesTypeId": 2, "accountNumber": 3001}],
    ),
    Case(
        "PUT /products/{id}/salestypeOverrides/{salesTypeId}",
        "/products/101/salestypeOverrides/2",
        lambda c: c.products.sales_type_overrides.set(101, 2, 3001),
        response={"productId": 101, "salesTypeId": 2, "accountNumber": 3001},
        body={"accountNumber": 3001},
        check=lambda r: r.account_number == 3001,
    ),
    Case(
        "DELETE /products/{id}/salestypeOverrides/{salesTypeId}",
        "/products/101/salestypeOverrides/2",
        lambda c: c.products.sales_type_overrides.delete(101, 2),
        status=204,
    ),
]


def _register(api: FakeAPI, case: Case) -> None:
    api.add(case.method, case.path, json_response(case.response, case.status))


def _verify(api: FakeAPI, case: Case, result: Any) -> None:
    request = api.last
    assert request.method == case.method
    assert request.url.path == "/v1" + case.path
    assert dict(request.url.params) == (case.params or {})
    assert request.headers["authorization"] == "Bearer token-1"
    if case.body is not None:
        assert json.loads(request.content) == case.body
    assert case.check(result) is not False


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.id)
def test_sync(case: Case, api: FakeAPI, client: Any) -> None:
    _register(api, case)
    result = case.call(client)
    if isinstance(result, Paginator):
        result = result.to_list()
    _verify(api, case, result)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.id)
async def test_async(case: Case, api: FakeAPI, aclient: Any) -> None:
    _register(api, case)
    result = case.call(aclient)
    if isinstance(result, AsyncPaginator):
        result = await result.to_list()
    elif inspect.isawaitable(result):
        result = await result
    _verify(api, case, result)


def test_every_spec_operation_is_covered() -> None:
    spec_ops = {
        f"{method.upper()} {path}"
        for path, item in SPEC["paths"].items()
        for method in item
        if method in {"get", "post", "put", "patch", "delete"}
    }
    covered = {case.op for case in CASES}
    assert spec_ops - covered == set(), "operations in the spec without a wrapper/test"
    assert covered - spec_ops == set(), "tests for operations that are not in the spec"


def test_attachment_upload_headers(api: FakeAPI, client: Any) -> None:
    api.add("POST", "/salesorders/1/attachments", json_response({"fileId": "f"}, 201))
    client.sales_orders.attachments.upload(1, b"%PDF-1.7", filename="Kvittering ø.pdf")
    request = api.last
    assert request.content == b"%PDF-1.7"
    assert request.headers["content-type"] == "application/pdf"
    assert request.headers["content-disposition"] == (
        "attachment; filename=\"Kvittering _.pdf\"; filename*=UTF-8''Kvittering%20%C3%B8.pdf"
    )


def test_file_upload_flow_never_leaks_token(api: FakeAPI) -> None:
    uploads = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "upload.example":
            uploads.append(request)
            return httpx.Response(200)
        return api.handler(request)

    from py24so import Client24SO
    from tests.conftest import FAST

    api.add(
        "POST",
        "/fileUpload",
        json_response(
            {"uploadMethod": "PUT", "uploadUrl": "https://upload.example/f1?sig=x", "fileId": "f1"}
        ),
    )
    api.add(
        "GET",
        "/fileUpload/f1",
        json_response({"fileId": "f1", "status": "Pending"}),
        json_response({"fileId": "f1", "status": "Processed", "documentId": 99}),
    )
    http = httpx.Client(transport=httpx.MockTransport(handler))
    with Client24SO("id", "secret", "1", FAST, http_client=http) as client:
        client._client._sleep = lambda seconds: None  # type: ignore[method-assign]
        status = client.files.upload(b"receipt", filename="receipt.pdf", wait=True)

    assert status.document_id == 99
    assert json.loads(api.requests[0].content) == {"contentType": "application/pdf"}
    assert uploads[0].method == "PUT"
    assert uploads[0].content == b"receipt"
    assert uploads[0].headers["content-type"] == "application/pdf"
    assert "authorization" not in uploads[0].headers
