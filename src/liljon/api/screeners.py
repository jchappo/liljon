"""ScreenersAPI: saved screeners, presets, indicators, and scan execution."""

from __future__ import annotations

from typing import Any

from liljon import _endpoints as ep
from liljon._http import HttpTransport
from liljon.models.screeners import (
    IndicatorCategory,
    ScanColumn,
    ScanResponse,
    ScanResult,
    Screener,
)


class ScreenersAPI:
    """Screener data: saved screeners, presets, indicators catalog, and scan."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    async def get_screeners(self, include_filters: bool = True) -> list[Screener]:
        """Fetch the user's saved screeners.

        Args:
            include_filters: Whether to include filter details in the response.
        """
        data = await self._transport.get(ep.screeners(include_filters))
        results = data.get("results", [])
        return [Screener(**r) for r in results if r is not None]

    async def get_presets(self) -> list[Screener]:
        """Fetch preset screener configurations."""
        data = await self._transport.get(ep.screener_presets())
        results = data.get("results", [])
        return [Screener(**r) for r in results if r is not None]

    async def get_screener(self, screener_id: str) -> Screener:
        """Fetch a single screener by ID."""
        data = await self._transport.get(ep.screener(screener_id))
        return Screener(**data)

    async def get_indicators(self) -> list[IndicatorCategory]:
        """Fetch the full catalog of available screener filter indicators."""
        data = await self._transport.get(ep.screener_indicators())
        results = data.get("results", [])
        return [IndicatorCategory(**r) for r in results if r is not None]

    async def scan(
        self,
        indicators: list[dict[str, Any]],
        columns: list[str] | None = None,
        sort_by: str | None = None,
        sort_direction: str = "DESC",
    ) -> ScanResponse:
        """Execute a screener scan query.

        Args:
            indicators: List of indicator filter dicts (key + filter config).
            columns: Column keys to include in results. Defaults to price and percentage change.
            sort_by: Column key to sort results by.
            sort_direction: Sort direction, 'ASC' or 'DESC'.
        """
        if columns is None:
            columns = ["last_price", "percent_change"]

        payload: dict[str, Any] = {"indicators": indicators, "columns": columns}
        if sort_by is not None:
            payload["sort_by"] = sort_by
        payload["sort_direction"] = sort_direction

        data = await self._transport.post(ep.screener_scan(), json=payload)

        raw_cols = data.get("columns", [])
        scan_columns = [ScanColumn(**c) if isinstance(c, dict) else ScanColumn(id=c) for c in raw_cols]

        results: list[ScanResult] = []
        for row in data.get("rows", []):
            symbol = row.get("instrument_symbol", "")
            instrument_id = row.get("instrument_id", "")
            if not symbol:
                continue
            name = ""
            values: list[str] = []
            for item in row.get("items", []):
                comp = item.get("component", {})
                comp_type = comp.get("sdui_component_type", "")
                if comp_type == "TABLE_INSTRUMENT_NAME":
                    name = comp.get("name", "")
                elif comp_type == "TEXT":
                    text_obj = comp.get("text", {})
                    values.append(text_obj.get("text", ""))
            results.append(ScanResult(
                instrument_id=instrument_id,
                symbol=symbol,
                name=name,
                values=values,
            ))

        return ScanResponse(
            results=results,
            subtitle=data.get("subtitle", ""),
            columns=scan_columns,
            sort_by=data.get("sort_by"),
            sort_direction=data.get("sort_direction"),
        )
