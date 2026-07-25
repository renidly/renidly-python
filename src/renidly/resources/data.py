"""Data API (``r.data``).

Clean, deduplicated professional records addressable by stable opaque IDs
(``prsn_``/``org_``/``inst_``/``skl_``) or rich filters. ``retrieve`` returns a
single model (or ``None`` when nothing resolved); ``search``/``employees``/
``alumni`` return a paginated ``RenidlyList``; ``enrich_batch`` returns a
:class:`~renidly._batch.BatchJob`. Multi-filter methods take typed ``**params``
(``Unpack[...]``) so your IDE autocompletes every filter name.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from typing_extensions import Unpack

from .._batch import AsyncBatchJob, BatchJob
from .._models import RenidlyModel
from .._pagination import AsyncRenidlyList, RenidlyList
from ..types.params import (
    CompaniesEmployeesParams,
    CompaniesSearchParams,
    InstitutionsAlumniParams,
    JobChangesSearchParams,
    PeopleSearchParams,
)
from ._base import AsyncResource, SyncResource
from ._paginators import cursor_paginator, page_paginator

_SVC = "data"


def _enrich_body(ids: Optional[List[str]], handles: Optional[List[str]], live: bool) -> Dict[str, Any]:
    return {"ids": ids or [], "handles": handles or [], "enrich_live": live}


# ─────────────────────────── sync ───────────────────────────
class People(SyncResource):
    """People records: retrieve one, search many, or enrich a list in bulk."""

    def retrieve(self, id: Optional[str] = None, *, handle: Optional[str] = None, options=None) -> Optional[RenidlyModel]:
        """Retrieve one professional record by stable id or public handle.

        Calls ``GET /api/data/v1/people/profile``. Pass ``id`` (opaque ``prsn_``,
        preferred/stable) **or** ``handle``. Returns the full record (drill in
        with dotted access), or ``None`` if nothing resolved.

        Example::

            p = client.data.people.retrieve(id="prsn_...")
            if p: print(p.first_name, p.headline)
        """
        return self._one(_SVC, "GET", "/people/profile", params={"id": id, "handle": handle}, options=options)

    def search(self, *, options=None, **params: Unpack[PeopleSearchParams]) -> RenidlyList[RenidlyModel]:
        """Filter professional records; cursor-paginated.

        Calls ``GET /api/data/v1/people/search``. Pass any documented filter as a
        keyword (``title``, ``current_only``, ``skills``, ``geo_country_code``,
        …); all combine with AND, ``None`` values are omitted. Returns a
        ``RenidlyList`` — index it, iterate it, or ``.auto_paging_iter()``.

        Example::

            for p in client.data.people.search(title="cto", current_only=True).auto_paging_iter():
                print(p.headline)
        """
        return self._list(_SVC, "GET", "/people/search", params=params, paginator=cursor_paginator, options=options)

    def enrich_batch(self, *, ids=None, handles=None, live=False, options=None) -> BatchJob:
        """Submit an async bulk people-enrichment job (up to 1000).

        Calls ``POST /api/data/v1/people/batch/enrich`` and returns a
        :class:`~renidly._batch.BatchJob` immediately. Pass ``ids`` and/or
        ``handles``; ``live=True`` forces the freshest per-item resolution.
        Collect with ``.wait()`` (blocking) or ``.stream()`` (generator).

        Example::

            job = client.data.people.enrich_batch(handles=["a", "b"], live=True)
            result = job.wait()
            print(result.resolved, result.not_found)
        """
        r = self._client._transport.request(
            "POST", _SVC, "/people/batch/enrich", json=_enrich_body(ids, handles, live), options=options
        )
        if r.error is not None:
            raise r.error
        return BatchJob(self._client, _SVC, "/people/batch/enrich", (r.data or {}).get("job_id"),
                        results_key="profiles", keyed=True, model=RenidlyModel, options=options)


class Companies(SyncResource):
    """Organization records: retrieve, search, list employees, or enrich in bulk."""

    def retrieve(self, id: Optional[str] = None, *, slug: Optional[str] = None, options=None) -> Optional[RenidlyModel]:
        """Retrieve one organization by opaque ``org_`` id or public slug.

        Calls ``GET /api/data/v1/companies/company``. Returns firmographics
        (name, slug, url, industry, employee count, HQ, funding…) or ``None``.

        Example::

            co = client.data.companies.retrieve(slug="google")
            print(co.name, co.id)
        """
        return self._one(_SVC, "GET", "/companies/company", params={"id": id, "slug": slug}, options=options)

    def search(self, *, options=None, **params: Unpack[CompaniesSearchParams]) -> RenidlyList[RenidlyModel]:
        """Filter organizations; cursor-paginated.

        Calls ``GET /api/data/v1/companies/search``. Requires ``name`` or
        ``website``; plus ``staff_count_min/max``, ``industries``, ``hq_city``,
        ``founded``, etc. Returns a ``RenidlyList``.

        Example::

            for c in client.data.companies.search(name="stripe", staff_count_min=100):
                print(c.name)
        """
        return self._list(_SVC, "GET", "/companies/search", params=params, paginator=cursor_paginator, options=options)

    def employees(self, slug: str, *, options=None, **params: Unpack[CompaniesEmployeesParams]) -> RenidlyList[RenidlyModel]:
        """List people who work (or worked) at an organization; cursor-paginated.

        Calls ``GET /api/data/v1/companies/employees``. ``slug`` is required; add
        ``current_only``, ``title`` (partial job-title match), geo, ``start_year``,
        or ``sort``. Returns a ``RenidlyList`` of people.

        Example::

            eng = client.data.companies.employees("google", title="engineer", current_only=True)
        """
        return self._list(_SVC, "GET", "/companies/employees", params={**params, "slug": slug}, paginator=cursor_paginator, options=options)

    def enrich_batch(self, *, ids=None, handles=None, live=False, options=None) -> BatchJob:
        """Submit an async bulk company-enrichment job (up to 1000).

        Calls ``POST /api/data/v1/companies/batch/enrich``. Same shape as
        :meth:`People.enrich_batch`; results come back under ``.results`` keyed to
        your inputs, with misses in ``.not_found``.

        Example::

            client.data.companies.enrich_batch(ids=["org_a", "org_b"]).wait()
        """
        r = self._client._transport.request(
            "POST", _SVC, "/companies/batch/enrich", json=_enrich_body(ids, handles, live), options=options
        )
        if r.error is not None:
            raise r.error
        return BatchJob(self._client, _SVC, "/companies/batch/enrich", (r.data or {}).get("job_id"),
                        results_key="companies", keyed=True, model=RenidlyModel, options=options)


class Institutions(SyncResource):
    """Educational institutions: retrieve, search, and browse alumni."""

    def retrieve(self, normalized_name: str, *, options=None) -> Optional[RenidlyModel]:
        """Retrieve one institution by its ``normalized_name`` (lowercase, hyphenated).

        Calls ``GET /api/data/v1/institutions/institution``. Returns name,
        normalized name, url, and opaque ``inst_`` id, or ``None``.

        Example::

            client.data.institutions.retrieve("stanford")
        """
        return self._one(_SVC, "GET", "/institutions/institution",
                         params={"normalized_name": normalized_name}, options=options)

    def search(self, name: str, *, page=None, limit=None, options=None) -> RenidlyList[RenidlyModel]:
        """Partial-match search on institution name; page-paginated.

        Calls ``GET /api/data/v1/institutions/search`` (``name`` min 3 chars).
        Use it to discover an institution's ``normalized_name`` or ``inst_`` id.

        Example::

            client.data.institutions.search("stanford", limit=5)
        """
        return self._list(_SVC, "GET", "/institutions/search",
                          params={"name": name, "page": page, "limit": limit}, paginator=page_paginator, options=options)

    def alumni(self, normalized_name: str, *, options=None, **params: Unpack[InstitutionsAlumniParams]) -> RenidlyList[RenidlyModel]:
        """Browse alumni / current students of an institution; page-paginated.

        Calls ``GET /api/data/v1/institutions/alumni``. Each result is a person
        plus their education record. Add ``current_only``, ``degree``,
        ``field_of_study``, year ranges, geo, or ``sort``.

        Example::

            for a in client.data.institutions.alumni("stanford", degree="MBA").auto_paging_iter():
                print(a.first_name)
        """
        return self._list(_SVC, "GET", "/institutions/alumni", params={**params, "normalized_name": normalized_name}, paginator=page_paginator, options=options)


class Skills(SyncResource):
    """The skill catalog: retrieve one by id, or search by name."""

    def retrieve(self, id: str, *, options=None) -> Optional[RenidlyModel]:
        """Retrieve one skill by its opaque ``skl_`` id.

        Calls ``GET /api/data/v1/skills/skill``. Returns ``id``, ``name``,
        ``normalized_name``, or ``None``.

        Example::

            client.data.skills.retrieve("skl_...")
        """
        return self._one(_SVC, "GET", "/skills/skill", params={"id": id}, options=options)

    def search(self, name: str, *, page=None, limit=None, options=None) -> RenidlyList[RenidlyModel]:
        """Partial-match search on skill name; page-paginated (``name`` min 3 chars).

        Calls ``GET /api/data/v1/skills/search``. Use it to find a skill's
        ``skl_`` id or its ``normalized_name`` for the people-search ``skills`` filter.

        Example::

            client.data.skills.search("python", limit=3)
        """
        return self._list(_SVC, "GET", "/skills/search",
                          params={"name": name, "page": page, "limit": limit}, paginator=page_paginator, options=options)


class JobChanges(SyncResource):
    """Recent professional job-change events (joins / leaves / title changes)."""

    def search(self, *, options=None, **params: Unpack[JobChangesSearchParams]) -> RenidlyList[RenidlyModel]:
        """Search recent job-change events; page-paginated.

        Calls ``GET /api/data/v1/job-changes/search``. Filter by ``event_type``
        (``joined``/``left``/``title_change``), ``organization_ids``, geo,
        ``title``, or ``days_ago``. Great for trigger-based prospecting.

        Example::

            client.data.job_changes.search(event_type="joined", days_ago=30)
        """
        return self._list(_SVC, "GET", "/job-changes/search", params=params, paginator=page_paginator, options=options)


class Data:
    """The Data-API namespace: ``people``, ``companies``, ``institutions``, ``skills``, ``job_changes``."""

    def __init__(self, client: Any) -> None:
        self.people = People(client)
        self.companies = Companies(client)
        self.institutions = Institutions(client)
        self.skills = Skills(client)
        self.job_changes = JobChanges(client)


# ─────────────────────────── async ───────────────────────────
class AsyncPeople(AsyncResource):
    """Async :class:`People`."""

    async def retrieve(self, id=None, *, handle=None, options=None) -> Optional[RenidlyModel]:
        """Retrieve one person. See :meth:`People.retrieve`."""
        return await self._one(_SVC, "GET", "/people/profile", params={"id": id, "handle": handle}, options=options)

    async def search(self, *, options=None, **params: Unpack[PeopleSearchParams]) -> AsyncRenidlyList[RenidlyModel]:
        """Filter people. See :meth:`People.search`."""
        return await self._list(_SVC, "GET", "/people/search", params=params, paginator=cursor_paginator, options=options)

    async def enrich_batch(self, *, ids=None, handles=None, live=False, options=None) -> AsyncBatchJob:
        """Bulk people enrichment. See :meth:`People.enrich_batch`."""
        r = await self._client._transport.request(
            "POST", _SVC, "/people/batch/enrich", json=_enrich_body(ids, handles, live), options=options
        )
        if r.error is not None:
            raise r.error
        return AsyncBatchJob(self._client, _SVC, "/people/batch/enrich", (r.data or {}).get("job_id"),
                             results_key="profiles", keyed=True, model=RenidlyModel, options=options)


class AsyncCompanies(AsyncResource):
    """Async :class:`Companies`."""

    async def retrieve(self, id=None, *, slug=None, options=None) -> Optional[RenidlyModel]:
        """Retrieve one company. See :meth:`Companies.retrieve`."""
        return await self._one(_SVC, "GET", "/companies/company", params={"id": id, "slug": slug}, options=options)

    async def search(self, *, options=None, **params: Unpack[CompaniesSearchParams]) -> AsyncRenidlyList[RenidlyModel]:
        """Filter companies. See :meth:`Companies.search`."""
        return await self._list(_SVC, "GET", "/companies/search", params=params, paginator=cursor_paginator, options=options)

    async def employees(self, slug, *, options=None, **params: Unpack[CompaniesEmployeesParams]) -> AsyncRenidlyList[RenidlyModel]:
        """List a company's employees. See :meth:`Companies.employees`."""
        return await self._list(_SVC, "GET", "/companies/employees", params={**params, "slug": slug}, paginator=cursor_paginator, options=options)

    async def enrich_batch(self, *, ids=None, handles=None, live=False, options=None) -> AsyncBatchJob:
        """Bulk company enrichment. See :meth:`Companies.enrich_batch`."""
        r = await self._client._transport.request(
            "POST", _SVC, "/companies/batch/enrich", json=_enrich_body(ids, handles, live), options=options
        )
        if r.error is not None:
            raise r.error
        return AsyncBatchJob(self._client, _SVC, "/companies/batch/enrich", (r.data or {}).get("job_id"),
                             results_key="companies", keyed=True, model=RenidlyModel, options=options)


