"""Pydantic models for futures-related API responses."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

# ── Arsenal endpoints (camelCase) ─────────────────────────────────────────────


class FuturesContract(BaseModel):
    """A futures contract instrument (from /arsenal/v1/futures/contracts)."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    product_id: str = Field(alias="productId")
    symbol: str
    display_symbol: str = Field(alias="displaySymbol")
    description: str
    multiplier: str
    expiration_mmy: str = Field(alias="expirationMmy")
    expiration: str
    customer_last_close_date: str = Field(alias="customerLastCloseDate")
    tradability: str
    state: str
    first_trade_date: str = Field(alias="firstTradeDate")
    settlement_date: str = Field(alias="settlementDate")
    settlement_start_time: str | None = Field(default=None, alias="settlementStartTime")


class FuturesProduct(BaseModel):
    """Futures product metadata (from /arsenal/v1/futures/products)."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    combined_commodity_id: str = Field(alias="combinedCommodityId")
    symbol: str
    display_symbol: str = Field(alias="displaySymbol")
    description: str
    country: str
    exchange: str
    currency: str
    future_sub_type: str = Field(alias="futureSubType")
    underlying_asset: str = Field(alias="underlyingAsset")
    delivery: str
    is_standardized: bool = Field(alias="isStandardized")
    price_increments: str = Field(alias="priceIncrements")
    active_futures_contract_id: str = Field(alias="activeFuturesContractId")
    long_description: str = Field(alias="longDescription")
    simple_name: str = Field(alias="simpleName")
    trading_hours_info: dict | None = Field(default=None, alias="tradingHoursInfo")
    settlement_start_time: str | None = Field(default=None, alias="settlementStartTime")
    search_rank: int | None = Field(default=None, alias="searchRank")
    rhd_product_group: str | None = Field(default=None, alias="rhdProductGroup")


class FuturesMarginRequirement(BaseModel):
    """Margin requirement for a futures contract."""

    model_config = ConfigDict(populate_by_name=True)

    margin_requirement: Decimal = Field(alias="marginRequirement")
    currency: str


class FuturesSessionDetail(BaseModel):
    """A single trading session within a day."""

    model_config = ConfigDict(populate_by_name=True)

    trading_date: str = Field(alias="tradingDate")
    is_trading: bool = Field(alias="isTrading")
    start_time: str = Field(alias="startTime")
    end_time: str = Field(alias="endTime")
    session_type: str = Field(alias="sessionType")


class FuturesTradingSession(BaseModel):
    """Trading session schedule for a contract on a given date."""

    model_config = ConfigDict(populate_by_name=True)

    date: str
    futures_contract_id: str = Field(alias="futuresContractId")
    is_holiday: bool = Field(alias="isHoliday")
    start_time: str = Field(alias="startTime")
    end_time: str = Field(alias="endTime")
    sessions: list[FuturesSessionDetail]
    current_session: FuturesSessionDetail | None = Field(default=None, alias="currentSession")
    previous_session: FuturesSessionDetail | None = Field(default=None, alias="previousSession")
    next_session: FuturesSessionDetail | None = Field(default=None, alias="nextSession")


# ── Marketdata endpoints (snake_case) ─────────────────────────────────────────


class FuturesQuote(BaseModel):
    """Real-time quote for a futures contract."""

    instrument_id: str | None = None
    symbol: str | None = None
    ask_price: Decimal | None = None
    ask_size: int | None = None
    ask_venue_timestamp: str | None = None
    bid_price: Decimal | None = None
    bid_size: int | None = None
    bid_venue_timestamp: str | None = None
    last_trade_price: Decimal | None = None
    last_trade_size: int | None = None
    last_trade_venue_timestamp: str | None = None
    state: str | None = None
    updated_at: str | None = None
    out_of_band: bool | None = None


class FuturesClose(BaseModel):
    """Previous close data for a futures contract."""

    instrument_id: str | None = None
    symbol: str | None = None
    previous_close_date: str | None = None
    previous_close_price: Decimal | None = None
    previous_close_price_type: str | None = None
    previous_close_source: str | None = None
    previous_close_price_last_updated_at: str | None = None
    close_date: str | None = None
    close_price: Decimal | None = None
    close_price_type: str | None = None
    close_source: str | None = None
    close_price_last_updated_at: str | None = None


class FuturesCloseRange(BaseModel):
    """A daily close entry within a historical range."""

    instrument_id: str | None = None
    symbol: str | None = None
    close_date: str | None = None
    close_price: Decimal | None = None
    close_price_type: str | None = None
    close_source: str | None = None
    close_price_last_updated_at: str | None = None
    interpolated: bool | None = None
    session_start_time: str | None = None
    session_end_time: str | None = None


class FuturesHistoricalBar(BaseModel):
    """OHLCV candle for a futures contract."""

    begins_at: str | None = None
    open_price: Decimal | None = None
    close_price: Decimal | None = None
    high_price: Decimal | None = None
    low_price: Decimal | None = None
    volume: int | None = None
    interpolated: bool | None = None
    is_market_open: bool | None = None
    contract_id: str | None = None


class FuturesFundamentals(BaseModel):
    """Session fundamentals for a futures contract."""

    instrument_id: str | None = None
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    volume: str | None = None
    previous_close_price: Decimal | None = None


class FuturesBuyingPower(BaseModel):
    """Futures buying power and margin info."""

    buying_power: Decimal | None = None
    futures_buying_power: Decimal | None = None
    futures_equity: Decimal | None = None
    futures_margin_requirement: Decimal | None = None
    swaps_buying_power: Decimal | None = None
    swaps_trade_balance: Decimal | None = None
    swaps_margin_requirement: Decimal | None = None
    swaps_market_value: Decimal | None = None


# ── Orders / Account (existing, unchanged) ───────────────────────────────────


class FuturesOrder(BaseModel):
    """A futures order (placed or historical).

    Robinhood's ``/ceres/v1/orders/`` endpoint returns at least two
    payload shapes: the canonical snake_case form (``id``, ``state``,
    ``order_type``, ...) and a camelCase variant seen on some records
    (notably REJECTED orders) that uses ``orderId`` and ``derivedState``.
    The aliases below let both shapes parse into the same model so a
    single odd-shaped order doesn't crash ``get_orders()``.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("id", "orderId"),
    )
    account_url: str | None = None
    contract_id: str | None = None
    symbol: str | None = None
    side: str | None = None
    order_type: str | None = None
    quantity: Decimal | None = None
    price: Decimal | None = None
    stop_price: Decimal | None = None
    time_in_force: str | None = None
    state: str | None = Field(
        default=None,
        validation_alias=AliasChoices("state", "derivedState"),
    )
    filled_quantity: Decimal | None = None
    average_price: Decimal | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    closing_strategy: str | None = None


class FuturesAccount(BaseModel):
    """The user's futures account summary."""

    id: str | None = None
    account_number: str | None = None
    equity: Decimal | None = None
    buying_power: Decimal | None = None
    cash: Decimal | None = None
    margin_used: Decimal | None = None
    unrealized_pnl: Decimal | None = None
    realized_pnl: Decimal | None = None
