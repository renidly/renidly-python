"""Email API (``r.emails``).

Verify deliverability, find work emails, reverse-resolve the person/company
behind an address, list known contacts for a domain, and run verify/find in
bulk. Single calls return a model; ``prospects`` returns a paginated list; the
``*_batch`` methods return a :class:`~renidly._batch.BatchJob`.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .._batch import AsyncBatchJob, BatchJob
from .._models import RenidlyModel
from .._pagination import AsyncRenidlyList, RenidlyList
from ._base import AsyncResource, SyncResource

_SVC = "emails"


def _prospects_paginator(env: Dict[str, Any], params: Dict[str, Any]) -> Tuple[List[Any], bool, Optional[Dict[str, Any]], Optional[str]]:
    """Paginate the prospects list, which nests items + cursor under ``data``."""
    d = env.get("data") or {}
    items = d.get("prospects") or []
    nc = d.get("next_cursor")
    has_more = bool(nc)
    nxt = {**params, "cursor": nc} if has_more else None
    return items, has_more, nxt, nc


class Emails(SyncResource):
    """Deliverability, discovery, and reverse resolution for business email."""

    def verify(self, email: str, *, options: Optional[Dict[str, Any]] = None) -> Optional[RenidlyModel]:
        """Check whether an email address can receive mail, and flag risks.

        Calls ``GET /api/emails/v1/verify``. Returns a verdict with ``email``,
        ``deliverable`` (bool), ``reason`` (e.g. ``mailbox_accepts``,
        ``mailbox_rejected``, ``catch_all``, ``disposable``…), ``catch_all``, and
        ``mx_hosts``. Always returns a verdict (never a not-found).

        Example::

            v = client.emails.verify("sundar@google.com")
            print(v.deliverable, v.reason)   # True mailbox_accepts
        """
        return self._one(_SVC, "GET", "/verify", params={"email": email}, options=options)

    def find(self, *, first_name: str, last_name: str, domain: str, options: Optional[Dict[str, Any]] = None) -> Optional[RenidlyModel]:
        """Discover a person's work email from name + company domain.

        Calls ``GET /api/emails/v1/find``. ``domain`` must be a bare hostname
        (``acme.com``). Returns ``email`` (empty if not found), ``found`` (bool),
        ``catch_all``, and ``confidence`` (``high``/``low``).

        Example::

            f = client.emails.find(first_name="Patrick", last_name="Collison", domain="stripe.com")
            print(f.email, f.confidence)     # patrick@stripe.com high
        """
        return self._one(_SVC, "GET", "/find", params={"first_name": first_name, "last_name": last_name, "domain": domain}, options=options)

    def find_by_url(self, url: str, *, options: Optional[Dict[str, Any]] = None) -> Optional[RenidlyModel]:
        """Find a work email from a professional profile URL.

        Calls ``GET /api/emails/v1/find/linkedin``. Pass the profile URL (or its
        public slug). Returns the same fields as :meth:`find` plus the resolved
        ``first_name``/``last_name``/``domain``/``company``.

        Example::

            client.emails.find_by_url("https://www.linkedin.com/in/sundarpichai/")
        """
        return self._one(_SVC, "GET", "/find/linkedin", params={"url": url}, options=options)

    def reverse(self, email: str, *, options: Optional[Dict[str, Any]] = None) -> Optional[RenidlyModel]:
        """Resolve the person and company behind a business email.

        Calls ``GET /api/emails/v1/reverse``. Business mailboxes only — public
        providers / role accounts / disposable addresses are rejected (422).
        Returns ``found``, ``confidence``, ``person`` and ``current_company``
        objects (drill in with dotted access).

        Example::

            r = client.emails.reverse("john@acme.com")
            if r.found: print(r.person.full_name, r.current_company.name)
        """
        return self._one(_SVC, "GET", "/reverse", params={"email": email}, options=options)

    def prospects(self, domain: str, kind: str, *, cursor: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> RenidlyList[RenidlyModel]:
        """Page emails already known for a company domain.

        Calls ``GET /api/emails/v1/prospects``. ``kind`` is ``full`` (all) or
        ``verified_only`` (deliverable). Returns a ``RenidlyList`` (20/page); use
        ``.auto_paging_iter()`` to walk them all. Billed per email returned.

        Example::

            for p in client.emails.prospects("acme.com", kind="verified_only").auto_paging_iter():
                print(p.email)
        """
        return self._list(_SVC, "GET", "/prospects", params={"domain": domain, "kind": kind, "cursor": cursor}, paginator=_prospects_paginator, options=options)

    def verify_batch(self, emails: List[str], *, options: Optional[Dict[str, Any]] = None) -> BatchJob:
        """Submit a bulk email-verification job (up to 1000).

        Calls ``POST /api/emails/v1/verify/batch`` and returns a
        :class:`~renidly._batch.BatchJob` immediately. Poll it with ``.wait()``
        (blocking) or ``.stream()`` (generator). Each address is billed on verdict.

        Example::

            job = client.emails.verify_batch(["a@x.com", "b@y.com"])
            for row in job.wait().results:
                print(row.email, row.deliverable)
        """
        r = self._client._transport.request("POST", _SVC, "/verify/batch", json={"emails": emails}, options=options)
        if r.error is not None:
            raise r.error
        return BatchJob(self._client, _SVC, "/verify/batch", (r.data or {}).get("job_id"),
                        results_key="results", keyed=True, model=RenidlyModel, options=options)

    def find_batch(self, queries: List[Dict[str, str]], *, options: Optional[Dict[str, Any]] = None) -> BatchJob:
        """Submit a bulk work-email-finding job (up to 1000).

        Calls ``POST /api/emails/v1/find/batch``. Each query is a dict of
        ``first_name``/``last_name``/``domain``. Returns a
        :class:`~renidly._batch.BatchJob`; collect with ``.wait()``/``.stream()``.

        Example::

            job = client.emails.find_batch([{"first_name": "A", "last_name": "B", "domain": "acme.com"}])
            print(job.wait().results)
        """
        r = self._client._transport.request("POST", _SVC, "/find/batch", json={"queries": queries}, options=options)
        if r.error is not None:
            raise r.error
        return BatchJob(self._client, _SVC, "/find/batch", (r.data or {}).get("job_id"),
                        results_key="results", keyed=False, model=RenidlyModel, options=options)


class AsyncEmails(AsyncResource):
    """Async version of :class:`Emails`. Same methods; ``await`` them."""

    async def verify(self, email: str, *, options: Optional[Dict[str, Any]] = None) -> Optional[RenidlyModel]:
        """Verify deliverability. See :meth:`Emails.verify`."""
        return await self._one(_SVC, "GET", "/verify", params={"email": email}, options=options)

    async def find(self, *, first_name: str, last_name: str, domain: str, options: Optional[Dict[str, Any]] = None) -> Optional[RenidlyModel]:
        """Find a work email from name + domain. See :meth:`Emails.find`."""
        return await self._one(_SVC, "GET", "/find", params={"first_name": first_name, "last_name": last_name, "domain": domain}, options=options)

    async def find_by_url(self, url: str, *, options: Optional[Dict[str, Any]] = None) -> Optional[RenidlyModel]:
        """Find a work email from a profile URL. See :meth:`Emails.find_by_url`."""
        return await self._one(_SVC, "GET", "/find/linkedin", params={"url": url}, options=options)

    async def reverse(self, email: str, *, options: Optional[Dict[str, Any]] = None) -> Optional[RenidlyModel]:
        """Resolve the person/company behind an email. See :meth:`Emails.reverse`."""
        return await self._one(_SVC, "GET", "/reverse", params={"email": email}, options=options)

    async def prospects(self, domain: str, kind: str, *, cursor: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> AsyncRenidlyList[RenidlyModel]:
        """Page known emails for a domain. See :meth:`Emails.prospects`."""
        return await self._list(_SVC, "GET", "/prospects", params={"domain": domain, "kind": kind, "cursor": cursor}, paginator=_prospects_paginator, options=options)

    async def verify_batch(self, emails: List[str], *, options: Optional[Dict[str, Any]] = None) -> AsyncBatchJob:
        """Submit a bulk verify job. See :meth:`Emails.verify_batch`."""
        r = await self._client._transport.request("POST", _SVC, "/verify/batch", json={"emails": emails}, options=options)
        if r.error is not None:
            raise r.error
        return AsyncBatchJob(self._client, _SVC, "/verify/batch", (r.data or {}).get("job_id"),
                             results_key="results", keyed=True, model=RenidlyModel, options=options)

    async def find_batch(self, queries: List[Dict[str, str]], *, options: Optional[Dict[str, Any]] = None) -> AsyncBatchJob:
        """Submit a bulk find job. See :meth:`Emails.find_batch`."""
        r = await self._client._transport.request("POST", _SVC, "/find/batch", json={"queries": queries}, options=options)
        if r.error is not None:
            raise r.error
        return AsyncBatchJob(self._client, _SVC, "/find/batch", (r.data or {}).get("job_id"),
                             results_key="results", keyed=False, model=RenidlyModel, options=options)
