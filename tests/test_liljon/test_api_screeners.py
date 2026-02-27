"""Tests for ScreenersAPI with mocked HTTP responses."""

import re

import pytest

from liljon._http import HttpTransport
from liljon.api.screeners import ScreenersAPI


@pytest.fixture
def transport():
    return HttpTransport(timeout=5.0)


@pytest.fixture
def screeners_api(transport):
    return ScreenersAPI(transport)


# ── get_screeners ──────────────────────────────────────────────────────────


async def test_get_screeners(screeners_api, httpx_mock):
    httpx_mock.add_response(
        url="https://bonfire.robinhood.com/screeners?include_filters=true",
        json={
            "results": [
                {
                    "id": "scr-1",
                    "display_name": "My Growth Screener",
                    "filters": [{"key": "market_cap", "filter": {"type": "RANGE", "min": 1000000000}, "is_hidden": False}],
                    "columns": ["last_price", "percent_change"],
                    "sort_by": "percent_change",
                    "sort_direction": "DESC",
                },
            ]
        },
    )
    screeners = await screeners_api.get_screeners()
    assert len(screeners) == 1
    assert screeners[0].id == "scr-1"
    assert screeners[0].display_name == "My Growth Screener"
    assert len(screeners[0].filters) == 1
    assert screeners[0].filters[0].key == "market_cap"


async def test_get_screeners_without_filters(screeners_api, httpx_mock):
    httpx_mock.add_response(
        url="https://bonfire.robinhood.com/screeners?include_filters=false",
        json={
            "results": [
                {"id": "scr-1", "display_name": "My Screener", "filters": [], "columns": []},
            ]
        },
    )
    screeners = await screeners_api.get_screeners(include_filters=False)
    assert len(screeners) == 1
    assert screeners[0].filters == []


async def test_get_screeners_empty(screeners_api, httpx_mock):
    httpx_mock.add_response(
        url="https://bonfire.robinhood.com/screeners?include_filters=true",
        json={"results": []},
    )
    screeners = await screeners_api.get_screeners()
    assert screeners == []


# ── get_presets ────────────────────────────────────────────────────────────


async def test_get_presets(screeners_api, httpx_mock):
    httpx_mock.add_response(
        url="https://bonfire.robinhood.com/screeners/presets/",
        json={
            "results": [
                {"id": "preset-1", "display_name": "Top Movers", "filters": [], "columns": ["last_price"]},
                {"id": "preset-2", "display_name": "Penny Stocks", "filters": [], "columns": ["last_price"]},
            ]
        },
    )
    presets = await screeners_api.get_presets()
    assert len(presets) == 2
    assert presets[0].display_name == "Top Movers"
    assert presets[1].display_name == "Penny Stocks"


# ── get_screener ───────────────────────────────────────────────────────────


async def test_get_screener(screeners_api, httpx_mock):
    httpx_mock.add_response(
        url="https://bonfire.robinhood.com/screeners/scr-42/",
        json={
            "id": "scr-42",
            "display_name": "Value Picks",
            "filters": [
                {"key": "pe_ratio", "filter": {"type": "RANGE", "max": 15}, "is_hidden": False},
            ],
            "columns": ["last_price", "pe_ratio"],
            "sort_by": "pe_ratio",
            "sort_direction": "ASC",
        },
    )
    screener = await screeners_api.get_screener("scr-42")
    assert screener.id == "scr-42"
    assert screener.display_name == "Value Picks"
    assert screener.filters[0].key == "pe_ratio"
    assert screener.sort_direction == "ASC"


# ── get_indicators ─────────────────────────────────────────────────────────


async def test_get_indicators(screeners_api, httpx_mock):
    httpx_mock.add_response(
        url="https://bonfire.robinhood.com/screeners/indicators/",
        json={
            "results": [
                {
                    "title": "Price & Volume",
                    "indicators": [
                        {
                            "key": "price_range",
                            "title": "Price Range",
                            "description": "Filter by stock price",
                            "filter_parameters": {
                                "type": "RANGE",
                                "options": [{"label": "$0-$10", "value": "0-10"}],
                            },
                        },
                        {
                            "key": "volume",
                            "title": "Volume",
                            "description": "Filter by volume",
                            "filter_parameters": {"type": "RANGE", "options": []},
                        },
                    ],
                },
                {
                    "title": "Fundamentals",
                    "indicators": [
                        {
                            "key": "market_cap",
                            "title": "Market Cap",
                            "description": "Filter by market cap",
                            "filter_parameters": {
                                "type": "SINGLE_SELECT",
                                "options": [
                                    {"label": "Large Cap", "value": "large"},
                                    {"label": "Small Cap", "value": "small"},
                                ],
                            },
                        },
                    ],
                },
            ]
        },
    )
    categories = await screeners_api.get_indicators()
    assert len(categories) == 2
    assert categories[0].title == "Price & Volume"
    assert len(categories[0].indicators) == 2
    assert categories[0].indicators[0].key == "price_range"
    assert categories[0].indicators[0].filter_parameters.type == "RANGE"
    assert categories[1].indicators[0].filter_parameters.options[0].label == "Large Cap"


