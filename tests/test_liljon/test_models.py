"""Tests for Pydantic models."""

from datetime import date, datetime, timezone
from decimal import Decimal

from liljon.models.account import AccountProfile, Position, PortfolioProfile, Watchlist
from liljon.models.common import PaginatedResponse
from liljon.models.crypto import CryptoPair, CryptoQuote
from liljon.models.futures import FuturesContract, FuturesQuote
from liljon.models.indexes import IndexInstrument, IndexQuote
from liljon.models.options import OptionChain, OptionInstrument, OptionMarketData
from liljon.models.orders import OrderResult
from liljon.models.stocks import Fundamentals, HistoricalBar, NewsArticle, StockQuote
from liljon.auth.models import ChallengeInfo, LoginResult, TokenData


def test_stock_quote_from_dict():
    q = StockQuote(
        symbol="AAPL",
        last_trade_price=Decimal("150.25"),
        ask_price=Decimal("150.30"),
        bid_price=Decimal("150.20"),
    )
    assert q.symbol == "AAPL"
    assert q.last_trade_price == Decimal("150.25")


def test_stock_quote_optional_fields():
    q = StockQuote(symbol="MSFT")
    assert q.last_trade_price is None
    assert q.trading_halted is False


def test_historical_bar():
    bar = HistoricalBar(
        open_price=Decimal("100.00"),
        close_price=Decimal("105.00"),
        high_price=Decimal("106.00"),
        low_price=Decimal("99.50"),
        volume=1000000,
    )
    assert bar.close_price == Decimal("105.00")
    assert bar.interpolated is False


def test_fundamentals():
    f = Fundamentals(symbol="AAPL", market_cap=Decimal("3000000000000"), pe_ratio=Decimal("28.5"))
    assert f.symbol == "AAPL"
    assert f.market_cap == Decimal("3000000000000")


def test_news_article():
    a = NewsArticle(title="Test Article", source="Reuters", url="https://example.com")
    assert a.title == "Test Article"


def test_option_chain():
    chain = OptionChain(
        id="chain1",
        symbol="AAPL",
        expiration_dates=["2026-03-20", "2026-04-17"],
    )
    assert len(chain.expiration_dates) == 2


def test_option_instrument():
    oi = OptionInstrument(
        id="opt1",
        url="https://api.robinhood.com/options/instruments/opt1/",
        chain_id="chain1",
        chain_symbol="AAPL",
        type="call",
        strike_price=Decimal("150.00"),
        expiration_date=date(2026, 3, 20),
    )
    assert oi.type == "call"
    assert oi.strike_price == Decimal("150.00")


def test_option_market_data():
    md = OptionMarketData(
        mark_price=Decimal("5.50"),
        delta=Decimal("0.55"),
        implied_volatility=Decimal("0.35"),
    )
    assert md.delta == Decimal("0.55")


def test_crypto_pair():
    cp = CryptoPair(id="pair1", code="BTC-USD", symbol="BTC", name="Bitcoin")
    assert cp.code == "BTC-USD"


def test_crypto_quote():
    cq = CryptoQuote(mark_price=Decimal("50000.00"), volume=Decimal("1234.5"))
    assert cq.mark_price == Decimal("50000.00")


def test_futures_contract():
    fc = FuturesContract(id="fc1", symbol="/ES", underlying="SPX", active=True)
    assert fc.symbol == "/ES"


def test_futures_quote():
    fq = FuturesQuote(symbol="/ES", last_trade_price=Decimal("4500.00"), volume=100000)
    assert fq.last_trade_price == Decimal("4500.00")


def test_index_instrument():
    idx = IndexInstrument(id="idx1", symbol="SPX", tradable_chain_ids=["chain1", "chain2"])
    assert len(idx.tradable_chain_ids) == 2


def test_index_quote():
    iq = IndexQuote(symbol="SPX", value=Decimal("5000.00"))
    assert iq.value == Decimal("5000.00")


def test_account_profile():
    ap = AccountProfile(account_number="ABC123", buying_power=Decimal("10000.00"))
    assert ap.account_number == "ABC123"


def test_portfolio_profile():
    pp = PortfolioProfile(equity=Decimal("50000.00"), withdrawable_amount=Decimal("5000.00"))
    assert pp.equity == Decimal("50000.00")


def test_position():
    pos = Position(symbol="AAPL", quantity=Decimal("10"), average_buy_price=Decimal("150.00"))
    assert pos.quantity == Decimal("10")


def test_order_result():
    order = OrderResult(
        id="order1",
        symbol="AAPL",
        side="buy",
        type="market",
        state="filled",
        quantity=Decimal("10"),
        average_price=Decimal("150.00"),
        cumulative_quantity=Decimal("10"),
    )
    assert order.state == "filled"


def test_token_data():
    td = TokenData(
        access_token="acc",
        refresh_token="ref",
        username="user",
        expires_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )
    assert td.token_type == "Bearer"


def test_challenge_info():
    ci = ChallengeInfo(challenge_id="c1", challenge_type="sms", machine_id="m1")
    assert ci.status == "issued"


def test_login_result():
    lr = LoginResult(status="logged_in", message="OK", username="user")
    assert lr.status == "logged_in"


def test_watchlist_with_id():
    wl = Watchlist(id="wl-123", display_name="My First List", name="default")
    assert wl.id == "wl-123"
    assert wl.display_name == "My First List"
    assert wl.items == []


def test_watchlist_id_defaults_none():
    wl = Watchlist(display_name="Test")
    assert wl.id is None


def test_paginated_response():
    pr = PaginatedResponse[dict](results=[{"a": 1}], next_url="http://next", count=1)
    assert len(pr.results) == 1
