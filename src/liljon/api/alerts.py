"""AlertsAPI: price alerts and indicator alerts for instruments."""

from __future__ import annotations

from typing import Any

from liljon import _endpoints as ep
from liljon._http import HttpTransport
from liljon.models.alerts import AlertSettings

# ── Valid parameter values ───────────────────────────────────────────────
#
# setting_type — Price alerts:
#   'price_above'          Price rises above target
#   'price_below'          Price falls below target
#
# setting_type — Indicator alerts:
#   'rsi_above'            RSI crosses above overbought level
#   'rsi_below'            RSI crosses below oversold level
#   'price_above_sma'      Price crosses above Simple Moving Average
#   'price_below_sma'      Price crosses below Simple Moving Average
#   'price_above_ema'      Price crosses above Exponential Moving Average
#   'price_below_ema'      Price crosses below Exponential Moving Average
#   'price_above_vwap'     Price crosses above Volume-Weighted Average Price
#   'price_below_vwap'     Price crosses below Volume-Weighted Average Price
#   'macd_cross_above'     MACD crosses above signal line
#   'macd_cross_below'     MACD crosses below signal line
#   'bollinger_above'      Price crosses above upper Bollinger Band
#   'bollinger_below'      Price crosses below lower Bollinger Band
#
# interval (indicator alerts only):
#   '5minute', '10minute', 'hour', 'day', 'week'
#
# period (indicator alerts only):
#   Integer number of intervals for the indicator calculation (e.g. 14 for RSI).
#
# overbought_level / oversold_level (RSI alerts only):
#   Integer 0–100.  Defaults are typically 70 (overbought) and 30 (oversold).
# ─────────────────────────────────────────────────────────────────────────


