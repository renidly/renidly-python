"""Rate-limiter unit tests (no network)."""
import asyncio

import pytest

from renidly import AsyncRenidly, Renidly, RenidlyConfig
from renidly._ratelimit import (
    AsyncRateLimiter,
    SyncRateLimiter,
    _Window,
    limit_from_tier,
)

# Real /credits/tier/k/ payloads.
TIERED = {"balance": 0.0, "current_tier": {"name": "Testing", "limit_per_minute": 7},
          "next_tier": {"name": "Hobby", "limit_per_minute": 30}}
ENTERPRISE = {"balance": 792626.0, "limit_per_minute": 300, "current_tier": None,
              "next_tier": None, "previous_tier": None}


def test_sliding_window_math():
    w = _Window(2)
    now = 100.0
    assert w.check(now) == 0.0
    assert w.check(now) == 0.0
    assert round(w.check(now)) == 60          # 3rd within the window waits ~60s
    assert w.check(now + 61) == 0.0           # window slid; slot free again


def test_limit_from_tier_tiered_and_enterprise():
    assert limit_from_tier(TIERED) == 7
    assert limit_from_tier(ENTERPRISE) == 300          # current_tier is null
    assert limit_from_tier({"current_tier": None}) is None
    assert limit_from_tier(None) is None


def test_enterprise_key_prefix_no_longer_requires_supplied_limit():
    c = Renidly("enterprise-abc", config=RenidlyConfig(auto_rate_limit=True))
    assert isinstance(c._transport._limiter, SyncRateLimiter)


def test_enterprise_fixed_limit_ok():
    c = Renidly("enterprise-abc", config=RenidlyConfig(auto_rate_limit=True, rate_limit_per_minute=550))
    assert c._transport._limiter._win.rpm == 550


def test_no_limiter_when_disabled():
    assert Renidly("rnd-abc")._transport._limiter is None


def test_safety_factor_applied():
    c = Renidly("rnd-abc", config=RenidlyConfig(auto_rate_limit=True, rate_limit_per_minute=100, rate_limit_safety=0.9))
    assert c._transport._limiter._win.rpm == 90


@pytest.mark.parametrize("payload, rpm", [(TIERED, 7), (ENTERPRISE, 300)])
def test_sync_limiter_loads_limit_for_both_key_types(payload, rpm):
    lim = SyncRateLimiter(fetch=lambda: limit_from_tier(payload))
    lim.acquire()
    assert lim._loaded and lim._win.rpm == rpm


@pytest.mark.parametrize("payload, rpm", [(TIERED, 7), (ENTERPRISE, 300)])
def test_async_limiter_loads_limit_for_both_key_types(payload, rpm):
    async def fetch():
        return limit_from_tier(payload)

    lim = AsyncRateLimiter(fetch=fetch)
    asyncio.run(lim.acquire())
    assert lim._loaded and lim._win.rpm == rpm


def test_unknown_limit_warns_once_and_does_not_throttle():
    calls = []

    def fetch():
        calls.append(1)
        return None

    lim = SyncRateLimiter(fetch=fetch)
    with pytest.warns(RuntimeWarning, match="could not determine"):
        lim.acquire()
    for _ in range(20):          # would block ~20 min if it fell back to 1 rpm
        lim.acquire()
    assert not lim._loaded
    assert len(calls) == 1       # not re-fetched on every request


def test_failed_lookup_warns_and_does_not_throttle():
    def fetch():
        raise RuntimeError("boom")

    lim = SyncRateLimiter(fetch=fetch)
    with pytest.warns(RuntimeWarning, match="boom"):
        lim.acquire()
    lim.acquire()
    assert not lim._loaded


def test_rate_limited_forces_refetch():
    values = iter([60, 90])
    lim = SyncRateLimiter(fetch=lambda: next(values))
    lim.acquire()
    assert lim._win.rpm == 60
    lim.on_rate_limited()
    lim.acquire()
    assert lim._win.rpm == 90


def test_async_client_enterprise_prefix_builds_limiter():
    c = AsyncRenidly("enterprise-abc", config=RenidlyConfig(auto_rate_limit=True))
    assert isinstance(c._transport._limiter, AsyncRateLimiter)
