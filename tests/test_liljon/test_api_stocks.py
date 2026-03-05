"""Tests for StocksAPI with mocked HTTP responses."""

import re

import pytest

from liljon._http import HttpTransport
from liljon.api.stocks import StocksAPI
from liljon.exceptions import InvalidSymbolError


@pytest.fixture
def transport():
    return HttpTransport(timeout=5.0)


@pytest.fixture
def stocks_api(transport):
    return StocksAPI(transport)


async def test_get_quotes(stocks_api, httpx_mock):
    httpx_mock.add_response(
        url="https://api.robinhood.com/marketdata/quotes/?symbols=AAPL,MSFT&bounds=regular&include_bbo_source=false&include_inactive=false",
        json={
            "results": [
                {"symbol": "AAPL", "last_trade_price": "150.25", "ask_price": "150.30", "bid_price": "150.20", "trading_halted": False},
                {"symbol": "MSFT", "last_trade_price": "300.50", "ask_price": "300.55", "bid_price": "300.45", "trading_halted": False},
            ]
        },
    )
    quotes = await stocks_api.get_quotes(["AAPL", "MSFT"])
    assert len(quotes) == 2
    assert quotes[0].symbol == "AAPL"
    assert float(quotes[0].last_trade_price) == 150.25


async def test_get_instrument_by_symbol(stocks_api, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r"https://api\.robinhood\.com/instruments/"),
        json={
            "results": [
                {"id": "abc", "url": "https://api.robinhood.com/instruments/abc/", "symbol": "AAPL", "name": "Apple Inc.", "tradeable": True},
            ]
        },
    )
    inst = await stocks_api.get_instrument_by_symbol("AAPL")
    assert inst.symbol == "AAPL"
    assert inst.id == "abc"


async def test_get_instrument_by_symbol_not_found(stocks_api, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r"https://api\.robinhood\.com/instruments/"),
        json={"results": []},
    )
    with pytest.raises(InvalidSymbolError):
        await stocks_api.get_instrument_by_symbol("FAKESYM")


async def test_get_instruments(stocks_api, httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r"https://api\.robinhood\.com/instruments/\?query=AAPL"),
        json={
            "results": [
                {"id": "abc", "url": "https://api.robinhood.com/instruments/abc/", "symbol": "AAPL", "name": "Apple Inc.", "tradeable": True},
                {"id": "def", "url": "https://api.robinhood.com/instruments/def/", "symbol": "AAPLX", "name": "Apple Fund", "tradeable": True},
            ]
        },
    )
    instruments = await stocks_api.get_instruments("AAPL")
    assert len(instruments) == 2
    assert instruments[0].symbol == "AAPL"
    assert instruments[1].symbol == "AAPLX"


async def test_get_instrument_by_id(stocks_api, httpx_mock):
    httpx_mock.add_response(
        url="https://api.robinhood.com/instruments/abc123/",
        json={"id": "abc123", "url": "https://api.robinhood.com/instruments/abc123/", "symbol": "AAPL", "name": "Apple Inc.", "tradeable": True},
    )
    inst = await stocks_api.get_instrument_by_id("abc123")
    assert inst.id == "abc123"
    assert inst.symbol == "AAPL"


async def test_get_instrument_by_id_with_url(stocks_api, httpx_mock):
    httpx_mock.add_response(
        url="https://api.robinhood.com/instruments/abc123/",
        json={"id": "abc123", "url": "https://api.robinhood.com/instruments/abc123/", "symbol": "AAPL", "name": "Apple Inc.", "tradeable": True},
    )
    inst = await stocks_api.get_instrument_by_id("https://api.robinhood.com/instruments/abc123/")
    assert inst.id == "abc123"
    assert inst.symbol == "AAPL"


async def test_get_fundamentals(stocks_api, httpx_mock):
    httpx_mock.add_response(
        url="https://api.robinhood.com/fundamentals/AAPL/?bounds=regular&include_inactive=true",
        json={"market_cap": "3000000000000", "pe_ratio": "28.5"},
    )
    f = await stocks_api.get_fundamentals("AAPL")
    assert f.symbol == "AAPL"
    assert float(f.market_cap) == 3000000000000


async def test_get_historicals(stocks_api, httpx_mock):
    httpx_mock.add_response(
        url="https://api.robinhood.com/marketdata/historicals/AAPL/?interval=day&span=year&bounds=regular",
        json={
            "historicals": [
                {"open_price": "100.00", "close_price": "105.00", "high_price": "106.00", "low_price": "99.50", "volume": 1000000, "interpolated": False},
                {"open_price": "105.00", "close_price": "103.00", "high_price": "107.00", "low_price": "102.00", "volume": 900000, "interpolated": False},
            ]
        },
    )
    bars = await stocks_api.get_historicals("AAPL", interval="day", span="year")
    assert len(bars) == 2
    assert float(bars[0].close_price) == 105.00


async def test_get_news(stocks_api, httpx_mock):
    httpx_mock.add_response(
        url="https://api.robinhood.com/midlands/news/AAPL/",
        json={
            "results": [
                {"title": "Apple earnings beat", "source": "Reuters", "url": "https://example.com/1"},
            ],
            "next": None,
        },
    )
    news = await stocks_api.get_news("AAPL")
    assert len(news) == 1
    assert news[0].title == "Apple earnings beat"


async def test_get_news_market_wide(stocks_api, httpx_mock):
    httpx_mock.add_response(
        url="https://api.robinhood.com/midlands/news/",
        json={
            "results": [
                {"title": "Markets rally on Fed news", "source": "AP", "url": "https://example.com/2"},
                {"title": "Oil prices surge", "source": "Reuters", "url": "https://example.com/3"},
            ],
            "next": None,
        },
    )
    news = await stocks_api.get_news()
    assert len(news) == 2
    assert news[0].title == "Markets rally on Fed news"


async def test_get_latest_price(stocks_api, httpx_mock):
    httpx_mock.add_response(
        url="https://api.robinhood.com/marketdata/quotes/?symbols=AAPL&bounds=regular&include_bbo_source=false&include_inactive=false",
        json={
            "results": [
                {"symbol": "AAPL", "last_trade_price": "150.25", "trading_halted": False},
            ]
        },
    )
    prices = await stocks_api.get_latest_price(["AAPL"])
    assert prices["AAPL"] == "150.25"
