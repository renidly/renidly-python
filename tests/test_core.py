"""Mocked unit tests for the core behaviors (no network)."""
import httpx
import pytest
import respx

from renidly import (
    AsyncRenidly,
    AuthenticationError,
    InsufficientCreditsError,
    InvalidRequestError,
    NotFoundError,
    RateLimitError,
    Renidly,
    RenidlyConfig,
    ServiceUnavailableError,
)

BASE = "https://renidly.com"


def ok(data, pagination=None):
    e = {"success": True, "statusCode": 200, "message": "ok", "errors": None, "data": data}
    if pagination is not None:
        e["pagination"] = pagination
    return e


def fail(status, message, error_code=None, errors=None):
    return {"success": False, "statusCode": status, "message": message,
            "error_code": error_code, "errors": errors, "data": None}


@respx.mock
def test_auth_error():
    respx.get(url__regex=r".*/skills/skill.*").mock(return_value=httpx.Response(401, json=fail(401, "API key required")))
    with pytest.raises(AuthenticationError) as e:
        Renidly("k").data.skills.retrieve("skl_x")
    assert e.value.status_code == 401


@respx.mock
def test_validation_error_carries_fields():
    respx.get(url__regex=r".*/people/search.*").mock(
        return_value=httpx.Response(400, json=fail(400, "Validation failed", "VALIDATION_ERROR", {"title": "too short"}))
    )
    with pytest.raises(InvalidRequestError) as e:
        Renidly("k").data.people.search(title="x")
    assert e.value.field_errors == {"title": "too short"}


@respx.mock
def test_insufficient_credits():
    respx.get(url__regex=r".*/prospects.*").mock(return_value=httpx.Response(402, json=fail(402, "insufficient", "1080")))
    with pytest.raises(InsufficientCreditsError):
        Renidly("k").emails.prospects("acme.com", kind="full")


@respx.mock
def test_not_found_returns_none_or_raises():
    respx.get(url__regex=r".*/institutions/institution.*").mock(
        return_value=httpx.Response(200, json=fail(200, "Institution not found", "1040"))
    )
    assert Renidly("k").data.institutions.retrieve("nope") is None
    with pytest.raises(NotFoundError):
        Renidly("k", config=RenidlyConfig(raise_on_not_found=True)).data.institutions.retrieve("nope")


@respx.mock
def test_rate_limit_error_metadata():
    respx.get(url__regex=r".*/skills/skill.*").mock(
        return_value=httpx.Response(429, json=fail(429, "slow down", errors={"current_tier": "Hobby", "current_limit": 30}))
    )
    with pytest.raises(RateLimitError) as e:
        Renidly("k", config=RenidlyConfig(max_retries=0)).data.skills.retrieve("skl_x")
    assert e.value.tier == "Hobby" and e.value.limit == 30


@respx.mock
def test_retry_then_success():
    route = respx.get(url__regex=r".*/skills/skill.*")
    route.side_effect = [
        httpx.Response(503, json=fail(503, "unavailable", "1072")),
        httpx.Response(200, json=ok({"id": "skl_1", "name": "Python"})),
    ]
    sk = Renidly("k", config=RenidlyConfig(backoff_factor=0.0)).data.skills.retrieve("skl_1")
    assert sk.name == "Python" and route.call_count == 2


@respx.mock
def test_service_unavailable_after_retries():
    respx.get(url__regex=r".*/skills/skill.*").mock(return_value=httpx.Response(503, json=fail(503, "down", "1072")))
    with pytest.raises(ServiceUnavailableError):
        Renidly("k", config=RenidlyConfig(max_retries=1, backoff_factor=0.0)).data.skills.retrieve("skl_1")


@respx.mock
def test_cursor_auto_paging():
    route = respx.get(url__regex=r".*/people/search.*")
    route.side_effect = [
        httpx.Response(200, json=ok([{"first_name": "a"}, {"first_name": "b"}],
                                    pagination={"has_more": True, "next_cursor": "c2"})),
        httpx.Response(200, json=ok([{"first_name": "c"}], pagination={"has_more": False})),
    ]
    names = [p.first_name for p in Renidly("k").data.people.search(title="cto").auto_paging_iter()]
    assert names == ["a", "b", "c"] and route.call_count == 2


@respx.mock
def test_list_ergonomics_and_last_response():
    respx.get(url__regex=r".*/skills/search.*").mock(
        return_value=httpx.Response(200, json=ok([{"name": "Go"}], pagination={"has_more": False}), headers={"x-request-id": "req_1"})
    )
    res = Renidly("k").data.skills.search("go")
    assert len(res) == 1 and res[0].name == "Go" and res.data[0].last_response.request_id == "req_1"


@respx.mock
def test_unwrap_false_returns_envelope():
    respx.get(url__regex=r".*/credits/balance/k/.*").mock(return_value=httpx.Response(200, json=ok({"balance": 42.0})))
    resp = Renidly("k", config=RenidlyConfig(unwrap_data_obj=False)).account.balance()
    assert resp.success is True and resp.data.balance == 42.0


@respx.mock
def test_nested_model_access():
    respx.get(url__regex=r".*/credits/tier/k/.*").mock(
        return_value=httpx.Response(200, json=ok({"balance": 100, "current_tier": {"name": "Hobby", "limit_per_minute": 30}}))
    )
    t = Renidly("k").account.tier()
    assert t.current_tier.name == "Hobby" and t.current_tier.limit_per_minute == 30


@respx.mock
def test_batch_submit_poll_collect():
    respx.post(url__regex=r".*/verify/batch.*").mock(return_value=httpx.Response(202, json=ok({"job_id": "j1"})))
    track = respx.get(url__regex=r".*/verify/batch.*")
    track.side_effect = [
        httpx.Response(200, json=ok({"status": "processing", "total": 2, "resolved": 1, "errors": 0,
                                     "next_cursor": 1, "results": {"a@x.com": {"email": "a@x.com", "deliverable": True}}})),
        httpx.Response(200, json=ok({"status": "completed", "total": 2, "resolved": 2, "errors": 0,
                                     "next_cursor": 2, "results": {"b@y.com": {"email": "b@y.com", "deliverable": False}}})),
        httpx.Response(200, json=ok({"status": "completed", "total": 2, "resolved": 2, "errors": 0,
                                     "next_cursor": 2, "results": {}})),
    ]
    job = Renidly("k").emails.verify_batch(["a@x.com", "b@y.com"])
    result = job.wait(poll_interval=0)
    assert job.id == "j1" and result.status == "completed" and result.resolved == 2
    emails = sorted(r.email for r in result.results)
    assert emails == ["a@x.com", "b@y.com"]


@respx.mock
def test_per_request_api_key_override():
    route = respx.get(url__regex=r".*/skills/skill.*").mock(return_value=httpx.Response(200, json=ok({"name": "X"})))
    Renidly("base-key").data.skills.retrieve("skl_1", options={"api_key": "override-key"})
    assert route.calls.last.request.headers["X-renidly-apikey"] == "override-key"


@pytest.mark.asyncio
@respx.mock
async def test_async_client():
    respx.get(url__regex=r".*/user/sub/tiers/.*").mock(
        return_value=httpx.Response(200, json=ok({"results": [{"name": "Testing", "limit_per_minute": 7}]}))
    )
    async with AsyncRenidly("k") as r:
        tiers = await r.account.tiers()
        assert [t.name async for t in tiers.auto_paging_iter()] == ["Testing"]
