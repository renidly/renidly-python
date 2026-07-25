"""HTTP engine: request building, retries with backoff, envelope parsing, and
error mapping. Sync and async variants share the pure helpers below.

Policy (unwrap, not-found→None, raise-on-error) lives in the resource layer, not
here — this module only turns an HTTP exchange into a normalized ``Result``.
"""
from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import httpx

from ._config import Config
from ._errors import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    InsufficientCreditsError,
    InternalServerError,
    InvalidRequestError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    RenidlyError,
    ServiceUnavailableError,
)
from ._models import LastResponse
from ._version import __version__

# Single-record "resolved but empty" codes come back as HTTP 200 + success:false.
_NOT_FOUND_CODES = {"1010", "1020", "1030", "1040", "1090"}
_USER_AGENT = f"renidly-python/{__version__}"


@dataclass
class Result:
    ok: bool
    data: Any
    envelope: Dict[str, Any]
    last_response: LastResponse
    error: Optional[RenidlyError]


def _request_id(headers: httpx.Headers) -> Optional[str]:
    return headers.get("x-request-id") or headers.get("x-renidly-request-id")


def _map_error(status: int, env: Dict[str, Any], last: LastResponse) -> RenidlyError:
    msg = env.get("message") or f"HTTP {status}"
    code = env.get("error_code")
    errors = env.get("errors") if isinstance(env.get("errors"), dict) else None
    kw: Dict[str, Any] = dict(status_code=status, error_code=code, errors=errors, request_id=last.request_id)
    low = msg.lower()
    if status == 402 or code == "1080" or "insufficient" in low or "enough credit" in low:
        return InsufficientCreditsError(msg, **kw)
    if status == 429:
        return RateLimitError(msg, **kw)
    if status == 503 or code == "1072":
        return ServiceUnavailableError(msg, **kw)
    if status == 401:
        return AuthenticationError(msg, **kw)
    if code in _NOT_FOUND_CODES or status == 404:
        return NotFoundError(msg, **kw)
    if status in (400, 422) or code == "VALIDATION_ERROR":
        return InvalidRequestError(msg, **kw)
    if status == 403:
        if "invalid" in low and "key" in low:
            return AuthenticationError(msg, **kw)
        if "credit" in low:
            return InsufficientCreditsError(msg, **kw)
        return PermissionDeniedError(msg, **kw)
    if status >= 500 or code in ("1000", "1001"):
        return InternalServerError(msg, **kw)
    return APIStatusError(msg, **kw)


def _parse(resp: httpx.Response) -> Result:
    last = LastResponse(resp.status_code, dict(resp.headers), _request_id(resp.headers))
    try:
        env = resp.json()
        if not isinstance(env, dict):
            env = {"success": resp.is_success, "data": env}
    except ValueError:
        env = {"success": False, "message": resp.text[:500] or f"HTTP {resp.status_code}"}
    ok = bool(env.get("success", resp.is_success)) and resp.is_success
    if ok:
        return Result(True, env.get("data"), env, last, None)
    return Result(False, env.get("data"), env, last, _map_error(resp.status_code, env, last))


def _is_retryable(err: RenidlyError) -> bool:
    return isinstance(err, (APIConnectionError, RateLimitError, ServiceUnavailableError))


def _backoff(cfg: Config, attempt: int, err: Optional[RenidlyError]) -> float:
    if isinstance(err, RateLimitError) and err.retry_after:
        return float(err.retry_after)
    return cfg.backoff_factor * (2 ** attempt) + random.uniform(0, cfg.backoff_factor)


class _BaseTransport:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self._limiter: Any = None  # set by the client when auto_rate_limit is on

    def _prepare(
        self, service: str, path: str, options: Optional[Dict[str, Any]]
    ) -> Tuple[str, Dict[str, str], Optional[float]]:
        options = options or {}
        api_key = options.get("api_key", self.cfg.api_key)
        headers = {"User-Agent": _USER_AGENT, "Accept": "application/json"}
        headers.update(self.cfg.default_headers)
        if api_key:
            headers[self.cfg._auth_header_for(service)] = api_key
        headers.update(options.get("headers") or {})
        return self.cfg._url_for(service, path), headers, options.get("timeout", self.cfg.timeout)


class SyncTransport(_BaseTransport):
    def __init__(self, cfg: Config, client: Optional[httpx.Client] = None) -> None:
        super().__init__(cfg)
        self._client = client or httpx.Client(timeout=cfg.timeout, proxy=cfg.proxy)

    def request(
        self,
        method: str,
        service: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None,
        apply_rate_limit: bool = True,
    ) -> Result:
        url, headers, timeout = self._prepare(service, path, options)
        if apply_rate_limit and self._limiter is not None:
            self._limiter.acquire()
        last_err: Optional[RenidlyError] = None
        for attempt in range(self.cfg.max_retries + 1):
            try:
                resp = self._client.request(
                    method, url, params=_clean(params), json=json, headers=headers, timeout=timeout
                )
                result = _parse(resp)
            except httpx.HTTPError as exc:
                result = None  # type: ignore[assignment]
                last_err = APIConnectionError(str(exc) or "connection error")
            if result is not None:
                if result.ok or not _is_retryable(result.error):  # type: ignore[arg-type]
                    return result
                last_err = result.error
                if isinstance(last_err, RateLimitError) and self._limiter is not None:
                    self._limiter.on_rate_limited()
            if attempt < self.cfg.max_retries:
                time.sleep(_backoff(self.cfg, attempt, last_err))
                continue
            raise last_err if last_err is not None else APIConnectionError("request failed")  # exhausted retries on a transport/retryable error
        raise last_err if last_err is not None else APIConnectionError("request failed")  # pragma: no cover

    def close(self) -> None:
        self._client.close()


class AsyncTransport(_BaseTransport):
    def __init__(self, cfg: Config, client: Optional[httpx.AsyncClient] = None) -> None:
        super().__init__(cfg)
        self._client = client or httpx.AsyncClient(timeout=cfg.timeout, proxy=cfg.proxy)

    async def request(
        self,
        method: str,
        service: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None,
        apply_rate_limit: bool = True,
    ) -> Result:
        url, headers, timeout = self._prepare(service, path, options)
        if apply_rate_limit and self._limiter is not None:
            await self._limiter.acquire()
        last_err: Optional[RenidlyError] = None
        for attempt in range(self.cfg.max_retries + 1):
            try:
                resp = await self._client.request(
                    method, url, params=_clean(params), json=json, headers=headers, timeout=timeout
                )
                result = _parse(resp)
            except httpx.HTTPError as exc:
                result = None  # type: ignore[assignment]
                last_err = APIConnectionError(str(exc) or "connection error")
            if result is not None:
                if result.ok or not _is_retryable(result.error):  # type: ignore[arg-type]
                    return result
                last_err = result.error
                if isinstance(last_err, RateLimitError) and self._limiter is not None:
                    self._limiter.on_rate_limited()
            if attempt < self.cfg.max_retries:
                await asyncio.sleep(_backoff(self.cfg, attempt, last_err))
                continue
            raise last_err if last_err is not None else APIConnectionError("request failed")
        raise last_err if last_err is not None else APIConnectionError("request failed")  # pragma: no cover

    async def close(self) -> None:
        await self._client.aclose()


def _clean(params: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Drop None-valued query params so optional filters simply omit."""
    if not params:
        return None
    return {k: v for k, v in params.items() if v is not None}
