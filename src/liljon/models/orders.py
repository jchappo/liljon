"""Pydantic models for order-related API responses."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class OrderResult(BaseModel):
    """Unified order result across stocks, options, and crypto."""

    id: str
    url: str | None = None
    account_url: str | None = None
    instrument_url: str | None = None
    symbol: str | None = None
    side: str | None = None
    type: str | None = None
    time_in_force: str | None = None
    trigger: str | None = None
    price: Decimal | None = None
    stop_price: Decimal | None = None
    quantity: Decimal | None = None
    cumulative_quantity: Decimal | None = None
    average_price: Decimal | None = None
    fees: Decimal | None = None
    state: str | None = None
    reject_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_transaction_at: datetime | None = None
    executions: list[dict] = []
    response_category: str | None = None
