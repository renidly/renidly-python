"""Live API (``r.live``).

Resolve a single B2B subject (person, organization, opportunity, activity) or
run a discovery search, returning the freshest snapshot on demand. Query params
are the API's native camelCase (``entityId``…); methods map friendly Python args
onto them. Single lookups return a model; list endpoints return a
``RenidlyList`` — ``_live_paginator`` auto-detects the items array and whether the
endpoint pages by cursor (``nextCursor``) or offset (``start``/``count``).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from typing_extensions import Unpack

from .._models import RenidlyModel
from .._pagination import AsyncRenidlyList, RenidlyList
from ..types.params import (
    DiscoverOpportunitiesParams,
    DiscoverOrganizationsParams,
    DiscoverPeopleParams,
)
from ._base import AsyncResource, SyncResource

_SVC = "live"


def _live_paginator(env: Dict[str, Any], params: Dict[str, Any]) -> Tuple[List[Any], bool, Optional[Dict[str, Any]], Optional[str]]:
    """Adapt the varied Live list shapes to the common paginator contract.

    Finds the items (the first list under ``data``); if the response carries a
    ``nextCursor`` it pages by cursor, otherwise by ``start``/``count`` offset.
    """
    d = env.get("data") or {}
    items: List[Any] = next((v for v in d.values() if isinstance(v, list)), [])
    nc = d.get("nextCursor")
    if nc:
        return items, True, {**params, "cursor": nc}, nc
    has_more = bool(d.get("hasMore"))
    start = int(params.get("start") or 0)
    count = int(params.get("count") or len(items) or 20)
    nxt = {**params, "start": start + count} if has_more else None
    return items, has_more, nxt, None


# ─────────────────────────── sync ───────────────────────────
class LivePeople(SyncResource):
    """A person's live profile, work history, recommendations, and network."""

    def enrich(self, entity_id: Optional[str] = None, *, handle: Optional[str] = None, options=None) -> Optional[RenidlyModel]:
        """Retrieve one professional's full live profile.

        Calls ``GET /api/v2/person/enrich``. Pass ``entity_id`` (stable) or
        ``handle``. Returns names, headline, counts, flags, industry, location.

        Example::

            p = client.live.people.enrich(handle="williamhgates")
            print(p.firstName)
        """
        return self._one(_SVC, "GET", "/person/enrich", params={"entityId": entity_id, "handle": handle}, options=options)

    def resolve_handle(self, handle: str, *, options=None) -> Optional[RenidlyModel]:
        """Resolve a public handle to a stable ``entityId`` (do this once, reuse it).

        Calls ``GET /api/v2/person/resolve-handle``.

        Example::

            eid = client.live.people.resolve_handle("williamhgates").entityId
        """
        return self._one(_SVC, "GET", "/person/resolve-handle", params={"handle": handle}, options=options)

    def employment_history(self, entity_id: str, *, options=None) -> Optional[RenidlyModel]:
        """Retrieve a person's complete work history.

        Calls ``GET /api/v2/person/employment-history``. Returns each role with
        organization, title, dates, and skills.

        Example::

            client.live.people.employment_history(eid)
        """
        return self._one(_SVC, "GET", "/person/employment-history", params={"entityId": entity_id}, options=options)

    def endorsements(self, entity_id: str, *, options=None) -> RenidlyList[RenidlyModel]:
        """List recommendations written for a person.

        Calls ``GET /api/v2/person/endorsements``. Returns a ``RenidlyList`` of
        recommendations (text + author).

        Example::

            for rec in client.live.people.endorsements(eid):
                print(rec.text)
        """
        return self._list(_SVC, "GET", "/person/endorsements", params={"entityId": entity_id}, paginator=_live_paginator, options=options)

    def lookalikes(self, entity_id: str, *, options=None) -> RenidlyList[RenidlyModel]:
        """Find similar professional profiles (peers).

        Calls ``GET /api/v2/person/lookalikes``. Expand a shortlist from one
        ideal example.

        Example::

            client.live.people.lookalikes(eid)
        """
        return self._list(_SVC, "GET", "/person/lookalikes", params={"entityId": entity_id}, paginator=_live_paginator, options=options)

    def interests(self, entity_id: str, *, options=None) -> RenidlyList[RenidlyModel]:
        """List entities a person follows (companies, groups, people, newsletters).

        Calls ``GET /api/v2/person/interests``. Useful for personalization.

        Example::

            client.live.people.interests(eid)
        """
        return self._list(_SVC, "GET", "/person/interests", params={"entityId": entity_id}, paginator=_live_paginator, options=options)


