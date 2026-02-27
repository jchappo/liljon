"""Pydantic models for options-related API responses."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class OptionChain(BaseModel):
    """An options chain for an underlying instrument."""

    id: str
    symbol: str
    can_open_position: bool = False
    cash_component: Decimal | None = None
    expiration_dates: list[str] = []
    underlying_instruments: list[dict] = []
    min_ticks: dict | None = None
    trade_value_multiplier: Decimal | None = None


class OptionInstrument(BaseModel):
    """A specific option contract."""

    id: str
    url: str
    chain_id: str
    chain_symbol: str
    type: str  # "call" or "put"
    strike_price: Decimal
    expiration_date: date
    state: str | None = None
    tradability: str | None = None
    issue_date: date | None = None
    cutoff_price: Decimal | None = None
    min_ticks: dict | None = None
    rhs_tradability: str | None = None
    sellout_datetime: datetime | None = None


class OptionMarketData(BaseModel):
    """Real-time market data (greeks, prices) for an option contract."""

    instrument_id: str | None = None
    mark_price: Decimal | None = None
    ask_price: Decimal | None = None
    ask_size: int | None = None
    bid_price: Decimal | None = None
    bid_size: int | None = None
    last_trade_price: Decimal | None = None
    last_trade_size: int | None = None
    high_price: Decimal | None = None
    low_price: Decimal | None = None
    volume: int | None = None
    open_interest: int | None = None
    implied_volatility: Decimal | None = None
    delta: Decimal | None = None
    gamma: Decimal | None = None
    theta: Decimal | None = None
    vega: Decimal | None = None
    rho: Decimal | None = None
    chance_of_profit_long: Decimal | None = None
    chance_of_profit_short: Decimal | None = None
    previous_close_price: Decimal | None = None
    adjusted_mark_price: Decimal | None = None
    break_even_price: Decimal | None = None


class OptionPosition(BaseModel):
    """An open option position in the user's account."""

    id: str | None = None
    url: str | None = None
    option_url: str | None = None
    option_id: str | None = None
    chain_id: str | None = None
    chain_symbol: str | None = None
    type: str | None = None
    quantity: Decimal | None = None
    average_price: Decimal | None = None
    pending_buy_quantity: Decimal | None = None
    pending_sell_quantity: Decimal | None = None
    intraday_quantity: Decimal | None = None
    intraday_average_open_price: Decimal | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
