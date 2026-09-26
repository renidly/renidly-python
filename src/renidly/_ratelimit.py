"""Built-in client-side rate limiter (``auto_rate_limit=True``).

The per-minute limit is fetched from the tier endpoint for every key type:
tiered accounts report it on ``current_tier`` (it moves as your balance crosses
tier boundaries, so it is refreshed periodically and re-fetched right after a
429); enterprise accounts report a fixed top-level ``limit_per_minute``.
``rate_limit_per_minute`` overrides the fetched value.

If the limit can't be determined, a ``RuntimeWarning`` is emitted and requests
are not throttled client-side until a later refresh succeeds — server 429s are
still retried by the transport. A sliding 60-second window guarantees we never
issue more than the limit once it is known.
"""
from __future__ import annotations

import asyncio
import threading
import time
import warnings
from collections import deque
from typing import Any, Awaitable, Callable, Optional


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


def limit_from_tier(data: Any) -> Optional[int]:
    """Per-minute limit from a ``/credits/tier/k/`` payload.

    Enterprise accounts carry a fixed top-level ``limit_per_minute`` (and a
    null ``current_tier``); tiered accounts carry it on ``current_tier``."""
    data = data if isinstance(data, dict) else {}
    tier = data.get("current_tier") if isinstance(data.get("current_tier"), dict) else {}
    return data.get("limit_per_minute") or tier.get("limit_per_minute")


_UNKNOWN_LIMIT_MSG = (
    "renidly: could not determine your per-minute rate limit ({reason}); "
    "client-side rate limiting is paused until the next refresh. Server 429s "
    "are still retried. Pass rate_limit_per_minute=<limit> to set it explicitly."
)


class _LimiterState:
    """Shared bookkeeping for the sync and async limiters."""

    def __init__(self, fixed_rpm: Optional[int], refresh_interval: float, safety: float) -> None:
        self._interval = refresh_interval
        self._safety = safety
        self._last_refresh: Optional[float] = None  # None → fetch on next acquire
        self._warned = False
        self._win = _Window(int(fixed_rpm * safety) if fixed_rpm else 1)
        self._loaded = fixed_rpm is not None

    def _due(self, now: float) -> bool:
        return self._last_refresh is None or now - self._last_refresh > self._interval

    def _apply(self, rpm: Optional[int], error: Optional[BaseException]) -> None:
        if rpm:
            self._win.rpm = max(1, int(rpm * self._safety))
            self._loaded = True
        elif not self._loaded and not self._warned:
            reason = f"tier lookup failed: {error}" if error else "tier response has no limit_per_minute"
            warnings.warn(_UNKNOWN_LIMIT_MSG.format(reason=reason), RuntimeWarning, stacklevel=4)
            self._warned = True

    def on_rate_limited(self) -> None:
        self._last_refresh = None  # force a re-fetch on the next acquire


class SyncRateLimiter(_LimiterState):
    def __init__(
        self,
        *,
        fixed_rpm: Optional[int] = None,
        fetch: Optional[Callable[[], Optional[int]]] = None,
        refresh_interval: float = 300.0,
        safety: float = 1.0,
    ) -> None:
        super().__init__(fixed_rpm, refresh_interval, safety)
        self._fetch = fetch
        self._lock = threading.Lock()
        self._fetch_lock = threading.Lock()

    def _ensure(self) -> None:
        if self._fetch is None:
            return
        with self._fetch_lock:
            now = time.monotonic()
            if not self._due(now):
                return
            self._last_refresh = now
            try:
                rpm, error = self._fetch(), None
            except Exception as e:
                rpm, error = None, e
            self._apply(rpm, error)

    def acquire(self) -> None:
        self._ensure()
        if not self._loaded:
            return
        while True:
            with self._lock:
                wait = self._win.check(time.monotonic())
            if wait <= 0:
                return
            time.sleep(min(wait, 60.0))


class AsyncRateLimiter(_LimiterState):
    def __init__(
        self,
        *,
        fixed_rpm: Optional[int] = None,
        fetch: Optional[Callable[[], Awaitable[Optional[int]]]] = None,
        refresh_interval: float = 300.0,
        safety: float = 1.0,
    ) -> None:
        super().__init__(fixed_rpm, refresh_interval, safety)
        self._fetch = fetch
        # Created lazily inside the running loop: on Python 3.9 asyncio.Lock()
        # binds to (or fails to find) an event loop at construction time.
        self._lock: Optional[asyncio.Lock] = None
        self._fetch_lock: Optional[asyncio.Lock] = None

    async def _ensure(self) -> None:
        if self._fetch is None:
            return
        if self._fetch_lock is None:
            self._fetch_lock = asyncio.Lock()
        async with self._fetch_lock:
            now = time.monotonic()
            if not self._due(now):
                return
            self._last_refresh = now
            try:
                rpm, error = await self._fetch(), None
            except Exception as e:
                rpm, error = None, e
            self._apply(rpm, error)

    async def acquire(self) -> None:
        await self._ensure()
        if not self._loaded:
            return
        if self._lock is None:
            self._lock = asyncio.Lock()
        while True:
            async with self._lock:
                wait = self._win.check(time.monotonic())
            if wait <= 0:
                return
            await asyncio.sleep(min(wait, 60.0))


def build_sync_limiter(cfg, transport) -> Optional[SyncRateLimiter]:
    if not cfg.auto_rate_limit:
        return None
    if cfg.rate_limit_per_minute is not None:
        return SyncRateLimiter(fixed_rpm=cfg.rate_limit_per_minute, safety=cfg.rate_limit_safety)

    def fetch() -> Optional[int]:
        r = transport.request("GET", "account", "/credits/tier/k/", apply_rate_limit=False)
        if r.error is not None:
            raise r.error
        return limit_from_tier(r.data)

    return SyncRateLimiter(fetch=fetch, refresh_interval=cfg.rate_limit_refresh, safety=cfg.rate_limit_safety)


def build_async_limiter(cfg, transport) -> Optional[AsyncRateLimiter]:
    if not cfg.auto_rate_limit:
        return None
    if cfg.rate_limit_per_minute is not None:
        return AsyncRateLimiter(fixed_rpm=cfg.rate_limit_per_minute, safety=cfg.rate_limit_safety)

    async def fetch() -> Optional[int]:
        r = await transport.request("GET", "account", "/credits/tier/k/", apply_rate_limit=False)
        if r.error is not None:
            raise r.error
        return limit_from_tier(r.data)

    return AsyncRateLimiter(fetch=fetch, refresh_interval=cfg.rate_limit_refresh, safety=cfg.rate_limit_safety)