class LiveActivities(SyncResource):
    """Professional activity: posts, their content, reactions, and replies."""

    def feed(self, entity_id: str, *, cursor=None, start=None, options=None) -> RenidlyList[RenidlyModel]:
        """List a person's recent posts / activity stream; cursor-paginated.

        Calls ``GET /api/v2/activity/feed``. Returns posts (text, author,
        timestamps, engagement, media). Use ``.auto_paging_iter()`` for older posts.

        Example::

            for post in client.live.activities.feed(eid).auto_paging_iter():
                print(post.text)
        """
        return self._list(_SVC, "GET", "/activity/feed", params={"entityId": entity_id, "cursor": cursor, "start": start}, paginator=_live_paginator, options=options)

    def retrieve(self, entity_id: str, *, options=None) -> Optional[RenidlyModel]:
        """Retrieve one post's full content + top-level comments.

        Calls ``GET /api/v2/activity/details`` (``entity_id`` is the activity id).

        Example::

            client.live.activities.retrieve(activity_id)
        """
        return self._one(_SVC, "GET", "/activity/details", params={"entityId": entity_id}, options=options)

    def reactions(self, entity_id: str, *, start=None, options=None) -> RenidlyList[RenidlyModel]:
        """List the people who reacted to a post; offset-paginated.

        Calls ``GET /api/v2/activity/reactions``. Note: ``start`` must be a
        multiple of 10.

        Example::

            client.live.activities.reactions(activity_id)
        """
        return self._list(_SVC, "GET", "/activity/reactions", params={"entityId": entity_id, "start": start}, paginator=_live_paginator, options=options)

    def replies(self, entity_id: str, *, sort_by=None, count=None, start=None, options=None) -> RenidlyList[RenidlyModel]:
        """List comments/replies on a post; offset-paginated.

        Calls ``GET /api/v2/activity/replies``. ``sort_by`` is ``relevance``
        (default) or ``date_posted`` (newest first).

        Example::

            client.live.activities.replies(activity_id, sort_by="date_posted")
        """
        return self._list(_SVC, "GET", "/activity/replies", params={"entityId": entity_id, "sortBy": sort_by, "count": count, "start": start}, paginator=_live_paginator, options=options)

    def replies_by_author(self, entity_id: str, *, cursor=None, start=None, options=None) -> RenidlyList[RenidlyModel]:
        """List comments authored by a person across posts; cursor-paginated.

        Calls ``GET /api/v2/activity/replies/by-author`` (``entity_id`` is the person).

        Example::

            client.live.activities.replies_by_author(eid)
        """
        return self._list(_SVC, "GET", "/activity/replies/by-author", params={"entityId": entity_id, "cursor": cursor, "start": start}, paginator=_live_paginator, options=options)


