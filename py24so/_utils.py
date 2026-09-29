import email.utils
import enum
import mimetypes
import os
import time
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, BinaryIO, Dict, Iterable, Mapping, Optional, Tuple, Type, Union
from urllib.parse import quote

import pydantic
from pydantic import TypeAdapter

from py24so.models._base import Py24soModel

Body = Union[Py24soModel, Mapping[str, Any]]


def path_param(value: Union[str, int]) -> str:
    """Encode a value for use as a single URL path segment.

    Rejects empty values, ``.`` and ``..``, and quotes everything else (including
    ``/``) so an id can never escape its path segment, e.g. ``"../other"`` or
    ``"1?limit=1"``.
    """
    if isinstance(value, bool) or value is None:
        raise TypeError(f"Expected a str or int path parameter, got {value!r}")
    text = str(value)
    if not text.strip():
        raise ValueError("Path parameter must not be empty")
    if text in (".", ".."):
        # Dots are not percent-encoded, so these would be normalized away by URL resolution.
        raise ValueError(f"Invalid path parameter: {text!r}")
    return quote(text, safe="")


def _param_value(value: Any) -> Any:
    if isinstance(value, enum.Enum):
        value = value.value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (list, tuple, set, frozenset)):
        return ",".join(str(_param_value(v)) for v in value)
    return value


def build_params(params: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """Drop ``None`` values and convert Python values to the API's query format.

    Booleans become ``true``/``false``, dates and datetimes ISO 8601, enums their
    value and sequences comma-separated strings (e.g. ``categoryIds=1,2,3``).
    """
    if not params:
        return {}
    return {key: _param_value(value) for key, value in params.items() if value is not None}


def serialize_body(
    data: Optional[Body], model: Optional[Type[Py24soModel]] = None
) -> Optional[Dict[str, Any]]:
    """Turn a request model or mapping into the JSON payload for the API.

    Mappings are validated through ``model`` (when given), so both ``snake_case``
    and the API's ``camelCase`` keys are accepted. Only fields that were set are
    sent: explicitly passing ``None`` sends ``null`` (to clear a value on PATCH),
    while omitted fields are left untouched.
    """
    if data is None:
        return None
    if isinstance(data, pydantic.BaseModel):
        return data.model_dump(mode="json", by_alias=True, exclude_unset=True)
    if isinstance(data, Mapping):
        if model is not None:
            return model.model_validate(dict(data)).model_dump(
                mode="json", by_alias=True, exclude_unset=True
            )
        result: Dict[str, Any] = type_adapter(Dict[str, Any]).dump_python(dict(data), mode="json")
        return result
    raise TypeError(
        f"Expected a pydantic model or a mapping as request body, got {type(data).__name__}"
    )


@lru_cache(maxsize=None)
def type_adapter(tp: Any) -> TypeAdapter:  # type: ignore[type-arg]
    return TypeAdapter(tp)


def parse_retry_after(value: Optional[str], now: Optional[float] = None) -> Optional[float]:
    """Parse a ``Retry-After`` header given in seconds or as an HTTP date."""
    if not value:
        return None
    value = value.strip()
    try:
        seconds = float(value)
    except ValueError:
        try:
            parsed = email.utils.parsedate_to_datetime(value)
        except (TypeError, ValueError, IndexError):
            return None
        if parsed is None:
            return None
        seconds = parsed.timestamp() - (time.time() if now is None else now)
    return max(0.0, seconds)


FileInput = Union[bytes, bytearray, memoryview, str, "os.PathLike[str]", BinaryIO]


def read_file(
    file: FileInput, filename: Optional[str] = None, content_type: Optional[str] = None
) -> Tuple[bytes, str, str]:
    """Read bytes, a path or a binary file object into ``(content, filename, content_type)``.

    The content is read fully so the request can be retried safely.
    """
    if isinstance(file, (bytes, bytearray, memoryview)):
        content = bytes(file)
    elif isinstance(file, (str, os.PathLike)):
        path = Path(file)
        content = path.read_bytes()
        filename = filename or path.name
    elif hasattr(file, "read"):
        content = file.read()
        if not isinstance(content, bytes):
            raise TypeError("File objects must be opened in binary mode ('rb')")
        name = getattr(file, "name", None)
        if not filename and isinstance(name, str):
            filename = os.path.basename(name)
    else:
        raise TypeError(f"Unsupported file input: {type(file).__name__}")

    filename = filename or "upload"
    if content_type is None:
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return content, filename, content_type


def content_disposition(filename: str) -> str:
    """Build a safe ``Content-Disposition`` header value (RFC 6266 / RFC 5987)."""
    fallback = (
        "".join(c if 32 <= ord(c) < 127 and c not in '"\\' else "_" for c in filename) or "upload"
    )
    header = f'attachment; filename="{fallback}"'
    if fallback != filename:
        header += f"; filename*=UTF-8''{quote(filename, safe='')}"
    return header


def unwrap_list(data: Any, keys: Iterable[str] = ("items", "data", "results")) -> Any:
    """Return the list inside common envelope shapes, or ``data`` unchanged."""
    if isinstance(data, dict):
        for key in keys:
            if isinstance(data.get(key), list):
                return data[key]
    return data
