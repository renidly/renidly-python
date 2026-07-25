"""Built-in client-side rate limiter (``auto_rate_limit=True``).

Regular keys: the per-minute limit is fetched from the tier endpoint and
refreshed periodically (it moves as your balance crosses tier boundaries), and
re-fetched immediately after a 429 (your tier likely dropped). Enterprise keys
have a fixed limit that the caller must supply via ``rate_limit_per_minute``.

A sliding 60-second window guarantees we never issue more than the limit.
"""
from __future__ import annotations

import asyncio
import threading
import time
from collections import deque
from typing import Awaitable, Callable, Optional


class _Window:
    def __init__(self, rpm: int) -> None:
        self.rpm = max(1, rpm)
        self._times: deque = deque()

    def check(self, now: float) -> float:
        """Reserve a slot if free (return 0), else the seconds to wait."""
        while self._times and now - self._times[0] >= 60.0:
            self._times.popleft()
        if len(self._times) < self.rpm:
            self._times.append(now)
            return 0.0
        return 60.0 - (now - self._times[0])


class SyncRateLimiter:
    def __init__(
        self,
        *,
        fixed_rpm: Optional[int] = None,
        fetch: Optional[Callable[[], Optional[int]]] = None,
        refresh_interval: float = 300.0,
        safety: float = 1.0,
    ) -> None:
        self._fetch = fetch
        self._interval = refresh_interval
        self._safety = safety
        self._last_refresh = 0.0
        self._lock = threading.Lock()
        rpm = int((fixed_rpm or 0) * safety) if fixed_rpm else None
        self._win = _Window(rpm or 1)
        self._loaded = fixed_rpm is not None

    def _ensure(self) -> None:
        if self._fetch is None:
            return
        now = time.monotonic()
        if not self._loaded or now - self._last_refresh > self._interval:
            try:
                rpm = self._fetch()
                if rpm:
                    self._win.rpm = max(1, int(rpm * self._safety))
                    self._loaded = True
            except Exception:
                if not self._loaded:
                    self._win.rpm = 1  # conservative default until a refresh succeeds
            self._last_refresh = now

    def acquire(self) -> None:
        self._ensure()
        while True:
            with self._lock:
                wait = self._win.check(time.monotonic())
            if wait <= 0:
                return
            time.sleep(min(wait, 60.0))

    def on_rate_limited(self) -> None:
        self._last_refresh = 0.0  # force a re-fetch on the next acquire


class AsyncRateLimiter:
    def __init__(
        self,
        *,
        fixed_rpm: Optional[int] = None,
        fetch: Optional[Callable[[], Awaitable[Optional[int]]]] = None,
        refresh_interval: float = 300.0,
        safety: float = 1.0,
    ) -> None:
        self._fetch = fetch
        self._interval = refresh_interval
        self._safety = safety
        self._last_refresh = 0.0
        self._lock = asyncio.Lock()
        rpm = int((fixed_rpm or 0) * safety) if fixed_rpm else None
        self._win = _Window(rpm or 1)
        self._loaded = fixed_rpm is not None

    async def _ensure(self) -> None:
        if self._fetch is None:
            return
        now = time.monotonic()
        if not self._loaded or now - self._last_refresh > self._interval:
            try:
                rpm = await self._fetch()
                if rpm:
                    self._win.rpm = max(1, int(rpm * self._safety))
                    self._loaded = True
            except Exception:
                if not self._loaded:
                    self._win.rpm = 1
            self._last_refresh = now

    async def acquire(self) -> None:
        await self._ensure()
        while True:
            async with self._lock:
                wait = self._win.check(time.monotonic())
            if wait <= 0:
                return
            await asyncio.sleep(min(wait, 60.0))

    def on_rate_limited(self) -> None:
        self._last_refresh = 0.0


def is_enterprise(api_key: Optional[str]) -> bool:
    return api_key is not None and api_key.startswith("enterprise-")


_ENTERPRISE_MSG = (
    "auto_rate_limit is on for an enterprise key, which has a fixed rate limit. "
    "Pass rate_limit_per_minute=<your limit> to the client."
)


def build_sync_limiter(cfg, transport) -> Optional[SyncRateLimiter]:
    if not cfg.auto_rate_limit:
        return None
    if cfg.rate_limit_per_minute is not None:
        return SyncRateLimiter(fixed_rpm=cfg.rate_limit_per_minute, safety=cfg.rate_limit_safety)
    if is_enterprise(cfg.api_key):
        raise ValueError(_ENTERPRISE_MSG)

    def fetch() -> Optional[int]:
        r = transport.request("GET", "account", "/credits/tier/k/", apply_rate_limit=False)
        if r.error is not None:
            raise r.error
        return ((r.data or {}).get("current_tier") or {}).get("limit_per_minute")

    return SyncRateLimiter(fetch=fetch, refresh_interval=cfg.rate_limit_refresh, safety=cfg.rate_limit_safety)


def build_async_limiter(cfg, transport) -> Optional[AsyncRateLimiter]:
    if not cfg.auto_rate_limit:
        return None
    if cfg.rate_limit_per_minute is not None:
        return AsyncRateLimiter(fixed_rpm=cfg.rate_limit_per_minute, safety=cfg.rate_limit_safety)
    if is_enterprise(cfg.api_key):
        raise ValueError(_ENTERPRISE_MSG)

    async def fetch() -> Optional[int]:
        r = await transport.request("GET", "account", "/credits/tier/k/", apply_rate_limit=False)
        if r.error is not None:
            raise r.error
        return ((r.data or {}).get("current_tier") or {}).get("limit_per_minute")

    return AsyncRateLimiter(fetch=fetch, refresh_interval=cfg.rate_limit_refresh, safety=cfg.rate_limit_safety)
