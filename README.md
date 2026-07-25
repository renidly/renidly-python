# Renidly Python SDK

The official Python SDK for the [Renidly](https://renidly.com) B2B professional data APIs — resolve, search, enrich, and verify professional identities (people, organizations, institutions, skills, professional activity, job opportunities, and business email) through one clean, typed client.

```python
from renidly import Renidly

renidly = Renidly("rnd-...")

person  = renidly.data.people.retrieve(handle="ryanroslansky")
company = renidly.data.companies.retrieve(slug="stripe")
email   = renidly.emails.verify("sundar@google.com")

print(person.headline, company.name, email.deliverable)
```

- **One client, four products** — `data`, `live`, `emails`, `account`, all off the same key.
- **Fully typed** — method names, parameters, and returns autocomplete in your IDE (ships `py.typed`).
- **Batteries included** — automatic retries, transparent pagination, batch jobs, a typed error hierarchy, and an optional self-tuning rate limiter.
- **Sync and async** — identical surface; just `await`.

---

## Table of contents

- [Install](#install)
- [Quickstart](#quickstart)
- [Authentication](#authentication)
- [The four products](#the-four-products)
- [Pagination](#pagination)
- [Batch jobs](#batch-jobs)
- [Errors](#errors)
- [Configuration](#configuration)
- [Automatic rate limiting](#automatic-rate-limiting)
- [Async](#async)
- [Response objects](#response-objects)
- [Advanced](#advanced)
- [Requirements & support](#requirements--support)

---

## Install

```sh
pip install renidly
```

Requires **Python 3.9+**.

---

## Quickstart

```python
from renidly import Renidly

renidly = Renidly("rnd-...")            # or Renidly() and set RENIDLY_API_KEY

# Retrieve a single record (returns None if nothing resolved)
person = renidly.data.people.retrieve(id="prsn_...")
if person:
    print(person.first_name, person.headline)

# Search with any filters — they autocomplete in your editor
for p in renidly.data.people.search(title="cto", current_only=True).auto_paging_iter():
    print(p.headline)

# Verify an email
v = renidly.emails.verify("sundar@google.com")
print(v.deliverable, v.reason)
```

That's the whole feel: `renidly.<product>.<resource>.<action>(...)`.

---

## Authentication

Pass your key positionally, via config, or through the environment — whichever you prefer.

```python
Renidly("rnd-...")                                  # positional
Renidly()                                           # reads RENIDLY_API_KEY
Renidly(config=RenidlyConfig(api_key="rnd-..."))    # inside the config object
```

Per-request override (e.g. multi-tenant apps):

```python
renidly.data.people.search(title="cto", options={"api_key": "rnd-tenant-key"})
```

Grab your key from [Workspace → API Keys](https://renidly.com/dashboard/key).

---

## The four products

### `data` — clean, queryable records

Deduplicated professional records addressable by stable opaque IDs (`prsn_`, `org_`, `inst_`, `skl_`) or rich filters.

```python
# People
renidly.data.people.retrieve(id="prsn_...")                     # or handle="..."
renidly.data.people.search(title="cto", skills="python", geo_country_code="US")
renidly.data.people.enrich_batch(handles=[...], ids=[...], live=True)   # bulk (see Batch jobs)

# Companies
renidly.data.companies.retrieve(slug="google")                  # or id="org_..."
renidly.data.companies.search(name="stripe", staff_count_min=100)
renidly.data.companies.employees("google", title="engineer", current_only=True)
renidly.data.companies.enrich_batch(ids=[...])                  # bulk (see Batch jobs)

# Institutions
renidly.data.institutions.retrieve("stanford")                  # by normalized name
renidly.data.institutions.search("stanford")
renidly.data.institutions.alumni("stanford", degree="MBA")

# Skills
renidly.data.skills.retrieve("skl_...")
renidly.data.skills.search("python")

# Job changes — trigger-based prospecting
renidly.data.job_changes.search(event_type="joined", days_ago=30)
```

### `live` — freshest snapshot on demand

Resolve a single subject or run a discovery search.

```python
# People — resolve a public handle to a stable id once, then reuse it
eid = renidly.live.people.resolve_handle("williamhgates").entityId
renidly.live.people.enrich(eid)                       # or handle="..."
renidly.live.people.employment_history(eid)
renidly.live.people.endorsements(eid)
renidly.live.people.lookalikes(eid)
renidly.live.people.interests(eid)

# Organizations
oid = renidly.live.organizations.resolve_slug("google").id
renidly.live.organizations.enrich(oid)
renidly.live.organizations.headcount(oid)
renidly.live.organizations.similar(oid)
renidly.live.organizations.affiliated(oid)
renidly.live.organizations.activities(oid)
renidly.live.organizations.opportunities("1441,1035")   # comma-separated org ids

# Opportunities (job postings)
renidly.live.opportunities.retrieve("4019200001")
renidly.live.opportunities.similar("4019200001")
renidly.live.opportunities.related_views("4019200001")
renidly.live.opportunities.hiring_team("4019200001")
renidly.live.opportunities.by_person(eid)

# Activity
renidly.live.activities.feed(eid)
renidly.live.activities.retrieve(activity_id)
renidly.live.activities.reactions(activity_id)
renidly.live.activities.replies(activity_id, sort_by="date_posted")
renidly.live.activities.replies_by_author(eid)

# Discover (search)
renidly.live.discover.people(keyword="cto", count=25)
renidly.live.discover.organizations(keyword="fintech", headcountRange="51-200")
renidly.live.discover.opportunities(keyword="python", workplaceTypes="remote")
```

### `emails` — verify, find, and resolve

```python
renidly.emails.verify("sundar@google.com")
renidly.emails.find(first_name="Patrick", last_name="Collison", domain="stripe.com")
renidly.emails.find_by_url("https://example.com/in/someone")   # from a professional profile URL
renidly.emails.reverse("john@acme.com")                        # who is behind this business email
renidly.emails.prospects("acme.com", kind="verified_only")     # known contacts for a domain

# Bulk (see Batch jobs)
renidly.emails.verify_batch(["a@x.com", "b@y.com"])
renidly.emails.find_batch([{"first_name": "A", "last_name": "B", "domain": "acme.com"}])
```

### `account` — balance, tier, and pricing

```python
renidly.account.balance().balance
renidly.account.tier().current_tier.limit_per_minute
renidly.account.enterprise_balance()   # for an Enterprise workspace
renidly.account.tiers()                # public tier ladder (no key needed)
renidly.account.route_costs()          # per-endpoint credit costs (no key needed)
```

---

## Pagination

Every `search`/list method returns a list you can use directly **and** page through transparently.

```python
page = renidly.data.people.search(title="cto", limit=25)

len(page)            # items on this page
page[0]              # index it
for p in page: ...   # iterate this page
page.has_more        # is there more?

# ...or walk EVERY page lazily (fetches as it goes, one page in memory at a time)
for person in renidly.data.people.search(title="cto").auto_paging_iter():
    print(person.headline)
```

---

## Batch jobs

Process up to 1000 items in one async job. Submit returns a handle instantly.

```python
job = renidly.data.people.enrich_batch(handles=["ryanroslansky", "williamhgates"], live=True)

# block until done and collect everything
result = job.wait(on_progress=lambda n: print("resolved", n))
print(result.status, result.resolved, "/", result.total)
for row in result.results:
    print(row.matched_input, "->", row.headline)
print("not found:", result.not_found)

# ...or stream results as they resolve
for row in renidly.emails.verify_batch(["a@x.com", "b@y.com"]).stream():
    print(row.email, row.deliverable)
```

Available on `data.people.enrich_batch`, `data.companies.enrich_batch`, `emails.verify_batch`, `emails.find_batch`.

---

## Errors

Every failure raises a specific subclass of `RenidlyError`, and the message tells you exactly what went wrong.

```python
from renidly import (
    RenidlyError, AuthenticationError, InvalidRequestError,
    InsufficientCreditsError, NotFoundError, RateLimitError,
    PermissionDeniedError, ServiceUnavailableError,
)

try:
    renidly.emails.find(first_name="A", last_name="B", domain="bad")
except InvalidRequestError as e:
    print(e.message)        # "Validation failed"
    print(e.field_errors)   # {"domain": "must be a bare hostname"}
except RateLimitError as e:
    print(e.tier, e.limit, e.retry_after)
except InsufficientCreditsError:
    ...
except RenidlyError as e:   # catch-all
    print(e.status_code, e.error_code, e.message, e.errors)
```

The string form includes the detail, so an uncaught error is self-explanatory:

```
InvalidRequestError: Validation failed — domain: must be a bare hostname (VALIDATION_ERROR, HTTP 400)
```

| Exception | When |
|---|---|
| `AuthenticationError` | missing / invalid key |
| `PermissionDeniedError` | key valid but not allowed here |
| `InvalidRequestError` | bad input (see `.field_errors`) |
| `InsufficientCreditsError` | not enough credits |
| `NotFoundError` | job not found / expired |
| `RateLimitError` | per-minute limit hit (`.tier`, `.limit`, `.retry_after`) |
| `ServiceUnavailableError` | temporary — retry shortly |
| `APIConnectionError` | network / timeout |

> **Not-found lookups:** a single `retrieve(...)` that resolves nothing returns `None` by default (not an exception). Set `raise_on_not_found=True` to raise instead.

---

## Configuration

All options live on one object, `RenidlyConfig`:

```python
from renidly import Renidly, RenidlyConfig

renidly = Renidly("rnd-...", config=RenidlyConfig(
    timeout=30,
    max_retries=3,            # auto-retry on 429 / 503 / connection errors (backoff + jitter)
    unwrap_data_obj=True,     # return the data model (False -> the full envelope)
    raise_on_not_found=False, # single lookups return None when empty (True -> raise)
    raise_on_api_error=True,  # map failures to typed exceptions
    auto_rate_limit=False,    # see below
))
```

| Option | Default | Meaning |
|---|---|---|
| `api_key` | `RENIDLY_API_KEY` env | Your key (positional arg overrides this). |
| `timeout` | `30` | Per-request timeout (seconds). |
| `max_retries` | `2` | Retries on transient failures. |
| `backoff_factor` | `0.5` | Base seconds for exponential backoff. |
| `base_url` | `https://renidly.com` | Override the API host. |
| `proxy` | `None` | HTTP(S) proxy URL. |
| `default_headers` | `{}` | Extra headers on every request. |
| `unwrap_data_obj` | `True` | Return `data` vs the full envelope. |
| `raise_on_not_found` | `False` | `None` vs `NotFoundError` on empty lookups. |
| `raise_on_api_error` | `True` | Raise vs return `None` on API errors. |
| `auto_rate_limit` | `False` | Self-throttle to your tier's limit. |
| `rate_limit_per_minute` | `None` | Fixed limit (required for enterprise keys). |
| `rate_limit_safety` | `1.0` | Fraction of the limit to target (e.g. `0.9`). |

---

## Automatic rate limiting

Turn it on and the SDK keeps you under your per-minute limit automatically — no limiter to build.

```python
# Regular key: the limit is read from your tier and refreshed automatically.
Renidly("rnd-...", config=RenidlyConfig(auto_rate_limit=True))

# Enterprise key: the limit is fixed — supply it.
Renidly("enterprise-...", config=RenidlyConfig(auto_rate_limit=True, rate_limit_per_minute=550))
```

It uses a sliding 60-second window so you never exceed the limit, and re-reads your tier after a `429`.

---

## Async

Same surface, same names — just `await` (and use it as a context manager to auto-close the connection pool).

```python
import asyncio
from renidly import AsyncRenidly

async def main():
    async with AsyncRenidly("rnd-...") as renidly:
        company = await renidly.data.companies.retrieve(slug="stripe")
        print(company.name)

        async for p in renidly.data.people.search(title="cto").auto_paging_iter():
            print(p.headline)

asyncio.run(main())
```

---

## Response objects

Responses are dynamic and drill-able — access any field (nested included) as an attribute, no schema classes required.

```python
t = renidly.account.tier()
t.current_tier.name              # nested attribute access, arbitrarily deep
t.model_dump()                   # convert to a plain dict anytime

# HTTP metadata is attached to every object
t.last_response.status_code
t.last_response.request_id
```

Prefer the raw envelope? Set `unwrap_data_obj=False` and every call returns `APIResponse(success=..., data=..., message=...)`.

---

## Advanced

**Per-request options** override config for a single call:

```python
renidly.data.skills.search("python", options={"timeout": 5, "api_key": "rnd-other"})
```

**Escape hatch** — call any endpoint directly:

```python
env = renidly.raw_request("GET", "/people/search", service="data", params={"title": "cto"})
print(env.success, env.data)
```

**Bring your own HTTP client** (connection pools, custom timeouts, mounts):

```python
import httpx
Renidly("rnd-...", http_client=httpx.Client(limits=httpx.Limits(max_connections=50)))
```

---

## Requirements & support

- Python **3.9+**
- Depends only on [`httpx`](https://www.python-httpx.org/) and [`pydantic`](https://docs.pydantic.dev/) v2.

Questions or issues? Open one on [GitHub](https://github.com/renidly/renidly-python/issues).

## License

MIT
