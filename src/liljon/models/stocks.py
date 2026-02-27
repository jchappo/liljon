"""Pydantic models for stock-related API responses."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class StockQuote(BaseModel):
    """Real-time quote for a stock or ETF."""

    symbol: str
    last_trade_price: Decimal | None = None
    last_extended_hours_trade_price: Decimal | None = None
    ask_price: Decimal | None = None
    ask_size: int | None = None
    bid_price: Decimal | None = None
    bid_size: int | None = None
    previous_close: Decimal | None = None
    adjusted_previous_close: Decimal | None = None
    updated_at: datetime | None = None
    trading_halted: bool = False
    instrument_url: str | None = None
    instrument_id: str | None = None


class StockInstrument(BaseModel):
    """Static metadata for a stock instrument."""

    id: str
    url: str
    symbol: str
    name: str
    type: str | None = None
    country: str | None = None
    tradeable: bool = False
    tradability: str | None = None
    market_url: str | None = None
    simple_name: str | None = None
    tradable_chain_id: str | None = None
    state: str | None = None
    day_trade_ratio: Decimal | None = None
    maintenance_ratio: Decimal | None = None
    margin_initial_ratio: Decimal | None = None


class Fundamentals(BaseModel):
    """Fundamental data for a stock."""

    symbol: str | None = None
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    volume: Decimal | None = None
    average_volume: Decimal | None = None
    average_volume_2_weeks: Decimal | None = None
    high_52_weeks: Decimal | None = None
    low_52_weeks: Decimal | None = None
    market_cap: Decimal | None = None
    dividend_yield: Decimal | None = None
    pe_ratio: Decimal | None = None
    pb_ratio: Decimal | None = None
    description: str | None = None
    headquarters_city: str | None = None
    headquarters_state: str | None = None
    sector: str | None = None
    industry: str | None = None
    num_employees: int | None = None
    year_founded: int | None = None
    ceo: str | None = None


class HistoricalBar(BaseModel):
    """Single OHLCV bar from historical data."""

    begins_at: datetime | None = None
    open_price: Decimal | None = None
    close_price: Decimal | None = None
    high_price: Decimal | None = None
    low_price: Decimal | None = None
    volume: int | None = None
    session: str | None = None
    interpolated: bool = False


class NewsArticle(BaseModel):
    """News article from Robinhood's news feed."""

    uuid: str | None = None
    title: str = ""
    source: str = ""
    summary: str | None = None
    preview_text: str | None = None
    url: str | None = None
    published_at: str | None = None
    relay_url: str | None = None
    currency_id: str | None = None
