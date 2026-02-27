"""Pydantic models for index-related API responses."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class IndexInstrument(BaseModel):
    """An index instrument (SPX, NDX, VIX, etc.)."""

    id: str
    symbol: str
    simple_name: str | None = None
    description: str | None = None
    tradable_chain_ids: list[str] = []
    state: str | None = None


class IndexQuote(BaseModel):
    """Real-time value for an index."""

    instrument_id: str | None = None
    symbol: str | None = None
    value: Decimal | None = None
    venue_timestamp: datetime | None = None
    state: str | None = None
    updated_at: datetime | None = None


class IndexFundamentals(BaseModel):
    """Fundamental data for an index (high/low, 52-week range)."""

    id: str | None = None
    symbol: str | None = None
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    high_52_weeks: Decimal | None = None
    low_52_weeks: Decimal | None = None
    previous_close: Decimal | None = None
    previous_close_date: str | None = None
    updated_at: datetime | None = None


class IndexClose(BaseModel):
    """Previous close value for an index."""

    id: str | None = None
    symbol: str | None = None
    close_value: Decimal | None = None
    date: str | None = None
    source: str | None = None
    updated_at: datetime | None = None
