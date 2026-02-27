"""Tests for AccountAPI with mocked HTTP responses."""

import re

import pytest

from liljon._http import HttpTransport
from liljon.api.account import AccountAPI


@pytest.fixture
def transport():
    return HttpTransport(timeout=5.0)


@pytest.fixture
def account_api(transport):
    return AccountAPI(transport)


async def test_get_accounts(account_api, httpx_mock):
    httpx_mock.add_response(
        url="https://api.robinhood.com/accounts/",
        json={
            "results": [
                {"url": "https://api.robinhood.com/accounts/ABC123/", "account_number": "ABC123", "type": "individual"},
            ],
            "next": None,
        },
    )
    accounts = await account_api.get_accounts()
    assert len(accounts) == 1
    assert accounts[0].account_number == "ABC123"


async def test_get_portfolio(account_api, httpx_mock):
    httpx_mock.add_response(
        url="https://api.robinhood.com/accounts/ABC123/portfolio/",
        json={"equity": "50000.00", "withdrawable_amount": "5000.00"},
    )
    portfolio = await account_api.get_portfolio("ABC123")
    assert float(portfolio.equity) == 50000.00
    assert float(portfolio.withdrawable_amount) == 5000.00


async def test_get_positions(account_api, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r"https://api\.robinhood\.com/positions/"),
        json={
            "results": [
                {"instrument_url": "https://api.robinhood.com/instruments/abc/", "quantity": "10", "average_buy_price": "150.00"},
            ],
            "next": None,
        },
    )
    positions = await account_api.get_positions()
    assert len(positions) == 1
    assert float(positions[0].quantity) == 10


async def test_get_watchlists(account_api, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r"https://api\.robinhood\.com/midlands/lists/\?owner_type="),
        json={
            "results": [
                {"id": "wl-123", "display_name": "My List", "name": "my_list"},
            ],
        },
    )
    httpx_mock.add_response(
        url=re.compile(r"https://api\.robinhood\.com/midlands/lists/items/\?list_id=wl-123"),
        json={
            "results": [
                {"object_id": "abc", "object_type": "instrument", "symbol": "AAPL", "name": "Apple Inc"},
            ],
        },
    )
    watchlists = await account_api.get_watchlists()
    assert len(watchlists) == 1
    assert watchlists[0].display_name == "My List"
    assert len(watchlists[0].items) == 1
    assert watchlists[0].items[0].symbol == "AAPL"


async def test_get_watchlists_includes_id(account_api, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r"https://api\.robinhood\.com/midlands/lists/\?owner_type="),
        json={
            "results": [
                {"id": "wl-abc", "display_name": "My First List", "name": "default"},
            ],
        },
    )
    httpx_mock.add_response(
        url=re.compile(r"https://api\.robinhood\.com/midlands/lists/items/\?list_id=wl-abc"),
        json={"results": []},
    )
    watchlists = await account_api.get_watchlists()
    assert watchlists[0].id == "wl-abc"


async def test_create_watchlist(account_api, httpx_mock):
    httpx_mock.add_response(
        url="https://api.robinhood.com/midlands/lists/",
        method="POST",
        json={
            "id": "wl-new",
            "url": "https://api.robinhood.com/midlands/lists/wl-new/",
            "name": "technology",
            "display_name": "Technology",
            "instruments": [],
        },
    )
    wl = await account_api.create_watchlist("Technology")
    assert wl.id == "wl-new"
    assert wl.display_name == "Technology"
    assert wl.items == []

    # Verify POST payload
    request = httpx_mock.get_requests()[-1]
    import json
    payload = json.loads(request.content)
    assert payload == {"display_name": "Technology"}


