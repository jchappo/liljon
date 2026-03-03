"""Pydantic models for price and indicator alert API responses."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class AlertSetting(BaseModel):
    """A single price or indicator alert setting."""

    id: str | None = None
    setting_type: str | None = None
    enabled: bool | None = None
    price: Decimal | None = None
    interval: str | None = None
    period: int | None = None
    overbought_level: int | None = None
    oversold_level: int | None = None
    title: str | None = None
    subtitle: str | None = None
    editor_title: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AlertSettings(BaseModel):
    """Alert settings response for an instrument."""

    instrument_id: str | None = None
    cooldown_description: str | None = None
    settings: list[AlertSetting] = []
    ui_resources_digest: str | None = None
    context: dict | None = None
    price_alerts_limit_reached: bool | None = None
    indicator_alerts_limit_reached: bool | None = None
