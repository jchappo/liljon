"""Pydantic models for futures-related API responses."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class FuturesContract(BaseModel):
    """A futures contract instrument."""

    id: str
    symbol: str
    underlying: str | None = None
    expiration_date: str | None = None
    contract_size: Decimal | None = None
    tick_size: Decimal | None = None
    tick_value: Decimal | None = None
    state: str | None = None
    tradability: str | None = None
    active: bool = True


class FuturesQuote(BaseModel):
    """Real-time quote for a futures contract."""

    contract_id: str | None = None
    symbol: str | None = None
    last_trade_price: Decimal | None = None
    ask_price: Decimal | None = None
    bid_price: Decimal | None = None
    mark_price: Decimal | None = None
    high_price: Decimal | None = None
    low_price: Decimal | None = None
    open_price: Decimal | None = None
    previous_close: Decimal | None = None
    volume: int | None = None
    open_interest: int | None = None
    updated_at: datetime | None = None


class FuturesOrder(BaseModel):
    """A futures order (placed or historical)."""

    id: str
    account_url: str | None = None
    contract_id: str | None = None
    symbol: str | None = None
    side: str | None = None
    order_type: str | None = None
    quantity: Decimal | None = None
    price: Decimal | None = None
    stop_price: Decimal | None = None
    time_in_force: str | None = None
    state: str | None = None
    filled_quantity: Decimal | None = None
    average_price: Decimal | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    closing_strategy: str | None = None


class FuturesAccount(BaseModel):
    """The user's futures account summary."""

    id: str | None = None
    account_number: str | None = None
    equity: Decimal | None = None
    buying_power: Decimal | None = None
    cash: Decimal | None = None
    margin_used: Decimal | None = None
    unrealized_pnl: Decimal | None = None
    realized_pnl: Decimal | None = None
