"""Client configuration and the service routing table.

``RenidlyConfig`` is the public, user-facing config object — build it with just
the fields you care about and pass ``Renidly(config=...)``. The four products
live under one host but different path prefixes, and the Account product uses a
*different* auth header (``X-AUTHAPI-Key``); the SDK hides that entirely.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Optional

DEFAULT_BASE_URL = "https://renidly.com"
DATA_HEADER = "X-renidly-apikey"
ACCOUNT_HEADER = "X-AUTHAPI-Key"

# service -> (path prefix, auth header)
SERVICES: Dict[str, tuple] = {
    "data": ("/api/data/v1", DATA_HEADER),
    "live": ("/api/v2", DATA_HEADER),
    "emails": ("/api/emails/v1", DATA_HEADER),
    "account": ("/api/panel", ACCOUNT_HEADER),
}


@dataclass
class RenidlyConfig:
    """Client configuration. Every field is optional and has a sensible default.

    Build only what you need::

        from renidly import Renidly, RenidlyConfig
        cfg = RenidlyConfig(timeout=10, max_retries=5, auto_rate_limit=True)
        client = Renidly("rnd-...", config=cfg)
    """

    api_key: Optional[str] = None
    """API key. Falls back to the ``RENIDLY_API_KEY`` env var. The client's
    positional ``api_key`` argument, if given, takes precedence over this."""
    timeout: float = 30.0
    """Per-request timeout in seconds."""
    max_retries: int = 2
    """Auto-retries on 429 / 503 / connection errors (exponential backoff + jitter)."""
    backoff_factor: float = 0.5
    """Base seconds for the exponential backoff between retries."""
    base_url: str = DEFAULT_BASE_URL
    """Override the API host (e.g. a staging environment)."""
    proxy: Optional[str] = None
    """HTTP(S) proxy URL."""
    default_headers: Dict[str, str] = field(default_factory=dict)
    """Extra headers sent on every request."""

    # ── Behavior flags ──
    unwrap_data_obj: bool = True
    """Return the unwrapped ``data`` model. If False, return the full envelope."""
    raise_on_not_found: bool = False
    """Single lookups: raise ``NotFoundError`` instead of returning ``None`` when empty."""
    raise_on_api_error: bool = True
    """Map ``success:false`` responses to typed exceptions."""

    # ── Built-in client-side rate limiting ──
    auto_rate_limit: bool = False
    """Throttle requests to stay under your per-minute limit automatically."""
    rate_limit_per_minute: Optional[int] = None
    """Fixed per-minute limit. REQUIRED for enterprise keys; optional override otherwise."""
    rate_limit_safety: float = 1.0
    """Fraction of the limit to target (e.g. 0.9 leaves headroom for clock skew)."""
    rate_limit_refresh: float = 300.0
    """Seconds between tier re-fetches for auto-fetched (non-fixed) limits."""

    def __post_init__(self) -> None:
        if self.api_key is None:
            self.api_key = os.environ.get("RENIDLY_API_KEY")
        self.base_url = self.base_url.rstrip("/")

    def _url_for(self, service: str, path: str) -> str:
        prefix, _ = SERVICES[service]
        return f"{self.base_url}{prefix}{path}"

    def _auth_header_for(self, service: str) -> str:
        _, header = SERVICES[service]
        return header


Config = RenidlyConfig  # internal alias
