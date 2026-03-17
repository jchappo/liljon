"""Pydantic models for price and indicator alert API responses."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class AlertSetting(BaseModel):
    """A single price or indicator alert setting.

    setting_type values:
        Price alerts: 'price_above', 'price_below'.
        Indicator alerts: 'rsi_above', 'rsi_below',
            'price_above_sma', 'price_below_sma',
            'price_above_ema', 'price_below_ema',
            'price_above_vwap', 'price_below_vwap',
            'macd_above_signal', 'macd_below_signal',
            'price_above_boll_upper', 'price_below_boll_lower'.

    interval values (indicator alerts):
        '5m', '10m', '1h', '1d', '1w'.
    """

    id: str | None = None
    setting_type: str | None = None
    enabled: bool | None = None
    price: Decimal | None = None
    value: Decimal | None = None
    interval: str | None = None
    period: int | None = None
    # MACD-specific fields
    fast_period: int | None = None
    slow_period: int | None = None
    signal_period: int | None = None
    # Bollinger-specific fields
    std_dev: Decimal | None = None
    ma_type: str | None = None
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
