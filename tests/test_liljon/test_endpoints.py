"""Tests for the pure URL template functions."""

from liljon import _endpoints as ep


def test_login_url():
    assert ep.login() == "https://api.robinhood.com/oauth2/token/"


def test_logout_url():
    assert ep.logout() == "https://api.robinhood.com/oauth2/revoke_token/"


def test_challenge_respond():
    url = ep.challenge_respond("abc123")
    assert url == "https://api.robinhood.com/challenge/abc123/respond/"


def test_pathfinder_urls():
    assert ep.pathfinder_user_machine() == "https://api.robinhood.com/pathfinder/user_machine/"
    url = ep.pathfinder_inquiry("m1")
    assert url == "https://api.robinhood.com/pathfinder/inquiries/m1/user_view/"


def test_quotes():
    url = ep.quotes("AAPL,MSFT")
    assert "symbols=AAPL,MSFT" in url


def test_historicals():
    url = ep.historicals("AAPL", "day", "year", "regular")
    assert "AAPL" in url
    assert "interval=day" in url
    assert "span=year" in url
    assert "bounds=regular" in url


def test_option_chains():
    url = ep.option_chains("inst123")
    assert "equity_instrument_ids=inst123" in url


def test_futures_contract():
    url = ep.futures_contract("c1")
    assert "arsenal/v1/futures/contracts/c1" in url


def test_futures_quote():
    url = ep.futures_quote("c1")
    assert "marketdata/futures/quotes/v1/c1" in url


def test_index_by_symbol():
    url = ep.index_by_symbol("SPX")
    assert "symbol=SPX" in url


def test_index_quote():
    url = ep.index_quote("idx1")
    assert "marketdata/indexes/values/v1/idx1" in url


def test_crypto_quotes():
    url = ep.crypto_quotes("pair1")
    assert "forex/quotes/pair1" in url


def test_stock_orders():
    assert ep.stock_orders() == "https://api.robinhood.com/orders/"
    assert ep.cancel_stock_order("o1") == "https://api.robinhood.com/orders/o1/cancel/"


def test_market_hours():
    url = ep.market_hours("XNYS", "2026-02-26")
    assert "XNYS" in url
    assert "2026-02-26" in url


def test_watchlist_bulk_update():
    assert ep.watchlist_bulk_update() == "https://api.robinhood.com/midlands/lists/items/"


def test_screeners():
    url = ep.screeners(include_filters=True)
    assert url == "https://bonfire.robinhood.com/screeners?include_filters=true"
    url_no_filters = ep.screeners(include_filters=False)
    assert url_no_filters == "https://bonfire.robinhood.com/screeners?include_filters=false"


def test_screener_presets():
    assert ep.screener_presets() == "https://bonfire.robinhood.com/screeners/presets/"


def test_screener_by_id():
    url = ep.screener("scr-42")
    assert url == "https://bonfire.robinhood.com/screeners/scr-42/"


def test_screener_indicators():
    assert ep.screener_indicators() == "https://bonfire.robinhood.com/screeners/indicators/"


def test_screener_scan():
    assert ep.screener_scan() == "https://bonfire.robinhood.com/screeners/scan/"