async def test_get_indicators_empty(screeners_api, httpx_mock):
    httpx_mock.add_response(
        url="https://bonfire.robinhood.com/screeners/indicators/",
        json={"results": []},
    )
    categories = await screeners_api.get_indicators()
    assert categories == []


# ── scan ───────────────────────────────────────────────────────────────────


def _make_row(instrument_id: str, symbol: str, name: str, values: list[str]) -> dict:
    """Build a scan response row matching the Robinhood SDUI format."""
    items = [
        {"component": {"sdui_component_type": "TABLE_INSTRUMENT_NAME", "name": name, "symbol": symbol}},
    ]
    for v in values:
        items.append({"component": {"sdui_component_type": "TEXT", "text": {"text": v}}})
    return {"instrument_id": instrument_id, "instrument_symbol": symbol, "items": items}


async def test_scan_with_results(screeners_api, httpx_mock):
    httpx_mock.add_response(
        url="https://bonfire.robinhood.com/screeners/scan/",
        json={
            "rows": [
                {"instrument_id": "", "instrument_symbol": "", "items": []},
                _make_row("abc", "AAPL", "Apple Inc.", ["$150.25", "2.5%"]),
                _make_row("def", "MSFT", "Microsoft Corporation", ["$300.50", "1.8%"]),
            ],
            "subtitle": "2 results",
            "columns": [
                {"id": "instrument_symbol"},
                {"id": "last_price"},
                {"id": "percent_change"},
            ],
            "sort_by": "percent_change",
            "sort_direction": "DESC",
        },
    )
    response = await screeners_api.scan(
        indicators=[{"key": "market_cap", "filter": {"type": "SINGLE_SELECT", "value": "large"}}],
        sort_by="percent_change",
    )
    assert len(response.results) == 2
    assert response.results[0].symbol == "AAPL"
    assert response.results[0].name == "Apple Inc."
    assert response.results[0].values == ["$150.25", "2.5%"]
    assert response.results[1].instrument_id == "def"
    assert response.subtitle == "2 results"
    assert response.sort_by == "percent_change"


async def test_scan_default_columns(screeners_api, httpx_mock):
    httpx_mock.add_response(
        url="https://bonfire.robinhood.com/screeners/scan/",
        json={"rows": [], "subtitle": "0 results", "columns": []},
    )
    await screeners_api.scan(indicators=[{"key": "volume", "filter": {"type": "RANGE", "min": 1000000}}])

    request = httpx_mock.get_request()
    import json
    body = json.loads(request.content)
    assert body["columns"] == ["last_price", "percent_change"]
    assert body["sort_direction"] == "DESC"


async def test_scan_with_price_range_filter(screeners_api, httpx_mock):
    httpx_mock.add_response(
        url="https://bonfire.robinhood.com/screeners/scan/",
        json={
            "rows": [
                {"instrument_id": "", "instrument_symbol": "", "items": []},
                _make_row("ford-1", "F", "Ford Motor", ["$8.50"]),
            ],
            "subtitle": "1 result",
            "columns": [{"id": "instrument_symbol"}, {"id": "last_price"}],
        },
    )
    response = await screeners_api.scan(
        indicators=[{"key": "price_range", "filter": {"type": "RANGE", "min": 5, "max": 10}}],
        columns=["last_price"],
    )
    assert len(response.results) == 1
    assert response.results[0].symbol == "F"


async def test_scan_empty_results(screeners_api, httpx_mock):
    httpx_mock.add_response(
        url="https://bonfire.robinhood.com/screeners/scan/",
        json={"rows": [], "subtitle": "0 results", "columns": []},
    )
    response = await screeners_api.scan(indicators=[{"key": "pe_ratio", "filter": {"type": "RANGE", "max": 1}}])
    assert response.results == []
    assert response.subtitle == "0 results"


async def test_scan_post_payload(screeners_api, httpx_mock):
    """Verify the exact POST payload sent to the scan endpoint."""
    httpx_mock.add_response(
        url="https://bonfire.robinhood.com/screeners/scan/",
        json={"rows": [], "subtitle": "0 results", "columns": []},
    )
    indicators = [
        {"key": "market_cap", "filter": {"type": "SINGLE_SELECT", "value": "large"}},
        {"key": "sector", "filter": {"type": "MULTI_SELECT", "values": ["technology", "healthcare"]}},
    ]
    await screeners_api.scan(
        indicators=indicators,
        columns=["last_price", "market_cap", "sector"],
        sort_by="market_cap",
        sort_direction="ASC",
    )

    request = httpx_mock.get_request()
    import json
    body = json.loads(request.content)
    assert body["indicators"] == indicators
    assert body["columns"] == ["last_price", "market_cap", "sector"]
    assert body["sort_by"] == "market_cap"
    assert body["sort_direction"] == "ASC"
