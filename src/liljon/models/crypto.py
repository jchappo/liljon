"""Pydantic models for crypto-related API responses."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class CryptoPair(BaseModel):
    """A tradable cryptocurrency pair (e.g. BTC-USD)."""

    id: str
    code: str
    symbol: str
    name: str
    tradability: str | None = None
    min_order_size: Decimal | None = None
    max_order_size: Decimal | None = None
    min_order_price_increment: Decimal | None = None
    min_order_quantity_increment: Decimal | None = None
    asset_currency: dict | None = None
    quote_currency: dict | None = None


class CryptoQuote(BaseModel):
    """Real-time quote for a crypto pair."""

    id: str | None = None
    symbol: str | None = None
    mark_price: Decimal | None = None
    ask_price: Decimal | None = None
    bid_price: Decimal | None = None
    high_price: Decimal | None = None
    low_price: Decimal | None = None
    open_price: Decimal | None = None
    volume: Decimal | None = None
    updated_at: datetime | None = None


class CryptoHolding(BaseModel):
    """A crypto holding in the user's account."""

    id: str | None = None
    currency: dict | None = None
    quantity: Decimal | None = None
    quantity_available: Decimal | None = None
    cost_bases: list[dict] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CryptoHistoricalBar(BaseModel):
    """Single OHLCV bar for crypto historical data."""

    begins_at: datetime | None = None
    open_price: Decimal | None = None
    close_price: Decimal | None = None
    high_price: Decimal | None = None
    low_price: Decimal | None = None
    volume: Decimal | None = None
    session: str | None = None
    interpolated: bool = False
