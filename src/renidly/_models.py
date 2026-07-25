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


class LastResponse:
    """HTTP metadata from the call that produced an object."""

    __slots__ = ("status_code", "headers", "request_id")

    def __init__(self, status_code: int, headers: Dict[str, str], request_id: Optional[str]) -> None:
        self.status_code = status_code
        self.headers = headers
        self.request_id = request_id

    def __repr__(self) -> str:  # pragma: no cover
        return f"LastResponse(status_code={self.status_code}, request_id={self.request_id!r})"


class RenidlyModel(BaseModel):
    """Base for every response object. Dynamic + typed."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    _last_response: Optional[LastResponse] = PrivateAttr(default=None)

    @property
    def last_response(self) -> Optional[LastResponse]:
        """HTTP status/headers/request-id of the response that produced this object."""
        return self._last_response

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
    def _build(cls: Type[T], data: Any, last_response: Optional[LastResponse]) -> T:
        if isinstance(data, dict):
            obj = cls.model_validate({k: RenidlyModel._coerce(v) for k, v in data.items()})
        else:
            obj = cls.model_validate({"value": data})
        obj._last_response = last_response
        return obj


class APIResponse(RenidlyModel):
    """The full shared envelope, returned when ``unwrap_data_obj=False``."""

    success: bool
    status_code: Optional[int] = None
    message: Optional[str] = None
    error_code: Optional[str] = None
    errors: Optional[Any] = None
    data: Optional[Any] = None
