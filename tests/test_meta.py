"""Mocked unit tests for the ResponseMeta surface (`.meta` / `.last_response`)."""
import httpx
import respx

from renidly import Renidly, RenidlyConfig, ResponseMeta


def ok(data, pagination=None):
    e = {"success": True, "statusCode": 200, "message": "ok", "errors": None, "data": data}
    if pagination is not None:
        e["pagination"] = pagination
    return e


CREDIT_HEADERS = {"x-credits-consumed": "5", "x-credits-balance": "95", "x-request-id": "req_42"}


@respx.mock
def test_meta_full_surface_on_single():
    respx.get(url__regex=r".*/people/profile.*").mock(
        return_value=httpx.Response(200, json=ok({"first_name": "Ada"}), headers=CREDIT_HEADERS)
    )
    p = Renidly("k").data.people.retrieve(id="prsn_x")
    m = p.meta
    assert isinstance(m, ResponseMeta)
    assert m.status_code == 200
    assert m.credit_consumed == 5.0
    assert m.remaining_balance == 95.0
    assert m.request_id == "req_42"
    assert m.headers["x-credits-consumed"] == "5"
    assert m.body["success"] is True and m.body["data"]["first_name"] == "Ada"
    assert '"first_name":"Ada"' in m.raw_body.replace(" ", "")
    assert isinstance(m.raw_http, httpx.Response) and m.raw_http.status_code == 200
    # alias
    assert p.last_response is p.meta
    # data itself is untouched
    assert p.first_name == "Ada"


@respx.mock
def test_meta_absent_credit_headers_are_none():
    respx.get(url__regex=r".*/people/profile.*").mock(
        return_value=httpx.Response(200, json=ok({"x": 1}))  # no X-Credits-* headers
    )
    p = Renidly("k").data.people.retrieve(id="prsn_x")
    assert p.meta.credit_consumed is None
    assert p.meta.remaining_balance is None
    assert p.meta.status_code == 200


@respx.mock
def test_meta_mixed_case_and_fractional():
    respx.get(url__regex=r".*/people/profile.*").mock(
        return_value=httpx.Response(200, json=ok({"x": 1}), headers={"X-Credits-Consumed": "2", "X-Credits-Balance": "8.5"})
    )
    p = Renidly("k").data.people.retrieve(id="prsn_x")
    assert p.meta.credit_consumed == 2.0
    assert p.meta.remaining_balance == 8.5


@respx.mock
def test_meta_on_envelope_mode():
    respx.get(url__regex=r".*/people/profile.*").mock(
        return_value=httpx.Response(200, json=ok({"x": 1}), headers=CREDIT_HEADERS)
    )
    c = Renidly("k", config=RenidlyConfig(unwrap_data_obj=False))
    resp = c.data.people.retrieve(id="prsn_x")
    assert resp.success is True
    assert resp.meta.credit_consumed == 5.0
    assert resp.meta.remaining_balance == 95.0


@respx.mock
def test_meta_on_list_and_items():
    respx.get(url__regex=r".*/people/search.*").mock(
        return_value=httpx.Response(
            200, json=ok([{"first_name": "a"}, {"first_name": "b"}], pagination={"has_more": False}), headers=CREDIT_HEADERS
        )
    )
    lst = Renidly("k").data.people.search(title="cto")
    assert lst.meta.credit_consumed == 5.0
    assert lst.meta.remaining_balance == 95.0
    assert lst.last_response is lst.meta
    # each item carries the same page's meta
    assert lst[0].meta.credit_consumed == 5.0
    assert lst[1].meta.remaining_balance == 95.0


@respx.mock
def test_meta_per_page_across_auto_paging():
    # Two pages, each a separate billed request with a different balance.
    respx.get(url__regex=r".*/people/search.*").mock(
        side_effect=[
            httpx.Response(200, json=ok([{"first_name": "a"}], pagination={"has_more": True, "next_cursor": "c2"}),
                          headers={"x-credits-consumed": "1", "x-credits-balance": "99"}),
            httpx.Response(200, json=ok([{"first_name": "b"}], pagination={"has_more": False}),
                          headers={"x-credits-consumed": "1", "x-credits-balance": "98"}),
        ]
    )
    page1 = Renidly("k").data.people.search(title="cto")
    balances = [item.meta.remaining_balance for item in page1.auto_paging_iter()]
    assert balances == [99.0, 98.0]  # each item reflects ITS page's headers
    # the container reflects the first page only
    assert page1.meta.remaining_balance == 99.0