async def test_add_symbols_to_watchlist(account_api, httpx_mock):
    # Mock get_watchlists (list endpoint)
    httpx_mock.add_response(
        url=re.compile(r"https://api\.robinhood\.com/midlands/lists/\?owner_type="),
        json={
            "results": [
                {"id": "wl-abc", "display_name": "Main", "name": "default"},
            ],
        },
    )
    # Mock get_watchlists (items endpoint)
    httpx_mock.add_response(
        url=re.compile(r"https://api\.robinhood\.com/midlands/lists/items/\?list_id=wl-abc"),
        json={"results": []},
    )
    # Mock instrument lookup
    httpx_mock.add_response(
        url=re.compile(r"https://api\.robinhood\.com/instruments/\?.*"),
        json={
            "results": [
                {"id": "inst-1", "url": "https://api.robinhood.com/instruments/inst-1/", "symbol": "AAPL", "name": "Apple Inc"},
            ],
            "next": None,
        },
    )
    # Mock bulk update POST
    httpx_mock.add_response(
        url="https://api.robinhood.com/midlands/lists/items/",
        method="POST",
        json={"success": True},
    )
    result = await account_api.add_symbols_to_watchlist(["AAPL"])
    assert result == {"success": True}

    # Verify POST payload
    request = httpx_mock.get_requests()[-1]
    import json
    payload = json.loads(request.content)
    assert "wl-abc" in payload
    assert payload["wl-abc"][0]["operation"] == "create"
    assert payload["wl-abc"][0]["object_id"] == "inst-1"


async def test_remove_symbols_from_watchlist(account_api, httpx_mock):
    # Mock get_watchlists (list endpoint)
    httpx_mock.add_response(
        url=re.compile(r"https://api\.robinhood\.com/midlands/lists/\?owner_type="),
        json={
            "results": [
                {"id": "wl-abc", "display_name": "Main", "name": "default"},
            ],
        },
    )
    # Mock get_watchlists (items endpoint)
    httpx_mock.add_response(
        url=re.compile(r"https://api\.robinhood\.com/midlands/lists/items/\?list_id=wl-abc"),
        json={"results": []},
    )
    # Mock instrument lookup
    httpx_mock.add_response(
        url=re.compile(r"https://api\.robinhood\.com/instruments/\?.*"),
        json={
            "results": [
                {"id": "inst-2", "url": "https://api.robinhood.com/instruments/inst-2/", "symbol": "TSLA", "name": "Tesla Inc"},
            ],
            "next": None,
        },
    )
    # Mock bulk update POST
    httpx_mock.add_response(
        url="https://api.robinhood.com/midlands/lists/items/",
        method="POST",
        json={"success": True},
    )
    result = await account_api.remove_symbols_from_watchlist(["TSLA"])
    assert result == {"success": True}

    # Verify POST payload
    request = httpx_mock.get_requests()[-1]
    import json
    payload = json.loads(request.content)
    assert payload["wl-abc"][0]["operation"] == "delete"
    assert payload["wl-abc"][0]["object_id"] == "inst-2"


async def test_add_symbols_watchlist_not_found(account_api, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r"https://api\.robinhood\.com/midlands/lists/\?owner_type="),
        json={
            "results": [
                {"id": "wl-abc", "display_name": "Other List", "name": "other"},
            ],
        },
    )
    httpx_mock.add_response(
        url=re.compile(r"https://api\.robinhood\.com/midlands/lists/items/\?list_id=wl-abc"),
        json={"results": []},
    )
    with pytest.raises(ValueError, match="Watchlist 'Main' not found"):
        await account_api.add_symbols_to_watchlist(["AAPL"])


async def test_remove_symbols_watchlist_not_found(account_api, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r"https://api\.robinhood\.com/midlands/lists/\?owner_type="),
        json={"results": []},
    )
    with pytest.raises(ValueError, match="not found"):
        await account_api.remove_symbols_from_watchlist(["AAPL"])


async def test_get_dividends(account_api, httpx_mock):
    httpx_mock.add_response(
        url="https://api.robinhood.com/dividends/",
        json={
            "results": [
                {"id": "div1", "amount": "1.50", "state": "paid"},
            ],
            "next": None,
        },
    )
    dividends = await account_api.get_dividends()
    assert len(dividends) == 1
    assert float(dividends[0].amount) == 1.50
