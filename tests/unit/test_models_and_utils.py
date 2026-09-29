import io
import logging
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List

import pydantic
import pytest

from py24so import models as m
from py24so._rate_limiter import RateLimiter
from py24so._utils import (
    build_params,
    content_disposition,
    parse_retry_after,
    path_param,
    read_file,
    serialize_body,
)
from py24so.models._base import RESPONSE_CONTEXT

ROOT = Path(__file__).parents[2]


# --- models ------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("2023-12-31 18:00:00.000Z", datetime(2023, 12, 31, 18, tzinfo=timezone.utc)),
        ("2023-12-31T18:00:00Z", datetime(2023, 12, 31, 18, tzinfo=timezone.utc)),
        ("", None),
        (None, None),
    ],
)
def test_timestamps_accept_the_api_formats(raw: str, expected: datetime) -> None:
    customer = m.Customer.model_validate({"createdAt": raw}, context=RESPONSE_CONTEXT)
    assert customer.created_at == expected


def test_malformed_response_dates_degrade_to_none(caplog: pytest.LogCaptureFixture) -> None:
    # The API's own spec contains "2024-06-31"; one bad value must not break a whole list.
    with caplog.at_level(logging.WARNING, logger="py24so"):
        order = m.SalesOrder.model_validate(
            {"id": 1, "date": "2024-06-31", "modifiedAt": "yesterday"}, context=RESPONSE_CONTEXT
        )
    assert order.id == 1 and order.date is None and order.modified_at is None
    assert "2024-06-31" in caplog.text


def test_user_input_dates_are_strict() -> None:
    with pytest.raises(pydantic.ValidationError):
        m.SalesOrderUpdate(date="2024-06-31")
    with pytest.raises(pydantic.ValidationError):
        m.TransactionCreate(transaction_type_number=1, date="", lines=[])


def test_unknown_fields_are_preserved() -> None:
    product = m.Product.model_validate({"id": 1, "brandNewField": {"x": 1}})
    assert product.model_extra == {"brandNewField": {"x": 1}}
    assert product.to_dict() == {"id": 1, "brandNewField": {"x": 1}}


def test_enum_values_are_plain_strings() -> None:
    order = m.SalesOrder.model_validate({"status": "SomethingNew"})  # new status: no crash
    assert order.status == "SomethingNew"
    assert m.SalesOrder(status=m.SalesOrderStatus.INVOICE).status == "Invoice"
    assert m.SalesOrderUpdate(status=m.SalesOrderStatus.INVOICE).to_dict() == {"status": "Invoice"}


def test_models_accept_snake_and_camel_case() -> None:
    a = m.CustomerUpdate(mobile_phone="1")
    b = m.CustomerUpdate.model_validate({"mobilePhone": "1"})
    assert a == b
    assert a.to_dict() == {"mobilePhone": "1"}


def test_customer_create_validation() -> None:
    assert m.CustomerCreate(is_company=True, name="Acme").to_dict() == {
        "isCompany": True,
        "name": "Acme",
    }
    person = m.CustomerCreate(
        is_company=False, person=m.CustomerPerson(first_name="Kari", last_name="Nordmann")
    )
    assert person.to_dict()["person"] == {"firstName": "Kari", "lastName": "Nordmann"}
    with pytest.raises(pydantic.ValidationError, match="requires a name"):
        m.CustomerCreate(is_company=True)
    with pytest.raises(pydantic.ValidationError, match="requires person"):
        m.CustomerCreate(is_company=False, name="Kari")


def test_payment_terms_value_types() -> None:
    days = m.PaymentTerms.model_validate({"type": "NumberOfDays", "value": 14})
    fixed = m.PaymentTerms.model_validate({"type": "FixedDate", "value": "2024-02-01"})
    assert days.value == 14
    assert str(fixed.value) == "2024-02-01"
    assert m.PaymentTerms(type="FixedDate", value=date(2024, 2, 1)).to_dict() == {
        "type": "FixedDate",
        "value": "2024-02-01",
    }


# --- serialization -------------------------------------------------------------------


def test_serialize_body_sends_only_set_fields() -> None:
    update = m.ProductUpdate(name="New", description=None)
    assert serialize_body(update) == {"name": "New", "description": None}
    assert serialize_body(None) is None
    assert serialize_body({"a": date(2024, 1, 2)}) == {"a": "2024-01-02"}
    with pytest.raises(TypeError):
        serialize_body(["not", "a", "mapping"])  # type: ignore[arg-type]


