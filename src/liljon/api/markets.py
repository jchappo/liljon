"""MarketsAPI: hours, movers, categories."""

from __future__ import annotations

from typing import Any

from liljon import _endpoints as ep
from liljon._http import HttpTransport


class MarketsAPI:
    """Market data: hours, movers, and categories."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    async def get_markets(self) -> list[dict[str, Any]]:
        """Fetch all available markets."""
        data = await self._transport.get(ep.markets())
        return data.get("results", [])

    async def get_market_hours(self, market_code: str, date: str) -> dict[str, Any]:
        """Fetch market hours for a specific market and date.

        Args:
            market_code: Market code (e.g. 'XNYS', 'XNAS').
            date: Date string in YYYY-MM-DD format.
        """
        return await self._transport.get(ep.market_hours(market_code, date))

    async def get_movers(self, direction: str = "up") -> list[dict[str, Any]]:
        """Fetch S&P 500 movers.

        Args:
            direction: 'up' or 'down'.
        """
        data = await self._transport.get(ep.movers(direction))
        return data.get("results", [])

    async def get_categories(self) -> list[dict[str, Any]]:
        """Fetch discovery categories (tags)."""
        data = await self._transport.get(ep.categories())
        return data.get("results", [])

    async def get_category_instruments(self, tag: str) -> list[dict[str, Any]]:
        """Fetch instruments in a discovery category."""
        data = await self._transport.get(ep.category_instruments(tag))
        return data.get("results", [])