class LiveOpportunities(SyncResource):
    """Job postings: details, similar roles, hiring team, and more."""

    def retrieve(self, opportunity_entity_id: str, *, options=None) -> Optional[RenidlyModel]:
        """Retrieve one job posting's full details.

        Calls ``GET /api/v2/opportunity/details``. Returns title, description,
        state, functions, apply url, plus nested organization + location.

        Example::

            client.live.opportunities.retrieve(job_id)
        """
        return self._one(_SVC, "GET", "/opportunity/details", params={"opportunityEntityId": opportunity_entity_id}, options=options)

    def similar(self, opportunity_entity_id: str, *, options=None) -> RenidlyList[RenidlyModel]:
        """List job postings similar to a given one.

        Calls ``GET /api/v2/opportunity/similar``.

        Example::

            client.live.opportunities.similar(job_id)
        """
        return self._list(_SVC, "GET", "/opportunity/similar", params={"opportunityEntityId": opportunity_entity_id}, paginator=_live_paginator, options=options)

    def related_views(self, opportunity_entity_id: str, *, options=None) -> RenidlyList[RenidlyModel]:
        """List "people also viewed" postings (behavioral relatedness).

        Calls ``GET /api/v2/opportunity/related-views``.

        Example::

            client.live.opportunities.related_views(job_id)
        """
        return self._list(_SVC, "GET", "/opportunity/related-views", params={"opportunityEntityId": opportunity_entity_id}, paginator=_live_paginator, options=options)

    def hiring_team(self, opportunity_entity_id: str, *, options=None) -> RenidlyList[RenidlyModel]:
        """List the hiring-team members for a posting.

        Calls ``GET /api/v2/opportunity/hiring-team``. Identify decision-makers.

        Example::

            client.live.opportunities.hiring_team(job_id)
        """
        return self._list(_SVC, "GET", "/opportunity/hiring-team", params={"opportunityEntityId": opportunity_entity_id}, paginator=_live_paginator, options=options)

    def by_person(self, person_entity_id: str, *, count=None, start=None, options=None) -> RenidlyList[RenidlyModel]:
        """List postings created by a person (e.g. a recruiter's open roles).

        Calls ``GET /api/v2/opportunity/by-person``. ``count`` 1–25.

        Example::

            client.live.opportunities.by_person(recruiter_eid)
        """
        return self._list(_SVC, "GET", "/opportunity/by-person", params={"personEntityId": person_entity_id, "count": count, "start": start}, paginator=_live_paginator, options=options)


class LiveOrganizations(SyncResource):
    """Companies: full profile, headcount, peers, affiliates, posts, and jobs."""

    def enrich(self, id: str, *, options=None) -> Optional[RenidlyModel]:
        """Retrieve one company's full live profile.

        Calls ``GET /api/v2/organization/enrich`` (numeric ``id``). Returns
        firmographics, locations, industries, specialties, funding.

        Example::

            client.live.organizations.enrich("1441")
        """
        return self._one(_SVC, "GET", "/organization/enrich", params={"id": id}, options=options)

    def headcount(self, id: str, *, options=None) -> Optional[RenidlyModel]:
        """Get a company's employee count + distribution buckets.

        Calls ``GET /api/v2/organization/headcount`` (by department, seniority,
        location…). Use for sizing and structure signals.

        Example::

            client.live.organizations.headcount("1441")
        """
        return self._one(_SVC, "GET", "/organization/headcount", params={"id": id}, options=options)

    def similar(self, id: str, *, options=None) -> RenidlyList[RenidlyModel]:
        """List similar companies / peers.

        Calls ``GET /api/v2/organization/similar``.

        Example::

            client.live.organizations.similar("1441")
        """
        return self._list(_SVC, "GET", "/organization/similar", params={"id": id}, paginator=_live_paginator, options=options)

    def affiliated(self, id: str, *, options=None) -> RenidlyList[RenidlyModel]:
        """List affiliated / subsidiary / showcase pages.

        Calls ``GET /api/v2/organization/affiliated``. Maps the corporate family.

        Example::

            client.live.organizations.affiliated("1441")
        """
        return self._list(_SVC, "GET", "/organization/affiliated", params={"id": id}, paginator=_live_paginator, options=options)

    def resolve_slug(self, slug: str, *, options=None) -> Optional[RenidlyModel]:
        """Resolve a public company slug to its numeric ``id`` (resolve once, reuse).

        Calls ``GET /api/v2/organization/resolve-slug``.

        Example::

            oid = client.live.organizations.resolve_slug("google").id
        """
        return self._one(_SVC, "GET", "/organization/resolve-slug", params={"slug": slug}, options=options)

    def activities(self, id: str, *, start=None, options=None) -> RenidlyList[RenidlyModel]:
        """List a company's recent posts; offset-paginated.

        Calls ``GET /api/v2/organization/activities``.

        Example::

            client.live.organizations.activities("1441")
        """
        return self._list(_SVC, "GET", "/organization/activities", params={"id": id, "start": start}, paginator=_live_paginator, options=options)

    def opportunities(self, organization_entity_ids: str, *, start=None, options=None) -> RenidlyList[RenidlyModel]:
        """List open postings across one or more organizations; offset-paginated.

        Calls ``GET /api/v2/organization/opportunities``.
        ``organization_entity_ids`` is a comma-separated string of org ids.

        Example::

            client.live.organizations.opportunities("1441,1035")
        """
        return self._list(_SVC, "GET", "/organization/opportunities", params={"organizationEntityIds": organization_entity_ids, "start": start}, paginator=_live_paginator, options=options)


