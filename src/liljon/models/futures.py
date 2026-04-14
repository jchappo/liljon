"""Pydantic models for futures-related API responses."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

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


class FuturesOrderLeg(BaseModel):
    """A single leg within a futures order."""

    model_config = ConfigDict(populate_by_name=True)

    id: str | None = None
    leg_id: str | None = Field(default=None, validation_alias=AliasChoices("leg_id", "legId"))
    contract_type: str | None = Field(
        default=None, validation_alias=AliasChoices("contract_type", "contractType")
    )
    contract_id: str | None = Field(
        default=None, validation_alias=AliasChoices("contract_id", "contractId")
    )
    ratio_quantity: int | None = Field(
        default=None, validation_alias=AliasChoices("ratio_quantity", "ratioQuantity")
    )
    order_side: str | None = Field(
        default=None, validation_alias=AliasChoices("order_side", "orderSide")
    )
    average_price: str | None = Field(
        default=None, validation_alias=AliasChoices("average_price", "averagePrice")
    )


class FuturesOrder(BaseModel):
    """A futures order (placed or historical).

    Robinhood's ``/ceres/v1/orders/`` endpoint returns camelCase keys
    (``orderId``, ``orderState``, ``limitPrice``, ``orderLegs``, etc.).
    The aliases below let both camelCase and snake_case shapes parse
    into the same model.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("id", "orderId"),
    )
    account_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("account_id", "accountId", "account_url"),
    )
    contract_id: str | None = None
    symbol: str | None = None
    side: str | None = None
    order_type: str | None = Field(
        default=None,
        validation_alias=AliasChoices("order_type", "orderType"),
    )
    quantity: Decimal | None = None
    price: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("price", "limitPrice"),
    )
    stop_price: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("stop_price", "stopPrice"),
    )
    time_in_force: str | None = Field(
        default=None,
        validation_alias=AliasChoices("time_in_force", "timeInForce"),
    )
    state: str | None = Field(
        default=None,
        validation_alias=AliasChoices("state", "derivedState", "orderState"),
    )
    filled_quantity: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("filled_quantity", "filledQuantity"),
    )
    average_price: Decimal | None = None
    created_at: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices("created_at", "createdAt"),
    )
    updated_at: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices("updated_at", "updatedAt"),
    )
    closing_strategy: str | None = Field(
        default=None,
        validation_alias=AliasChoices("closing_strategy", "closingStrategy"),
    )
    order_legs: list[FuturesOrderLeg] | None = Field(
        default=None,
        validation_alias=AliasChoices("order_legs", "orderLegs"),
    )

    @model_validator(mode="before")
    @classmethod
    def _extract_from_legs(cls, data: Any) -> Any:
        """Extract side and contract_id from the first order leg."""
        if not isinstance(data, dict):
            return data
        legs = data.get("orderLegs") or data.get("order_legs") or []
        if legs and isinstance(legs, list):
            first = legs[0] if isinstance(legs[0], dict) else {}
            if not data.get("side"):
                data["side"] = first.get("orderSide") or first.get("order_side")
            if not data.get("contract_id") and not data.get("contractId"):
                data["contract_id"] = first.get("contractId") or first.get("contract_id")
        return data


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
