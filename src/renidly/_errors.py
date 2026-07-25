"""Typed exception hierarchy, mapped from the shared response envelope.

Every request that fails raises a subclass of :class:`RenidlyError`. Catch the
specific class you care about, or ``RenidlyError`` for all of them.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


class RenidlyError(Exception):
    """Base class for every error raised by the SDK."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        errors: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        #: The clean, top-level server message (e.g. "Validation failed").
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        #: Field-level detail (``{field: reason}``) — the *why* behind the message.
        self.errors = errors or {}
        self.request_id = request_id
        # The exception's str() includes everything, so an uncaught traceback (or
        # a plain print/log) shows exactly what went wrong — not just "Validation
        # failed". Example: "Validation failed — name: must be at least 3 characters
        # (VALIDATION_ERROR, request_id=req_1)".
        super().__init__(self._full_message())

    def _full_message(self) -> str:
        detail = self.message
        if self.errors:
            fields = "; ".join(f"{k}: {v}" for k, v in self.errors.items())
            detail = f"{detail} — {fields}" if fields else detail
        meta = []
        if self.error_code:
            meta.append(str(self.error_code))
        if self.status_code:
            meta.append(f"HTTP {self.status_code}")
        if self.request_id:
            meta.append(f"request_id={self.request_id}")
        return f"{detail} ({', '.join(meta)})" if meta else detail

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return (
            f"{type(self).__name__}(message={self.message!r}, "
            f"status_code={self.status_code!r}, error_code={self.error_code!r})"
        )


class APIConnectionError(RenidlyError):
    """The request never reached the API (network failure, timeout, DNS…)."""


class APIStatusError(RenidlyError):
    """The API returned a non-success response. Base of all HTTP-status errors."""


class AuthenticationError(APIStatusError):
    """Missing or invalid API key (HTTP 401 / 403)."""


class PermissionDeniedError(APIStatusError):
    """Key is valid but not allowed here — premium-gated or opted-out (HTTP 403)."""


class InvalidRequestError(APIStatusError):
    """Request failed validation (HTTP 400 / 422). See :attr:`field_errors`."""

    @property
    def field_errors(self) -> Dict[str, Any]:
        return self.errors


class InsufficientCreditsError(APIStatusError):
    """Not enough credits for the request (HTTP 402 / 403)."""


class NotFoundError(APIStatusError):
    """A lookup resolved nothing, or a batch job was not found / expired."""


class RateLimitError(APIStatusError):
    """Per-minute rate limit for your tier exceeded (HTTP 429)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        meta = self.errors or {}
        self.tier: Optional[str] = meta.get("current_tier") or meta.get("tier")
        self.limit: Optional[int] = meta.get("current_limit") or meta.get("limit")
        self.retry_after: Optional[float] = meta.get("retry_after")


class ServiceUnavailableError(APIStatusError):
    """Temporarily unavailable — safe to retry shortly (HTTP 503)."""


class InternalServerError(APIStatusError):
    """Unexpected server error (HTTP 5xx)."""
