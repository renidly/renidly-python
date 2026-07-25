"""Account & Credits (``r.account``).

Read your live balance, tier, and per-minute rate limit with your key; the tier
ladder and per-route costs are public (no key). The SDK sends the correct
``X-AUTHAPI-Key`` header and the required trailing slash on ``/k/`` routes for
you — you never think about either.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .._models import RenidlyModel
from .._pagination import AsyncRenidlyList, RenidlyList
from ._base import AsyncResource, SyncResource

_SVC = "account"


def _collection(items_key: str):
    """Build a paginator for a non-paginated ``data.<items_key>`` array.

    Account collection endpoints (tiers, route costs) return everything in one
    response, so this reports ``has_more=False`` and just hands back the items.
    """

    def paginator(env: Dict[str, Any], _params: Dict[str, Any]) -> Tuple[List[Any], bool, Optional[Dict[str, Any]], Optional[str]]:
        data = env.get("data") or {}
        return data.get(items_key) or [], False, None, None

    return paginator


class Account(SyncResource):
    """Balance, tier, and pricing for your account."""

    def balance(self, *, options: Optional[Dict[str, Any]] = None) -> Optional[RenidlyModel]:
        """Get your current credit balance.

        Calls ``GET /api/panel/credits/balance/k/`` and returns just the balance
        (``data.balance``). Lightweight — use it for low-balance alerts.

        Example::

            print(client.account.balance().balance)   # -> 19873.0
        """
        return self._one(_SVC, "GET", "/credits/balance/k/", model=RenidlyModel, options=options)

    def tier(self, *, options: Optional[Dict[str, Any]] = None) -> Optional[RenidlyModel]:
        """Get your tier, per-minute rate limit, balance, and neighbouring tiers.

        Calls ``GET /api/panel/credits/tier/k/``. Read ``.current_tier.name`` and
        ``.current_tier.limit_per_minute`` (the number to feed a rate limiter),
        plus ``.next_tier.credits_needed`` to reach the next tier.

        Example::

            t = client.account.tier()
            print(t.current_tier.name, t.current_tier.limit_per_minute)
        """
        return self._one(_SVC, "GET", "/credits/tier/k/", model=RenidlyModel, options=options)

    def enterprise_balance(self, *, options: Optional[Dict[str, Any]] = None) -> Optional[RenidlyModel]:
        """Get the credit balance for an Enterprise workspace.

        Calls ``GET /api/panel/credits/balance/k/enterprise/`` with your key (the
        backend decides regular vs enterprise).

        Example::

            print(client.account.enterprise_balance().balance)
        """
        return self._one(_SVC, "GET", "/credits/balance/k/enterprise/", model=RenidlyModel, options=options)

    def tiers(self, *, options: Optional[Dict[str, Any]] = None) -> RenidlyList[RenidlyModel]:
        """List the full public tier ladder — **no key required**.

        Calls ``GET /api/panel/user/sub/tiers/`` and returns a ``RenidlyList`` of
        tiers (``id``, ``name``, ``min_credits``, ``max_credits``,
        ``limit_per_minute``, ``credits_per_dollar``).

        Example::

            for tier in client.account.tiers():
                print(tier.name, tier.limit_per_minute)
        """
        return self._list(
            _SVC, "GET", "/user/sub/tiers/", model=RenidlyModel, paginator=_collection("results"), options=options
        )

    def route_costs(self, *, options: Optional[Dict[str, Any]] = None) -> RenidlyList[RenidlyModel]:
        """List per-route credit costs — **no key required**.

        Calls ``GET /api/panel/credits/routes/costs/``. Only routes whose cost is
        **not 1** are returned; anything absent costs 1 credit, and
        ``credits_cost == 0`` means free.

        Example::

            costs = {r.route: r.credits_cost for r in client.account.route_costs()}
        """
        return self._list(
            _SVC, "GET", "/credits/routes/costs/", model=RenidlyModel, paginator=_collection("routes"), options=options
        )


class AsyncAccount(AsyncResource):
    """Async version of :class:`Account`. Same methods; ``await`` them."""

    async def balance(self, *, options: Optional[Dict[str, Any]] = None) -> Optional[RenidlyModel]:
        """Get your current credit balance. See :meth:`Account.balance`."""
        return await self._one(_SVC, "GET", "/credits/balance/k/", model=RenidlyModel, options=options)

    async def tier(self, *, options: Optional[Dict[str, Any]] = None) -> Optional[RenidlyModel]:
        """Get your tier + rate limit. See :meth:`Account.tier`."""
        return await self._one(_SVC, "GET", "/credits/tier/k/", model=RenidlyModel, options=options)

    async def enterprise_balance(self, *, options: Optional[Dict[str, Any]] = None) -> Optional[RenidlyModel]:
        """Get an Enterprise workspace's balance. See :meth:`Account.enterprise_balance`."""
        return await self._one(_SVC, "GET", "/credits/balance/k/enterprise/", model=RenidlyModel, options=options)

    async def tiers(self, *, options: Optional[Dict[str, Any]] = None) -> AsyncRenidlyList[RenidlyModel]:
        """List the public tier ladder (no key). See :meth:`Account.tiers`."""
        return await self._list(
            _SVC, "GET", "/user/sub/tiers/", model=RenidlyModel, paginator=_collection("results"), options=options
        )

    async def route_costs(self, *, options: Optional[Dict[str, Any]] = None) -> AsyncRenidlyList[RenidlyModel]:
        """List per-route costs (no key). See :meth:`Account.route_costs`."""
        return await self._list(
            _SVC, "GET", "/credits/routes/costs/", model=RenidlyModel, paginator=_collection("routes"), options=options
        )
