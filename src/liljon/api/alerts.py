"""AlertsAPI: price alerts and indicator alerts for instruments."""

from __future__ import annotations

from typing import Any

from liljon import _endpoints as ep
from liljon._http import HttpTransport
from liljon.models.alerts import AlertSettings

# ── Valid parameter values ───────────────────────────────────────────────
#
# setting_type — Price alerts:
#   'price_above'              Price rises above target
#   'price_below'              Price falls below target
#
# setting_type — Indicator alerts:
#   'rsi_above'                RSI crosses above threshold
#   'rsi_below'                RSI crosses below threshold
#   'price_above_sma'          Price crosses above Simple Moving Average
#   'price_below_sma'          Price crosses below Simple Moving Average
#   'price_above_ema'          Price crosses above Exponential Moving Average
#   'price_below_ema'          Price crosses below Exponential Moving Average
#   'vwap_above'               Price crosses above Volume-Weighted Average Price
#   'vwap_below'               Price crosses below Volume-Weighted Average Price
#   'macd_above_signal'        MACD crosses above signal line
#   'macd_below_signal'        MACD crosses below signal line
#   'price_above_boll_upper'   Price crosses above upper Bollinger Band
#   'price_below_boll_lower'   Price crosses below lower Bollinger Band
#
# interval (indicator alerts only):
#   '5m', '10m', '1h', '1d', '1w'
#
# period (indicator alerts only):
#   Integer number of intervals for the indicator calculation (e.g. 14 for RSI).
#
# value (RSI and VWAP alerts):
#   Threshold value as string (e.g. '70' for RSI overbought, '25' for VWAP).
#
# MACD-specific parameters:
#   fast_period: int   Fast EMA period (default 12).
#   slow_period: int   Slow EMA period (default 26).
#   signal_period: int Signal line period (default 9).
#
# Bollinger-specific parameters:
#   std_dev: str       Standard deviations from MA (default "2.0").
#   ma_type: str       Moving average type (default "sma").
# ─────────────────────────────────────────────────────────────────────────

_DEFAULT_PARAMS = {"allow_multiple": "true", "sort_by": "created_at"}


