"""Tests for pagination helpers."""

import re

import pytest

from liljon._http import HttpTransport
from liljon._pagination import paginate_cursor, paginate_results


@pytest.fixture
def transport():
    return HttpTransport(timeout=5.0)


async def test_paginate_results_single_page(transport, httpx_mock):
    httpx_mock.add_response(
        url="https://api.robinhood.com/items/",
        json={"results": [{"id": "1"}, {"id": "2"}], "next": None},
    )
    results = await paginate_results(transport, "https://api.robinhood.com/items/")
    assert len(results) == 2
    assert results[0]["id"] == "1"


async def test_paginate_results_multi_page(transport, httpx_mock):
    httpx_mock.add_response(
        url="https://api.robinhood.com/items/",
        json={"results": [{"id": "1"}], "next": "https://api.robinhood.com/items/?page=2"},
    )
    httpx_mock.add_response(
        url="https://api.robinhood.com/items/?page=2",
        json={"results": [{"id": "2"}], "next": None},
    )
    results = await paginate_results(transport, "https://api.robinhood.com/items/")
    assert len(results) == 2


async def test_paginate_results_filters_none(transport, httpx_mock):
    httpx_mock.add_response(
        url="https://api.robinhood.com/items/",
        json={"results": [{"id": "1"}, None, {"id": "3"}], "next": None},
    )
    results = await paginate_results(transport, "https://api.robinhood.com/items/")
    assert len(results) == 2


async def test_paginate_results_max_pages(transport, httpx_mock):
    # Use regex to match URL with or without query params for re-requested URLs
    httpx_mock.add_response(
        url=re.compile(r"https://api\.robinhood\.com/items/"),
        json={"results": [{"id": "x"}], "next": "https://api.robinhood.com/items/"},
        is_reusable=True,
    )
    results = await paginate_results(transport, "https://api.robinhood.com/items/", max_pages=3)
    assert len(results) == 3


async def test_paginate_cursor_single_page(transport, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r"https://api\.robinhood\.com/cursor-items/"),
        json={"results": [{"id": "1"}], "cursor": None},
    )
    results = await paginate_cursor(transport, "https://api.robinhood.com/cursor-items/")
    assert len(results) == 1


async def test_paginate_cursor_multi_page(transport, httpx_mock):
    # First request: no cursor param, returns cursor "c2"
    # Second request: with cursor=c2 param, returns no cursor
    # Use a list to track call count
    call_count = [0]
    original_get = transport.get

    async def mock_get(url, params=None, headers=None):
        call_count[0] += 1
        if call_count[0] == 1:
            return {"results": [{"id": "1"}], "cursor": "c2"}
        return {"results": [{"id": "2"}], "cursor": None}

    transport.get = mock_get
    results = await paginate_cursor(transport, "https://api.robinhood.com/cursor-items/")
    assert len(results) == 2
    assert call_count[0] == 2
    transport.get = original_get
