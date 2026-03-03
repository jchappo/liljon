"""AlertsAPI: price alerts and indicator alerts for instruments."""

from __future__ import annotations

from typing import Any

from liljon import _endpoints as ep
from liljon._http import HttpTransport
from liljon.models.alerts import AlertSettings


class AlertsAPI:
    """Custom price and indicator alerts for instruments."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    async def get_alerts(self, instrument_id: str) -> AlertSettings:
        """Get all alert settings for an instrument."""
        params = {"allow_multiple": "true", "sort_by": "created_at"}
        data = await self._transport.get(
            ep.notification_settings(instrument_id), params=params
        )
        return AlertSettings(**data)

    async def create_alert(
        self, instrument_id: str, settings: list[dict[str, Any]]
    ) -> AlertSettings:
        """Create one or more alerts for an instrument.

        Args:
            instrument_id: Instrument UUID.
            settings: List of alert setting dicts, e.g.
                [{"enabled": True, "price": "100.00", "setting_type": "price_above"}]
        """
        params = {"allow_multiple": "true", "sort_by": "created_at"}
        data = await self._transport.post(
            ep.notification_settings(instrument_id),
            json={"settings": settings},
            params=params,
        )
        return AlertSettings(**data)

    async def update_alert(
        self, instrument_id: str, settings: list[dict[str, Any]]
    ) -> AlertSettings:
        """Update existing alerts for an instrument.

        Args:
            instrument_id: Instrument UUID.
            settings: List of alert setting dicts with id and updated fields, e.g.
                [{"id": "...", "setting_type": "price_above", "enabled": False}]
        """
        params = {"allow_multiple": "true", "sort_by": "created_at"}
        data = await self._transport.patch(
            ep.notification_settings(instrument_id),
            json={"settings": settings},
            params=params,
        )
        return AlertSettings(**data)
