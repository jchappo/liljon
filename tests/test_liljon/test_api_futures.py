"""Tests for FuturesAPI.place_order idempotency key handling."""

import json
import re
import uuid

import pytest

from liljon._http import HttpTransport
from liljon.api.futures import FuturesAPI


@pytest.fixture
def transport():
    return HttpTransport(timeout=5.0)


@pytest.fixture
def futures_api(transport):
    return FuturesAPI(transport)


_ORDER_RESPONSE = {
    "id": "ord-123",
    "account_id": "acct-1",
    "contract_id": "ct-1",
    "quantity": "1",
    "state": "queued",
    "side": "BUY",
    "order_type": "MARKET",
    "time_in_force": "GFD",
    "created_at": "2026-04-17T00:00:00Z",
}


async def test_place_order_uses_provided_ref_id(futures_api, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r"https://.*/ceres/v1/orders/"),
        method="POST",
        json=_ORDER_RESPONSE,
    )

    await futures_api.place_order(
        contract_id="ct-1",
        side="BUY",
        quantity=1,
        account_id="acct-1",
        order_type="MARKET",
        ref_id="my-custom-id",
    )

    (request,) = httpx_mock.get_requests()
    payload = json.loads(request.content)
    assert payload["refId"] == "my-custom-id"


async def test_place_order_generates_ref_id_when_none(futures_api, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r"https://.*/ceres/v1/orders/"),
        method="POST",
        json=_ORDER_RESPONSE,
    )

    await futures_api.place_order(
        contract_id="ct-1",
        side="BUY",
        quantity=1,
        account_id="acct-1",
        order_type="MARKET",
    )

    (request,) = httpx_mock.get_requests()
    payload = json.loads(request.content)
    # Must be a valid UUID string when auto-generated.
    uuid.UUID(payload["refId"])


async def test_place_order_same_ref_id_submitted_twice_sends_same_payload_key(
    futures_api, httpx_mock
):
    """Caller-supplied ID is preserved across retries — enables server-side dedup."""
    httpx_mock.add_response(
        url=re.compile(r"https://.*/ceres/v1/orders/"),
        method="POST",
        json=_ORDER_RESPONSE,
    )
    httpx_mock.add_response(
        url=re.compile(r"https://.*/ceres/v1/orders/"),
        method="POST",
        json=_ORDER_RESPONSE,
    )

    await futures_api.place_order(
        contract_id="ct-1", side="BUY", quantity=1, account_id="acct-1",
        order_type="MARKET", ref_id="retry-id-42",
    )
    await futures_api.place_order(
        contract_id="ct-1", side="BUY", quantity=1, account_id="acct-1",
        order_type="MARKET", ref_id="retry-id-42",
    )

    req_a, req_b = httpx_mock.get_requests()
    assert json.loads(req_a.content)["refId"] == "retry-id-42"
    assert json.loads(req_b.content)["refId"] == "retry-id-42"