class LiveDiscover(SyncResource):
    """Discovery search over people, organizations, and opportunities."""

    def people(self, *, options=None, **params: Unpack[DiscoverPeopleParams]) -> RenidlyList[RenidlyModel]:
        """Search professionals by keyword + structured filters; offset-paginated.

        Calls ``GET /api/v2/discover/people``. Multi-value filters are
        comma-separated strings (OR within a param, AND across params).

        Example::

            for p in client.live.discover.people(keyword="cto", count=25).auto_paging_iter():
                print(p.fullName)
        """
        return self._list(_SVC, "GET", "/discover/people", params=params, paginator=_live_paginator, options=options)

    def organizations(self, *, options=None, **params: Unpack[DiscoverOrganizationsParams]) -> RenidlyList[RenidlyModel]:
        """Search companies by keyword + filters; offset-paginated.

        Calls ``GET /api/v2/discover/organizations`` (``keyword`` required; plus
        ``headcountRange``, ``industry``, ``geoEntityId``, ``hasJobs``).

        Example::

            client.live.discover.organizations(keyword="fintech", headcountRange="51-200")
        """
        return self._list(_SVC, "GET", "/discover/organizations", params=params, paginator=_live_paginator, options=options)

    def opportunities(self, *, options=None, **params: Unpack[DiscoverOpportunitiesParams]) -> RenidlyList[RenidlyModel]:
        """Search job postings by keyword + rich filters; offset-paginated.

        Calls ``GET /api/v2/discover/opportunities`` (``experience``,
        ``jobTypes``, ``workplaceTypes``, ``salary``, ``datePosted``, …).

        Example::

            client.live.discover.opportunities(keyword="python", workplaceTypes="remote")
        """
        return self._list(_SVC, "GET", "/discover/opportunities", params=params, paginator=_live_paginator, options=options)


class Live:
    """The Live-API namespace: ``people``, ``activities``, ``opportunities``, ``organizations``, ``discover``."""

    def __init__(self, client: Any) -> None:
        self.people = LivePeople(client)
        self.activities = LiveActivities(client)
        self.opportunities = LiveOpportunities(client)
        self.organizations = LiveOrganizations(client)
        self.discover = LiveDiscover(client)


# ─────────────────────────── async ───────────────────────────
class AsyncLivePeople(AsyncResource):
    """Async :class:`LivePeople`."""

    async def enrich(self, entity_id=None, *, handle=None, options=None) -> Optional[RenidlyModel]:
        """Full live profile. See :meth:`LivePeople.enrich`."""
        return await self._one(_SVC, "GET", "/person/enrich", params={"entityId": entity_id, "handle": handle}, options=options)

    async def resolve_handle(self, handle, *, options=None) -> Optional[RenidlyModel]:
        """Handle -> entityId. See :meth:`LivePeople.resolve_handle`."""
        return await self._one(_SVC, "GET", "/person/resolve-handle", params={"handle": handle}, options=options)

    async def employment_history(self, entity_id, *, options=None) -> Optional[RenidlyModel]:
        """Work history. See :meth:`LivePeople.employment_history`."""
        return await self._one(_SVC, "GET", "/person/employment-history", params={"entityId": entity_id}, options=options)

    async def endorsements(self, entity_id, *, options=None) -> AsyncRenidlyList[RenidlyModel]:
        """Recommendations. See :meth:`LivePeople.endorsements`."""
        return await self._list(_SVC, "GET", "/person/endorsements", params={"entityId": entity_id}, paginator=_live_paginator, options=options)

    async def lookalikes(self, entity_id, *, options=None) -> AsyncRenidlyList[RenidlyModel]:
        """Similar profiles. See :meth:`LivePeople.lookalikes`."""
        return await self._list(_SVC, "GET", "/person/lookalikes", params={"entityId": entity_id}, paginator=_live_paginator, options=options)

    async def interests(self, entity_id, *, options=None) -> AsyncRenidlyList[RenidlyModel]:
        """Follows. See :meth:`LivePeople.interests`."""
        return await self._list(_SVC, "GET", "/person/interests", params={"entityId": entity_id}, paginator=_live_paginator, options=options)


