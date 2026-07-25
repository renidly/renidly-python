"""Paginator functions for the standard Data-API list envelopes.

Each returns ``(items, has_more, next_params, next_cursor)`` given the response
envelope and the params used for the current page.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

Page = Tuple[List[Any], bool, Optional[Dict[str, Any]], Optional[str]]


def cursor_paginator(env: Dict[str, Any], params: Dict[str, Any]) -> Page:
    items = env.get("data") or []
    pag = env.get("pagination") or {}
    has_more = bool(pag.get("has_more"))
    nc = pag.get("next_cursor")
    nxt = {**params, "cursor": nc} if (has_more and nc) else None
    return items, has_more, nxt, nc


def page_paginator(env: Dict[str, Any], params: Dict[str, Any]) -> Page:
    items = env.get("data") or []
    pag = env.get("pagination") or {}
    has_more = bool(pag.get("has_more"))
    page = int(params.get("page") or 1)
    nxt = {**params, "page": page + 1} if has_more else None
    return items, has_more, nxt, None
