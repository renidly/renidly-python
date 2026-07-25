"""Rate-limiter unit tests (no network)."""
import pytest

from renidly import Renidly, RenidlyConfig
from renidly._ratelimit import _Window, is_enterprise


def test_sliding_window_math():
    w = _Window(2)
    now = 100.0
    assert w.check(now) == 0.0
    assert w.check(now) == 0.0
    assert round(w.check(now)) == 60          # 3rd within the window waits ~60s
    assert w.check(now + 61) == 0.0           # window slid; slot free again


def test_is_enterprise():
    assert is_enterprise("enterprise-abc") is True
    assert is_enterprise("rnd-abc") is False
    assert is_enterprise(None) is False


def test_enterprise_requires_supplied_limit():
    with pytest.raises(ValueError):
        Renidly("enterprise-abc", config=RenidlyConfig(auto_rate_limit=True))


def test_enterprise_fixed_limit_ok():
    c = Renidly("enterprise-abc", config=RenidlyConfig(auto_rate_limit=True, rate_limit_per_minute=550))
    assert c._transport._limiter._win.rpm == 550


def test_no_limiter_when_disabled():
    assert Renidly("rnd-abc")._transport._limiter is None


def test_safety_factor_applied():
    c = Renidly("rnd-abc", config=RenidlyConfig(auto_rate_limit=True, rate_limit_per_minute=100, rate_limit_safety=0.9))
    assert c._transport._limiter._win.rpm == 90