class AsyncLiveActivities(AsyncResource):
    """Async :class:`LiveActivities`."""

    async def feed(self, entity_id, *, cursor=None, start=None, options=None) -> AsyncRenidlyList[RenidlyModel]:
        """Activity feed. See :meth:`LiveActivities.feed`."""
        return await self._list(_SVC, "GET", "/activity/feed", params={"entityId": entity_id, "cursor": cursor, "start": start}, paginator=_live_paginator, options=options)

    async def retrieve(self, entity_id, *, options=None) -> Optional[RenidlyModel]:
        """One post. See :meth:`LiveActivities.retrieve`."""
        return await self._one(_SVC, "GET", "/activity/details", params={"entityId": entity_id}, options=options)

    async def reactions(self, entity_id, *, start=None, options=None) -> AsyncRenidlyList[RenidlyModel]:
        """Reactions. See :meth:`LiveActivities.reactions`."""
        return await self._list(_SVC, "GET", "/activity/reactions", params={"entityId": entity_id, "start": start}, paginator=_live_paginator, options=options)

    async def replies(self, entity_id, *, sort_by=None, count=None, start=None, options=None) -> AsyncRenidlyList[RenidlyModel]:
        """Replies. See :meth:`LiveActivities.replies`."""
        return await self._list(_SVC, "GET", "/activity/replies", params={"entityId": entity_id, "sortBy": sort_by, "count": count, "start": start}, paginator=_live_paginator, options=options)

    async def replies_by_author(self, entity_id, *, cursor=None, start=None, options=None) -> AsyncRenidlyList[RenidlyModel]:
        """Replies by author. See :meth:`LiveActivities.replies_by_author`."""
        return await self._list(_SVC, "GET", "/activity/replies/by-author", params={"entityId": entity_id, "cursor": cursor, "start": start}, paginator=_live_paginator, options=options)


class AsyncLiveOpportunities(AsyncResource):
    """Async :class:`LiveOpportunities`."""

    async def retrieve(self, opportunity_entity_id, *, options=None) -> Optional[RenidlyModel]:
        """Job details. See :meth:`LiveOpportunities.retrieve`."""
        return await self._one(_SVC, "GET", "/opportunity/details", params={"opportunityEntityId": opportunity_entity_id}, options=options)

    async def similar(self, opportunity_entity_id, *, options=None) -> AsyncRenidlyList[RenidlyModel]:
        """Similar jobs. See :meth:`LiveOpportunities.similar`."""
        return await self._list(_SVC, "GET", "/opportunity/similar", params={"opportunityEntityId": opportunity_entity_id}, paginator=_live_paginator, options=options)

    async def related_views(self, opportunity_entity_id, *, options=None) -> AsyncRenidlyList[RenidlyModel]:
        """Also-viewed. See :meth:`LiveOpportunities.related_views`."""
        return await self._list(_SVC, "GET", "/opportunity/related-views", params={"opportunityEntityId": opportunity_entity_id}, paginator=_live_paginator, options=options)

    async def hiring_team(self, opportunity_entity_id, *, options=None) -> AsyncRenidlyList[RenidlyModel]:
        """Hiring team. See :meth:`LiveOpportunities.hiring_team`."""
        return await self._list(_SVC, "GET", "/opportunity/hiring-team", params={"opportunityEntityId": opportunity_entity_id}, paginator=_live_paginator, options=options)

    async def by_person(self, person_entity_id, *, count=None, start=None, options=None) -> AsyncRenidlyList[RenidlyModel]:
        """Posted by person. See :meth:`LiveOpportunities.by_person`."""
        return await self._list(_SVC, "GET", "/opportunity/by-person", params={"personEntityId": person_entity_id, "count": count, "start": start}, paginator=_live_paginator, options=options)