class AlertsAPI:
    """Custom price and indicator alerts for instruments."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    # ── Read ─────────────────────────────────────────────────────────────

    async def get_alerts(self, instrument_id: str) -> AlertSettings:
        """Get all alert settings for an instrument."""
        params = {"allow_multiple": "true", "sort_by": "created_at"}
        data = await self._transport.get(
            ep.notification_settings(instrument_id), params=params
        )
        return AlertSettings(**data)

    # ── Create ───────────────────────────────────────────────────────────

    async def create_alert(
        self,
        instrument_id: str,
        setting_type: str,
        enabled: bool = True,
        price: str | None = None,
        interval: str | None = None,
        period: int | None = None,
        overbought_level: int | None = None,
        oversold_level: int | None = None,
    ) -> AlertSettings:
        """Create an alert for an instrument.

        Args:
            instrument_id: Instrument UUID.
            setting_type: Alert type.
                Price alerts: 'price_above', 'price_below'.
                Indicator alerts: 'rsi_above', 'rsi_below',
                    'price_above_sma', 'price_below_sma',
                    'price_above_ema', 'price_below_ema',
                    'price_above_vwap', 'price_below_vwap',
                    'macd_cross_above', 'macd_cross_below',
                    'bollinger_above', 'bollinger_below'.
            enabled: Whether the alert is active (default True).
            price: Target price string (required for price_above/price_below).
            interval: Candle interval for indicator alerts:
                '5minute', '10minute', 'hour', 'day', 'week'.
            period: Number of intervals for indicator calculation
                (e.g. 14 for RSI, 20 for SMA/EMA/Bollinger).
            overbought_level: RSI overbought threshold 0–100 (default 70).
            oversold_level: RSI oversold threshold 0–100 (default 30).
        """
        setting: dict[str, Any] = {
            "enabled": enabled,
            "setting_type": setting_type,
        }
        if price is not None:
            setting["price"] = price
        if interval is not None:
            setting["interval"] = interval
        if period is not None:
            setting["period"] = period
        if overbought_level is not None:
            setting["overbought_level"] = overbought_level
        if oversold_level is not None:
            setting["oversold_level"] = oversold_level

        params = {"allow_multiple": "true", "sort_by": "created_at"}
        data = await self._transport.post(
            ep.notification_settings(instrument_id),
            json={"settings": [setting]},
            params=params,
        )
        return AlertSettings(**data)

    async def create_alerts(
        self, instrument_id: str, settings: list[dict[str, Any]]
    ) -> AlertSettings:
        """Create multiple alerts for an instrument in one request.

        Args:
            instrument_id: Instrument UUID.
            settings: List of alert setting dicts. Each dict should contain
                'setting_type' and relevant fields (see create_alert for values).
        """
        params = {"allow_multiple": "true", "sort_by": "created_at"}
        data = await self._transport.post(
            ep.notification_settings(instrument_id),
            json={"settings": settings},
            params=params,
        )
        return AlertSettings(**data)

    # ── Update ───────────────────────────────────────────────────────────

    async def update_alert(
        self,
        instrument_id: str,
        alert_id: str,
        setting_type: str,
        enabled: bool | None = None,
        price: str | None = None,
        interval: str | None = None,
        period: int | None = None,
        overbought_level: int | None = None,
        oversold_level: int | None = None,
    ) -> AlertSettings:
        """Update an existing alert for an instrument.

        Args:
            instrument_id: Instrument UUID.
            alert_id: Alert UUID to update.
            setting_type: Alert type (must match existing alert).
                Price alerts: 'price_above', 'price_below'.
                Indicator alerts: 'rsi_above', 'rsi_below',
                    'price_above_sma', 'price_below_sma',
                    'price_above_ema', 'price_below_ema',
                    'price_above_vwap', 'price_below_vwap',
                    'macd_cross_above', 'macd_cross_below',
                    'bollinger_above', 'bollinger_below'.
            enabled: Enable or disable the alert.
            price: New target price string.
            interval: New candle interval:
                '5minute', '10minute', 'hour', 'day', 'week'.
            period: New indicator period.
            overbought_level: New RSI overbought threshold 0–100.
            oversold_level: New RSI oversold threshold 0–100.
        """
        setting: dict[str, Any] = {
            "id": alert_id,
            "setting_type": setting_type,
        }
        if enabled is not None:
            setting["enabled"] = enabled
        if price is not None:
            setting["price"] = price
        if interval is not None:
            setting["interval"] = interval
        if period is not None:
            setting["period"] = period
        if overbought_level is not None:
            setting["overbought_level"] = overbought_level
        if oversold_level is not None:
            setting["oversold_level"] = oversold_level

        params = {"allow_multiple": "true", "sort_by": "created_at"}
        data = await self._transport.patch(
            ep.notification_settings(instrument_id),
            json={"settings": [setting]},
            params=params,
        )
        return AlertSettings(**data)

    async def update_alerts(
        self, instrument_id: str, settings: list[dict[str, Any]]
    ) -> AlertSettings:
        """Update multiple alerts for an instrument in one request.

        Args:
            instrument_id: Instrument UUID.
            settings: List of alert setting dicts. Each must include 'id' and
                'setting_type', plus any fields to update.
        """
        params = {"allow_multiple": "true", "sort_by": "created_at"}
        data = await self._transport.patch(
            ep.notification_settings(instrument_id),
            json={"settings": settings},
            params=params,
        )
        return AlertSettings(**data)

    # ── Convenience: Price alerts ────────────────────────────────────────

    async def create_price_above_alert(
        self, instrument_id: str, price: str
    ) -> AlertSettings:
        """Create an alert that triggers when price rises above target."""
        return await self.create_alert(instrument_id, "price_above", price=price)

    async def create_price_below_alert(
        self, instrument_id: str, price: str
    ) -> AlertSettings:
        """Create an alert that triggers when price falls below target."""
        return await self.create_alert(instrument_id, "price_below", price=price)

    # ── Convenience: RSI alerts ──────────────────────────────────────────

    async def create_rsi_above_alert(
        self,
        instrument_id: str,
        interval: str = "day",
        period: int = 14,
        overbought_level: int = 70,
    ) -> AlertSettings:
        """Create an alert that triggers when RSI crosses above overbought level.

        Args:
            instrument_id: Instrument UUID.
            interval: '5minute', '10minute', 'hour', 'day', 'week'.
            period: RSI look-back periods (default 14).
            overbought_level: Threshold 0–100 (default 70).
        """
        return await self.create_alert(
            instrument_id,
            "rsi_above",
            interval=interval,
            period=period,
            overbought_level=overbought_level,
        )

    async def create_rsi_below_alert(
        self,
        instrument_id: str,
        interval: str = "day",
        period: int = 14,
        oversold_level: int = 30,
    ) -> AlertSettings:
        """Create an alert that triggers when RSI crosses below oversold level.

        Args:
            instrument_id: Instrument UUID.
            interval: '5minute', '10minute', 'hour', 'day', 'week'.
            period: RSI look-back periods (default 14).
            oversold_level: Threshold 0–100 (default 30).
        """
        return await self.create_alert(
            instrument_id,
            "rsi_below",
            interval=interval,
            period=period,
            oversold_level=oversold_level,
        )

    # ── Convenience: Moving average alerts ───────────────────────────────

    async def create_sma_cross_alert(
        self,
        instrument_id: str,
        direction: str = "above",
        interval: str = "day",
        period: int = 20,
    ) -> AlertSettings:
        """Create an alert when price crosses a Simple Moving Average.

        Args:
            instrument_id: Instrument UUID.
            direction: 'above' or 'below'.
            interval: '5minute', '10minute', 'hour', 'day', 'week'.
            period: SMA look-back periods (default 20).
        """
        setting_type = f"price_{direction}_sma"
        return await self.create_alert(
            instrument_id, setting_type, interval=interval, period=period
        )

    async def create_ema_cross_alert(
        self,
        instrument_id: str,
        direction: str = "above",
        interval: str = "day",
        period: int = 20,
    ) -> AlertSettings:
        """Create an alert when price crosses an Exponential Moving Average.

        Args:
            instrument_id: Instrument UUID.
            direction: 'above' or 'below'.
            interval: '5minute', '10minute', 'hour', 'day', 'week'.
            period: EMA look-back periods (default 20).
        """
        setting_type = f"price_{direction}_ema"
        return await self.create_alert(
            instrument_id, setting_type, interval=interval, period=period
        )

    # ── Convenience: VWAP alerts ─────────────────────────────────────────

    async def create_vwap_cross_alert(
        self,
        instrument_id: str,
        direction: str = "above",
        interval: str = "day",
    ) -> AlertSettings:
        """Create an alert when price crosses the Volume-Weighted Average Price.

        Args:
            instrument_id: Instrument UUID.
            direction: 'above' or 'below'.
            interval: '5minute', '10minute', 'hour', 'day', 'week'.
        """
        setting_type = f"price_{direction}_vwap"
        return await self.create_alert(
            instrument_id, setting_type, interval=interval
        )

    # ── Convenience: MACD alerts ─────────────────────────────────────────

    async def create_macd_cross_alert(
        self,
        instrument_id: str,
        direction: str = "above",
        interval: str = "day",
    ) -> AlertSettings:
        """Create an alert when MACD crosses the signal line.

        Args:
            instrument_id: Instrument UUID.
            direction: 'above' (bullish crossover) or 'below' (bearish crossover).
            interval: '5minute', '10minute', 'hour', 'day', 'week'.
        """
        setting_type = f"macd_cross_{direction}"
        return await self.create_alert(
            instrument_id, setting_type, interval=interval
        )

    # ── Convenience: Bollinger Band alerts ───────────────────────────────

    async def create_bollinger_alert(
        self,
        instrument_id: str,
        direction: str = "above",
        interval: str = "day",
        period: int = 20,
    ) -> AlertSettings:
        """Create an alert when price crosses a Bollinger Band.

        Args:
            instrument_id: Instrument UUID.
            direction: 'above' (upper band) or 'below' (lower band).
            interval: '5minute', '10minute', 'hour', 'day', 'week'.
            period: Bollinger Band look-back periods (default 20).
        """
        setting_type = f"bollinger_{direction}"
        return await self.create_alert(
            instrument_id, setting_type, interval=interval, period=period
        )