def test_build_params() -> None:
    assert build_params(
        {
            "a": None,
            "b": True,
            "c": False,
            "d": date(2024, 1, 2),
            "e": [1, 2, 3],
            "f": m.SalesOrderStatus.DRAFT,
            "g": 0,
            "h": datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
        }
    ) == {
        "b": "true",
        "c": "false",
        "d": "2024-01-02",
        "e": "1,2,3",
        "f": "Draft",
        "g": 0,
        "h": "2024-01-02T03:04:05+00:00",
    }
    assert build_params(None) == {}


def test_path_param() -> None:
    assert path_param(12) == "12"
    assert path_param("a b/c") == "a%20b%2Fc"
    for bad in ("", " ", None, False):
        with pytest.raises((ValueError, TypeError)):
            path_param(bad)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "header, expected",
    [("5", 5.0), ("0.5", 0.5), ("-3", 0.0), ("soon", None), (None, None), ("", None)],
)
def test_parse_retry_after_seconds(header: str, expected: float) -> None:
    assert parse_retry_after(header) == expected


def test_parse_retry_after_http_date() -> None:
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc).timestamp()
    assert parse_retry_after("Mon, 01 Jan 2024 12:00:30 GMT", now=now) == 30.0


def test_read_file_inputs(tmp_path: Path) -> None:
    path = tmp_path / "receipt.png"
    path.write_bytes(b"\x89PNG")
    assert read_file(path) == (b"\x89PNG", "receipt.png", "image/png")
    assert read_file(str(path), content_type="application/octet-stream")[2] == (
        "application/octet-stream"
    )
    with path.open("rb") as handle:
        assert read_file(handle) == (b"\x89PNG", "receipt.png", "image/png")
    assert read_file(b"data") == (b"data", "upload", "application/octet-stream")
    with pytest.raises(TypeError, match="binary mode"):
        read_file(io.StringIO("text"))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        read_file(123)  # type: ignore[arg-type]


def test_content_disposition_is_header_safe() -> None:
    assert content_disposition("a.pdf") == 'attachment; filename="a.pdf"'
    evil = content_disposition('x".pdf\r\nX-Injected: 1')
    assert "\r" not in evil and "\n" not in evil
    assert evil.startswith('attachment; filename="x_.pdf__X-Injected: 1"')


# --- rate limiter --------------------------------------------------------------------


def test_rate_limiter_bucket() -> None:
    now = [0.0]
    limiter = RateLimiter(2, period=1.0, clock=lambda: now[0])
    assert limiter.reserve() == 0
    assert limiter.reserve() == 0
    assert limiter.reserve() == pytest.approx(0.5)  # bucket empty: next slot in 0.5s
    assert limiter.reserve() == pytest.approx(1.0)  # slots are reserved, not re-used
    now[0] = 10.0
    assert limiter.reserve() == 0  # refilled


def test_rate_limiter_is_thread_safe() -> None:
    import threading

    limiter = RateLimiter(100, period=60.0, clock=lambda: 0.0)
    waits: List[float] = []
    lock = threading.Lock()

    def worker() -> None:
        for _ in range(50):
            w = limiter.reserve()
            with lock:
                waits.append(w)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sum(1 for w in waits if w == 0) == 100
    assert sorted(waits)[-1] == pytest.approx(100 * 0.6)


def test_rate_limiter_rejects_bad_config() -> None:
    with pytest.raises(ValueError):
        RateLimiter(0)
    with pytest.raises(ValueError):
        RateLimiter(1, period=0)


# --- generated code ---------------------------------------------------------------------


def test_sync_resources_are_up_to_date() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "unasync.py"), "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_sync_and_async_clients_expose_the_same_api() -> None:
    import inspect

    from py24so import AsyncClient24SO, Client24SO

    def public(obj: object) -> set:
        return {name for name in dir(obj) if not name.startswith("_")}

    sync = Client24SO("id", "secret", "1")
    async_ = AsyncClient24SO("id", "secret", "1")
    assert public(sync) == public(async_)
    for name in public(sync):
        s, a = getattr(sync, name), getattr(async_, name)
        if hasattr(s, "_client"):  # a resource: compare its methods' signatures
            for method in public(s):
                if callable(getattr(s, method)):
                    assert inspect.signature(getattr(s, method)).parameters.keys() == (
                        inspect.signature(getattr(a, method)).parameters.keys()
                    ), f"{name}.{method}"
    sync.close()
