"""Pydantic models for screener-related API responses."""

from __future__ import annotations

from pydantic import BaseModel


class ScreenerFilter(BaseModel):
    """Individual filter within a screener configuration."""

    key: str
    filter: dict = {}
    is_hidden: bool = False


class Screener(BaseModel):
    """Saved or preset screener configuration."""

    id: str | None = None
    display_name: str = ""
    filters: list[ScreenerFilter] = []
    columns: list[str] = []
    sort_by: str | None = None
    sort_direction: str | None = None


class IndicatorOption(BaseModel):
    """Selectable option within a filter indicator."""

    id: str = ""
    title: str = ""
    subtitle: str | None = None
    secondary_filter: dict | None = None
    column_key: str | None = None
    # Legacy fields
    label: str = ""
    value: str = ""


class IndicatorFilterParameters(BaseModel):
    """Describes the filter type and available options for an indicator."""

    type: str = ""
    options: list[IndicatorOption] = []


class Indicator(BaseModel):
    """Filter indicator from the full catalog."""

    key: str = ""
    title: str = ""
    description: str | dict | None = None
    filter_parameters: IndicatorFilterParameters | None = None


class IndicatorCategory(BaseModel):
    """Category group containing related indicators."""

    title: str = ""
    indicators: list[Indicator] = []


class ScanResult(BaseModel):
    """Single stock match from a screener scan."""

    instrument_id: str = ""
    symbol: str = ""
    name: str = ""
    values: list[str] = []


class ScanColumn(BaseModel):
    """Column descriptor in a scan response."""

    id: str = ""
    alignment: str | None = None
    screend_indicator_id: str | None = None


class ScanResponse(BaseModel):
    """Response from a screener scan execution."""

    results: list[ScanResult] = []
    subtitle: str = ""
    columns: list[ScanColumn] = []
    sort_by: str | None = None
    sort_direction: str | None = None
