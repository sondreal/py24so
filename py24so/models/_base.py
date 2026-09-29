import logging
from datetime import date, datetime
from typing import Annotated, Any, Optional

from pydantic import BaseModel, ConfigDict, ValidationError, ValidatorFunctionWrapHandler
from pydantic.alias_generators import to_camel
from pydantic.functional_validators import BeforeValidator, WrapValidator

logger = logging.getLogger("py24so")


class Py24soModel(BaseModel):
    """Base class for all API models.

    * Attributes are ``snake_case``; the wire format is the API's ``camelCase``.
      Both spellings are accepted when constructing a model.
    * Unknown fields returned by the API are kept (``model.model_extra``) instead
      of being dropped or raising, so new API fields never break parsing.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
        protected_namespaces=(),
    )

    def to_dict(self) -> dict:  # type: ignore[type-arg]
        """Return the model as a JSON-compatible dict using the API's field names."""
        return self.model_dump(mode="json", by_alias=True, exclude_unset=True)


#: Validation context used when parsing API responses. Only then are malformed
#: dates tolerated; user input is always validated strictly.
RESPONSE_CONTEXT = {"py24so_response": True}


def _lenient(value: Any, handler: ValidatorFunctionWrapHandler, info: Any) -> Any:
    context = getattr(info, "context", None)
    if not (isinstance(context, dict) and context.get("py24so_response")):
        return handler(value)
    if value is None or value == "":
        return None
    try:
        return handler(value)
    except ValidationError:
        logger.warning(
            "py24so: could not parse %r as a date/time for field %r; using None",
            value,
            getattr(info, "field_name", None),
        )
        return None


#: A datetime that accepts the API's mixed formats (``2023-12-31 18:00:00.000Z``,
#: ISO 8601). In API responses, empty or malformed values degrade to ``None``
#: (with a warning) instead of failing the whole response.
Timestamp = Annotated[Optional[datetime], WrapValidator(_lenient)]


def _number_to_str(value: Any) -> Any:
    return str(value) if isinstance(value, int) and not isinstance(value, bool) else value


#: A string identifier that the API sometimes sends as a number (e.g. ``fileId``).
StrId = Annotated[Optional[str], BeforeValidator(_number_to_str)]

#: A date with the same tolerance as :data:`Timestamp`.
Date = Annotated[Optional[date], WrapValidator(_lenient)]
