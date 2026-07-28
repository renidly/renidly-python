"""Base response model and envelope wrapper.

Models are permissive (``extra="allow"``) so every field the API returns is
accessible as an attribute even before a typed model is generated for it — the
generated subclasses in ``renidly.types`` add precise typing + autocomplete on
top of the same base.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, ConfigDict, PrivateAttr

T = TypeVar("T", bound="RenidlyModel")


_CONSUMED_HEADER = "x-credits-consumed"
_BALANCE_HEADER = "x-credits-balance"


def _credit_from(headers: Optional[Dict[str, str]], name: str) -> Optional[float]:
    """Parse a numeric ``X-Credits-*`` header, case-insensitively. ``None`` when
    absent (e.g. an endpoint that isn't credit-billed)."""
    if not headers:
        return None
    raw = headers.get(name)
    if raw is None:
        for k, v in headers.items():
            if k.lower() == name:
                raw = v
                break
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


class ResponseMeta:
    """HTTP metadata for the response that produced an object.

    Exposes the status code, the raw response headers, the request id, the credit
    accounting for the call, the parsed body envelope, the raw response text, and
    ``raw_http`` — the underlying ``httpx.Response`` for anything not surfaced
    here (``.content``, ``.elapsed``, ``.http_version``, ``.request``, …)."""

    __slots__ = ("status_code", "headers", "request_id", "body", "raw_body", "raw_http")

    def __init__(
        self,
        status_code: int,
        headers: Dict[str, str],
        request_id: Optional[str],
        *,
        body: Any = None,
        raw_body: Optional[str] = None,
        raw_http: Any = None,
    ) -> None:
        self.status_code = status_code
        self.headers = headers
        self.request_id = request_id
        self.body = body          # parsed JSON envelope (dict)
        self.raw_body = raw_body  # raw response text
        self.raw_http = raw_http  # the httpx.Response object

    @property
    def credit_consumed(self) -> Optional[float]:
        """Credits charged for this request (``X-Credits-Consumed``); ``None`` if
        the endpoint isn't credit-billed."""
        return _credit_from(self.headers, _CONSUMED_HEADER)

    @property
    def remaining_balance(self) -> Optional[float]:
        """Credit balance remaining after this request (``X-Credits-Balance``);
        ``None`` if the endpoint isn't credit-billed."""
        return _credit_from(self.headers, _BALANCE_HEADER)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ResponseMeta(status_code={self.status_code}, request_id={self.request_id!r}, "
            f"credit_consumed={self.credit_consumed}, remaining_balance={self.remaining_balance})"
        )


# Backwards-compatible alias for the previous name.
LastResponse = ResponseMeta


class RenidlyModel(BaseModel):
    """Base for every response object. Dynamic + typed."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    _meta: Optional[ResponseMeta] = PrivateAttr(default=None)

    @property
    def meta(self) -> Optional[ResponseMeta]:
        """HTTP metadata for the response that produced this object: status code,
        raw headers, request id, ``credit_consumed`` / ``remaining_balance``,
        parsed ``body``, ``raw_body``, and ``raw_http`` (the httpx response)."""
        return self._meta

    @property
    def last_response(self) -> Optional[ResponseMeta]:
        """Deprecated alias for :attr:`meta`."""
        return self._meta

    @classmethod
    def _coerce(cls, v: Any) -> Any:
        """Recursively wrap nested dicts/lists so ``obj.a.b`` works dynamically.

        Nested values become the base ``RenidlyModel`` (typed subclasses declare
        their own nested fields and validate natively, bypassing this)."""
        if isinstance(v, dict):
            return RenidlyModel.model_validate({k: RenidlyModel._coerce(val) for k, val in v.items()})
        if isinstance(v, list):
            return [RenidlyModel._coerce(x) for x in v]
        return v

    @classmethod
    def _build(cls: Type[T], data: Any, meta: Optional[ResponseMeta]) -> T:
        if isinstance(data, dict):
            obj = cls.model_validate({k: RenidlyModel._coerce(v) for k, v in data.items()})
        else:
            obj = cls.model_validate({"value": data})
        obj._meta = meta
        return obj


class APIResponse(RenidlyModel):
    """The full shared envelope, returned when ``unwrap_data_obj=False``."""

    success: bool
    status_code: Optional[int] = None
    message: Optional[str] = None
    error_code: Optional[str] = None
    errors: Optional[Any] = None
    data: Optional[Any] = None
