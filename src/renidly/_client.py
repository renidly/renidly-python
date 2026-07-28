"""The public clients: ``Renidly`` (sync) and ``AsyncRenidly`` (async).

Same surface, same method names; the async client just needs ``await``. Product
namespaces hang off the client: ``r.data``, ``r.live``, ``r.emails``, ``r.account``.

Configuration goes through one object, :class:`RenidlyConfig`, so there is a
single place (with autocomplete) for every option::

    from renidly import Renidly, RenidlyConfig
    client = Renidly("rnd-...", config=RenidlyConfig(timeout=10, auto_rate_limit=True))

``api_key`` may be passed positionally for convenience; it overrides
``config.api_key`` and falls back to the ``RENIDLY_API_KEY`` env var.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, Optional

import httpx

from ._config import RenidlyConfig
from ._models import APIResponse
from ._ratelimit import build_async_limiter, build_sync_limiter
from ._transport import AsyncTransport, SyncTransport
from .resources.account import Account, AsyncAccount
from .resources.data import AsyncData, Data
from .resources.emails import AsyncEmails, Emails
from .resources.live import AsyncLive, Live


def _resolve(api_key: Optional[str], config: Optional[RenidlyConfig]) -> RenidlyConfig:
    cfg = replace(config) if config is not None else RenidlyConfig()  # copy; never mutate the caller's
    if api_key is not None:
        cfg.api_key = api_key
    return cfg


class Renidly:
    """Synchronous Renidly client. See :class:`RenidlyConfig` for all options."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        config: Optional[RenidlyConfig] = None,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self._config = _resolve(api_key, config)
        self._transport = SyncTransport(self._config, client=http_client)
        self._transport._limiter = build_sync_limiter(self._config, self._transport)
        self.account = Account(self)
        self.data = Data(self)
        self.emails = Emails(self)
        self.live = Live(self)

    def raw_request(
        self,
        method: str,
        path: str,
        *,
        service: str = "data",
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> APIResponse:
        """Escape hatch: call any endpoint directly; returns the raw envelope."""
        r = self._transport.request(method, service, path, params=params, json=json, options=options)
        return APIResponse._build(r.envelope, r.meta)

    def close(self) -> None:
        """Close the underlying HTTP client and release its connections."""
        self._transport.close()

    def __enter__(self) -> "Renidly":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


class AsyncRenidly:
    """Asynchronous Renidly client. See :class:`RenidlyConfig` for all options."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        config: Optional[RenidlyConfig] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self._config = _resolve(api_key, config)
        self._transport = AsyncTransport(self._config, client=http_client)
        self._transport._limiter = build_async_limiter(self._config, self._transport)
        self.account = AsyncAccount(self)
        self.data = AsyncData(self)
        self.emails = AsyncEmails(self)
        self.live = AsyncLive(self)

    async def raw_request(
        self,
        method: str,
        path: str,
        *,
        service: str = "data",
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> APIResponse:
        """Async escape hatch — call any endpoint directly. See :meth:`Renidly.raw_request`."""
        r = await self._transport.request(method, service, path, params=params, json=json, options=options)
        return APIResponse._build(r.envelope, r.meta)

    async def close(self) -> None:
        """Close the underlying async HTTP client."""
        await self._transport.close()

    async def __aenter__(self) -> "AsyncRenidly":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()
