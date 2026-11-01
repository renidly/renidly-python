"""Phone API (``r.phones``).

Get a professional's phone numbers from their profile URL, and resolve the
professional behind a phone number.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .._models import RenidlyModel
from ._base import AsyncResource, SyncResource

_SVC = "phones"


class Phones(SyncResource):
    """Phone numbers from a profile, and the person behind a number."""

    def find(self, url: str, *, options: Optional[Dict[str, Any]] = None) -> Optional[RenidlyModel]:
        """A person's phone numbers, best first, from their profile URL or username.

        Calls ``GET /api/phones/v1/find``. Returns ``found``, ``person`` and
        ``phones`` (each with ``phone`` in E.164, ``type``, ``line_type``,
        ``country``, ``is_shared``). ``found`` is false — billed 1 credit — when
        the profile doesn't exist or has no known numbers.

        Example::

            p = client.phones.find("https://www.linkedin.com/in/ryanroslansky")
            if p.found: print(p.phones[0].phone)
        """
        return self._one(_SVC, "GET", "/find", params={"url": url}, options=options)

    def reverse(self, phone: str, *, country: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> Optional[RenidlyModel]:
        """The people behind a phone number (up to 3 when it is shared).

        Calls ``GET /api/phones/v1/reverse``. ``phone`` may be in any common
        format; ``country`` is the ISO code for a number without a country code
        (default ``US``). Returns ``phone`` (E.164), ``found`` and
        ``candidates``. An unknown number is free.

        Example::

            r = client.phones.reverse("020 7946 0958", country="GB")
            for c in r.candidates: print(c.full_name, c.linkedin_url)
        """
        return self._one(_SVC, "GET", "/reverse", params={"phone": phone, "country": country}, options=options)


class AsyncPhones(AsyncResource):
    """Async version of :class:`Phones`. Same methods; ``await`` them."""

    async def find(self, url: str, *, options: Optional[Dict[str, Any]] = None) -> Optional[RenidlyModel]:
        """A person's phone numbers. See :meth:`Phones.find`."""
        return await self._one(_SVC, "GET", "/find", params={"url": url}, options=options)

    async def reverse(self, phone: str, *, country: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> Optional[RenidlyModel]:
        """The people behind a phone number. See :meth:`Phones.reverse`."""
        return await self._one(_SVC, "GET", "/reverse", params={"phone": phone, "country": country}, options=options)