class AlertsAPI:
    """Custom price and indicator alerts for instruments."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    # ── Read ─────────────────────────────────────────────────────────────

    async def get_alerts(self, instrument_id: str) -> AlertSettings:
        """Get all alert settings for an instrument."""
        data = await self._transport.get(
            ep.notification_settings(instrument_id), params=_DEFAULT_PARAMS
        )
        return AlertSettings(**data)

    # ── Create ───────────────────────────────────────────────────────────

    async def create_alert(
        self,
        instrument_id: str,
        setting_type: str,
        enabled: bool = True,
        price: str | None = None,
        value: str | int | None = None,
        interval: str | None = None,
        period: int | None = None,
        *,
        fast_period: int | None = None,
        slow_period: int | None = None,
        signal_period: int | None = None,
        std_dev: str | None = None,
        ma_type: str | None = None,
    ) -> AlertSettings:
        """Create an alert for an instrument.

        All alert types (price and indicator) are created via POST.

        Args:
            instrument_id: Instrument UUID.
            setting_type: Alert type.
                Price alerts: 'price_above', 'price_below'.
                Indicator alerts: 'rsi_above', 'rsi_below',
                    'price_above_sma', 'price_below_sma',
                    'price_above_ema', 'price_below_ema',
                    'vwap_above', 'vwap_below',
                    'macd_above_signal', 'macd_below_signal',
                    'price_above_boll_upper', 'price_below_boll_lower'.
            enabled: Whether the alert is active (default True).
            price: Target price string (required for price_above/price_below).
            value: Threshold value (for RSI: e.g. '70'; for VWAP: target value).
            interval: Candle interval for indicator alerts:
                '5m', '10m', '1h', '1d', '1w'.
            period: Number of intervals for indicator calculation
                (e.g. 14 for RSI, 20 for SMA/EMA/Bollinger).
            fast_period: MACD fast EMA period (default 12).
            slow_period: MACD slow EMA period (default 26).
            signal_period: MACD signal line period (default 9).
            std_dev: Bollinger Band standard deviations (default "2.0").
            ma_type: Bollinger Band moving average type (default "sma").
        """
        setting: dict[str, Any] = {
            "enabled": enabled,
            "setting_type": setting_type,
        }
        if price is not None:
            setting["price"] = price
        if value is not None:
            setting["value"] = value
        if interval is not None:
            setting["interval"] = interval
        if period is not None:
            setting["period"] = period
        if fast_period is not None:
            setting["fast_period"] = fast_period
        if slow_period is not None:
            setting["slow_period"] = slow_period
        if signal_period is not None:
            setting["signal_period"] = signal_period
        if std_dev is not None:
            setting["std_dev"] = std_dev
        if ma_type is not None:
            setting["ma_type"] = ma_type

        data = await self._transport.post(
            ep.notification_settings(instrument_id),
            json={"settings": [setting]},
            params=_DEFAULT_PARAMS,
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
        data = await self._transport.post(
            ep.notification_settings(instrument_id),
            json={"settings": settings},
            params=_DEFAULT_PARAMS,
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
        value: str | int | None = None,
        interval: str | None = None,
        period: int | None = None,
    ) -> AlertSettings:
        """Update an existing alert for an instrument.

        Args:
            instrument_id: Instrument UUID.
            alert_id: Alert UUID to update.
            setting_type: Alert type (must match existing alert).
            enabled: Enable or disable the alert.
            price: New target price string.
            value: New threshold value (for RSI/VWAP).
            interval: New candle interval: '5m', '10m', '1h', '1d', '1w'.
            period: New indicator period.
        """
        setting: dict[str, Any] = {
            "id": alert_id,
            "setting_type": setting_type,
        }
        if enabled is not None:
            setting["enabled"] = enabled
        if price is not None:
            setting["price"] = price
        if value is not None:
            setting["value"] = value
        if interval is not None:
            setting["interval"] = interval
        if period is not None:
            setting["period"] = period

        data = await self._transport.patch(
            ep.notification_settings(instrument_id),
            json={"settings": [setting]},
            params=_DEFAULT_PARAMS,
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
        data = await self._transport.patch(
            ep.notification_settings(instrument_id),
            json={"settings": settings},
            params=_DEFAULT_PARAMS,
        )
        return AlertSettings(**data)

    # ── Delete ───────────────────────────────────────────────────────────

    async def delete_alert(
        self,
        instrument_id: str,
        alert_id: str,
        setting_type: str,
    ) -> AlertSettings:
        """Delete an alert by ID.

        Args:
            instrument_id: Instrument UUID.
            alert_id: Alert UUID to delete.
            setting_type: Alert type (must match the alert being deleted).
        """
        setting: dict[str, Any] = {
            "id": alert_id,
            "setting_type": setting_type,
        }
        data = await self._transport.delete(
            ep.notification_settings(instrument_id),
            json={"settings": [setting]},
            params=_DEFAULT_PARAMS,
        )
        return AlertSettings(**data)

    async def delete_alerts(
        self, instrument_id: str, settings: list[dict[str, Any]]
    ) -> AlertSettings:
        """Delete multiple alerts in one request.

        Args:
            instrument_id: Instrument UUID.
            settings: List of dicts with 'id' and 'setting_type' for each
                alert to delete.
        """
        data = await self._transport.delete(
            ep.notification_settings(instrument_id),
            json={"settings": settings},
            params=_DEFAULT_PARAMS,
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
        interval: str = "1d",
        period: int = 14,
        value: str | int = 70,
    ) -> AlertSettings:
        """Create an alert that triggers when RSI crosses above threshold.

        Args:
            instrument_id: Instrument UUID.
            interval: '5m', '10m', '1h', '1d', '1w'.
            period: RSI look-back periods (default 14).
            value: RSI threshold (default 70).
        """
        return await self.create_alert(
            instrument_id,
            "rsi_above",
            interval=interval,
            period=period,
            value=value,
        )

    async def create_rsi_below_alert(
        self,
        instrument_id: str,
        interval: str = "1d",
        period: int = 14,
        value: str | int = 30,
    ) -> AlertSettings:
        """Create an alert that triggers when RSI crosses below threshold.

        Args:
            instrument_id: Instrument UUID.
            interval: '5m', '10m', '1h', '1d', '1w'.
            period: RSI look-back periods (default 14).
            value: RSI threshold (default 30).
        """
        return await self.create_alert(
            instrument_id,
            "rsi_below",
            interval=interval,
            period=period,
            value=value,
        )

    # ── Convenience: Moving average alerts ───────────────────────────────

    async def create_sma_cross_alert(
        self,
        instrument_id: str,
        direction: str = "above",
        interval: str = "1d",
        period: int = 20,
    ) -> AlertSettings:
        """Create an alert when price crosses a Simple Moving Average.

        Args:
            instrument_id: Instrument UUID.
            direction: 'above' or 'below'.
            interval: '5m', '10m', '1h', '1d', '1w'.
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
        interval: str = "1d",
        period: int = 20,
    ) -> AlertSettings:
        """Create an alert when price crosses an Exponential Moving Average.

        Args:
            instrument_id: Instrument UUID.
            direction: 'above' or 'below'.
            interval: '5m', '10m', '1h', '1d', '1w'.
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
        interval: str = "5m",
    ) -> AlertSettings:
        """Create an alert when price crosses the Volume-Weighted Average Price.

        Args:
            instrument_id: Instrument UUID.
            direction: 'above' or 'below'.
            interval: '5m', '10m', '1h', '1d', '1w'.
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
        interval: str = "1d",
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> AlertSettings:
        """Create an alert when MACD crosses the signal line.

        Args:
            instrument_id: Instrument UUID.
            direction: 'above' (bullish crossover) or 'below' (bearish crossover).
            interval: '5m', '10m', '1h', '1d', '1w'.
            fast_period: Fast EMA period (default 12).
            slow_period: Slow EMA period (default 26).
            signal_period: Signal line period (default 9).
        """
        setting_type = f"macd_{direction}_signal"
        return await self.create_alert(
            instrument_id,
            setting_type,
            interval=interval,
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
        )

    # ── Convenience: Bollinger Band alerts ───────────────────────────────

    async def create_bollinger_alert(
        self,
        instrument_id: str,
        direction: str = "above",
        interval: str = "1d",
        period: int = 20,
        std_dev: str = "2.0",
        ma_type: str = "sma",
    ) -> AlertSettings:
        """Create an alert when price crosses a Bollinger Band.

        Args:
            instrument_id: Instrument UUID.
            direction: 'above' (upper band) or 'below' (lower band).
            interval: '5m', '10m', '1h', '1d', '1w'.
            period: Bollinger Band look-back periods (default 20).
            std_dev: Standard deviations from MA (default "2.0").
            ma_type: Moving average type (default "sma").
        """
        band = "upper" if direction == "above" else "lower"
        setting_type = f"price_{direction}_boll_{band}"
        return await self.create_alert(
            instrument_id,
            setting_type,
            interval=interval,
            period=period,
            std_dev=std_dev,
            ma_type=ma_type,
        )

