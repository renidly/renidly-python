"""Renidly Python SDK — usage examples.

Every product hangs off the client: r.account, r.data, r.live, r.emails.
Set your key once (arg or RENIDLY_API_KEY) and go. Nothing here runs without a
key except the public account.tiers() / account.route_costs().

    pip install renidly
"""
import asyncio

from renidly import (
    AsyncRenidly,
    AuthenticationError,
    InsufficientCreditsError,
    NotFoundError,
    RateLimitError,
    Renidly,
    RenidlyConfig,
    RenidlyError,
)


# ─────────────────────────────────────────────────────────────
# 1. Create a client
# ─────────────────────────────────────────────────────────────
client = Renidly("rnd-...")                      # or Renidly() with RENIDLY_API_KEY set

# ...with options: build a RenidlyConfig (every field autocompletes) and pass it.
client = Renidly("rnd-...", config=RenidlyConfig(
    timeout=30,
    max_retries=2,                # auto-retry on 429 / 503 / connection errors (backoff + jitter)
    base_url="https://renidly.com",
    unwrap_data_obj=True,         # return the data model (False -> the full envelope)
    raise_on_not_found=False,     # single lookups return None when empty (True -> raise NotFoundError)
    raise_on_api_error=True,      # map success:false -> typed exceptions
    auto_rate_limit=True,         # throttle to your tier's per-minute limit automatically
))


# ─────────────────────────────────────────────────────────────
# 2. Account & Credits  (tiers / route_costs need NO key)
# ─────────────────────────────────────────────────────────────
for tier in client.account.tiers():              # public tier ladder
    print(tier.name, tier.limit_per_minute, tier.credits_per_dollar)

print(client.account.balance().balance)          # your live balance
t = client.account.tier()
print(t.current_tier.name, t.current_tier.limit_per_minute)

for route in client.account.route_costs():        # only routes != 1 credit; absent = 1
    print(route.route, route.credits_cost)


# ─────────────────────────────────────────────────────────────
# 3. Data API — clean records by stable id or filters
# ─────────────────────────────────────────────────────────────
# single lookup -> the model, or None if nothing resolved
person = client.data.people.retrieve(id="prsn_...")     # or handle="ryanroslansky"
if person:
    print(person.first_name, person.headline)

# search -> a list you can index, iterate, or auto-page across pages.
# IDE autocompletes every filter name (title, current_only, skills, ...).
results = client.data.people.search(title="cto", current_only=True, limit=25)
print("page count:", len(results.data), "| more:", results.has_more)
first = results.data[0]

for p in client.data.people.search(headline="engineer").auto_paging_iter():
    ...                                            # spans ALL pages lazily

# companies
google = client.data.companies.retrieve(slug="google")
for c in client.data.companies.search(name="stripe", limit=10):
    print(c.name)
engineers = client.data.companies.employees("google", title="engineer", current_only=True)

# institutions, skills, job changes
mit = client.data.institutions.retrieve("mit")
skills = client.data.skills.search("python")
changes = client.data.job_changes.search(event_type="joined", days_ago=30)


# ─────────────────────────────────────────────────────────────
# 4. Batch enrichment — submit -> poll -> collect
# ─────────────────────────────────────────────────────────────
job = client.data.people.enrich_batch(handles=["ryanroslansky", "williamhgates"], live=True)
print("job:", job.id)

# (a) block until done and get everything
result = job.wait(on_progress=lambda n: print("resolved", n))
print(result.status, result.resolved, "/", result.total, "| not_found:", result.not_found)
for row in result.results:
    print(row.matched_input, "->", getattr(row, "headline", None))

# (b) OR stream results as they resolve (a generator)
for row in client.data.companies.enrich_batch(ids=["org_a", "org_b"]).stream():
    print(row.matched_input)


# ─────────────────────────────────────────────────────────────
# 5. Email API
# ─────────────────────────────────────────────────────────────
v = client.emails.verify("sundar@google.com")
print(v.email, v.deliverable, v.reason)

f = client.emails.find(first_name="Patrick", last_name="Collison", domain="stripe.com")
print(f.email, f.found, f.confidence)

client.emails.find_by_url("https://www.linkedin.com/in/sundarpichai/")
client.emails.reverse("john@acme.com")
for prospect in client.emails.prospects("acme.com", kind="verified_only").auto_paging_iter():
    print(prospect.email)

# email batch jobs (verify / find)
vjob = client.emails.verify_batch(["a@x.com", "b@y.com"])
print(vjob.wait().results)


# ─────────────────────────────────────────────────────────────
# 6. Live API — freshest snapshot on demand
# ─────────────────────────────────────────────────────────────
entity = client.live.people.resolve_handle("williamhgates")   # handle -> stable entityId
profile = client.live.people.enrich(entity.entityId)
org_id = client.live.organizations.resolve_slug("microsoft").id
org = client.live.organizations.enrich(org_id)
for p in client.live.discover.people(keyword="cto", count=25):
    ...


# ─────────────────────────────────────────────────────────────
# 7. Error handling — a typed hierarchy (all subclass RenidlyError)
# ─────────────────────────────────────────────────────────────
try:
    client.emails.verify("x@y.com")
except NotFoundError:
    print("nothing resolved")
except InsufficientCreditsError:
    print("top up your balance")
except RateLimitError as e:
    print("slow down; tier", e.tier, "limit", e.limit)
except AuthenticationError:
    print("bad / missing key")
except RenidlyError as e:                      # catch-all
    print(e.status_code, e.error_code, e.message, e.errors)


# ─────────────────────────────────────────────────────────────
# 8. Extras
# ─────────────────────────────────────────────────────────────
# per-request overrides
client.data.skills.search("golang", options={"timeout": 5, "api_key": "rnd-other"})

# HTTP metadata + credit accounting on any object, under .meta
sk = client.data.skills.retrieve("skl_...")
print(sk.meta.status_code, sk.meta.request_id)
print("credits charged:", sk.meta.credit_consumed, "| balance left:", sk.meta.remaining_balance)

# raw escape hatch for anything not yet wrapped
env = client.raw_request("GET", "/people/search", service="data", params={"title": "cto"})
print(env.success, env.data)

# full envelope instead of unwrapped data
raw_client = Renidly("rnd-...", config=RenidlyConfig(unwrap_data_obj=False))
resp = raw_client.account.balance()            # -> APIResponse(success=..., data=..., message=...)


# ─────────────────────────────────────────────────────────────
# 9. Async — same surface, just await (context-manages the HTTP client)
# ─────────────────────────────────────────────────────────────
async def main() -> None:
    async with AsyncRenidly("rnd-...") as r:
        tiers = await r.account.tiers()
        async for tier in tiers.auto_paging_iter():
            print(tier.name)
        person = await r.data.people.retrieve(handle="ryanroslansky")
        job = await r.data.people.enrich_batch(handles=["a", "b"])
        result = await job.wait()
        print(result.resolved)


if __name__ == "__main__":
    asyncio.run(main())