class AsyncLiveOrganizations(AsyncResource):
    """Async :class:`LiveOrganizations`."""

    async def enrich(self, id, *, options=None) -> Optional[RenidlyModel]:
        """Company profile. See :meth:`LiveOrganizations.enrich`."""
        return await self._one(_SVC, "GET", "/organization/enrich", params={"id": id}, options=options)

    async def headcount(self, id, *, options=None) -> Optional[RenidlyModel]:
        """Headcount. See :meth:`LiveOrganizations.headcount`."""
        return await self._one(_SVC, "GET", "/organization/headcount", params={"id": id}, options=options)

    async def similar(self, id, *, options=None) -> AsyncRenidlyList[RenidlyModel]:
        """Similar companies. See :meth:`LiveOrganizations.similar`."""
        return await self._list(_SVC, "GET", "/organization/similar", params={"id": id}, paginator=_live_paginator, options=options)

    async def affiliated(self, id, *, options=None) -> AsyncRenidlyList[RenidlyModel]:
        """Affiliated pages. See :meth:`LiveOrganizations.affiliated`."""
        return await self._list(_SVC, "GET", "/organization/affiliated", params={"id": id}, paginator=_live_paginator, options=options)

    async def resolve_slug(self, slug, *, options=None) -> Optional[RenidlyModel]:
        """Slug -> id. See :meth:`LiveOrganizations.resolve_slug`."""
        return await self._one(_SVC, "GET", "/organization/resolve-slug", params={"slug": slug}, options=options)

    async def activities(self, id, *, start=None, options=None) -> AsyncRenidlyList[RenidlyModel]:
        """Company posts. See :meth:`LiveOrganizations.activities`."""
        return await self._list(_SVC, "GET", "/organization/activities", params={"id": id, "start": start}, paginator=_live_paginator, options=options)

    async def opportunities(self, organization_entity_ids, *, start=None, options=None) -> AsyncRenidlyList[RenidlyModel]:
        """Company jobs. See :meth:`LiveOrganizations.opportunities`."""
        return await self._list(_SVC, "GET", "/organization/opportunities", params={"organizationEntityIds": organization_entity_ids, "start": start}, paginator=_live_paginator, options=options)


class AsyncLiveDiscover(AsyncResource):
    """Async :class:`LiveDiscover`."""

    async def people(self, *, options=None, **params: Unpack[DiscoverPeopleParams]) -> AsyncRenidlyList[RenidlyModel]:
        """Discover people. See :meth:`LiveDiscover.people`."""
        return await self._list(_SVC, "GET", "/discover/people", params=params, paginator=_live_paginator, options=options)

    async def organizations(self, *, options=None, **params: Unpack[DiscoverOrganizationsParams]) -> AsyncRenidlyList[RenidlyModel]:
        """Discover companies. See :meth:`LiveDiscover.organizations`."""
        return await self._list(_SVC, "GET", "/discover/organizations", params=params, paginator=_live_paginator, options=options)

    async def opportunities(self, *, options=None, **params: Unpack[DiscoverOpportunitiesParams]) -> AsyncRenidlyList[RenidlyModel]:
        """Discover jobs. See :meth:`LiveDiscover.opportunities`."""
        return await self._list(_SVC, "GET", "/discover/opportunities", params=params, paginator=_live_paginator, options=options)


class AsyncLive:
    """Async Live-API namespace. Mirrors :class:`Live`."""

    def __init__(self, client: Any) -> None:
        self.people = AsyncLivePeople(client)
        self.activities = AsyncLiveActivities(client)
        self.opportunities = AsyncLiveOpportunities(client)
        self.organizations = AsyncLiveOrganizations(client)
        self.discover = AsyncLiveDiscover(client)