class AsyncInstitutions(AsyncResource):
    """Async :class:`Institutions`."""

    async def retrieve(self, normalized_name, *, options=None) -> Optional[RenidlyModel]:
        """Retrieve one institution. See :meth:`Institutions.retrieve`."""
        return await self._one(_SVC, "GET", "/institutions/institution",
                               params={"normalized_name": normalized_name}, options=options)

    async def search(self, name, *, page=None, limit=None, options=None) -> AsyncRenidlyList[RenidlyModel]:
        """Search institutions. See :meth:`Institutions.search`."""
        return await self._list(_SVC, "GET", "/institutions/search",
                                params={"name": name, "page": page, "limit": limit}, paginator=page_paginator, options=options)

    async def alumni(self, normalized_name, *, options=None, **params: Unpack[InstitutionsAlumniParams]) -> AsyncRenidlyList[RenidlyModel]:
        """Browse alumni. See :meth:`Institutions.alumni`."""
        return await self._list(_SVC, "GET", "/institutions/alumni", params={**params, "normalized_name": normalized_name}, paginator=page_paginator, options=options)


class AsyncSkills(AsyncResource):
    """Async :class:`Skills`."""

    async def retrieve(self, id, *, options=None) -> Optional[RenidlyModel]:
        """Retrieve one skill. See :meth:`Skills.retrieve`."""
        return await self._one(_SVC, "GET", "/skills/skill", params={"id": id}, options=options)

    async def search(self, name, *, page=None, limit=None, options=None) -> AsyncRenidlyList[RenidlyModel]:
        """Search skills. See :meth:`Skills.search`."""
        return await self._list(_SVC, "GET", "/skills/search",
                                params={"name": name, "page": page, "limit": limit}, paginator=page_paginator, options=options)


class AsyncJobChanges(AsyncResource):
    """Async :class:`JobChanges`."""

    async def search(self, *, options=None, **params: Unpack[JobChangesSearchParams]) -> AsyncRenidlyList[RenidlyModel]:
        """Search job-change events. See :meth:`JobChanges.search`."""
        return await self._list(_SVC, "GET", "/job-changes/search", params=params, paginator=page_paginator, options=options)


class AsyncData:
    """Async Data-API namespace. Mirrors :class:`Data`."""

    def __init__(self, client: Any) -> None:
        self.people = AsyncPeople(client)
        self.companies = AsyncCompanies(client)
        self.institutions = AsyncInstitutions(client)
        self.skills = AsyncSkills(client)
        self.job_changes = AsyncJobChanges(client)
