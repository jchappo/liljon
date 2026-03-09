"""Pydantic models for order-related API responses."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class Notional(BaseModel):
    """Monetary amount with currency info, used for total/executed notional."""

    amount: Decimal | None = None
    currency_code: str | None = None
    currency_id: str | None = None


class Execution(BaseModel):
    """A single fill/execution within an order."""

    id: str | None = None
    price: Decimal | None = None
    quantity: Decimal | None = None
    rounded_notional: Decimal | None = None
    settlement_date: str | None = None
    timestamp: datetime | None = None
    ipo_access_execution_rank: int | None = None


class OrderResult(BaseModel):
    """Unified order result for stock orders."""

    id: str
    ref_id: str | None = None
    url: str | None = None
    account: str | None = None
    user_uuid: str | None = None
    position: str | None = None
    cancel: str | None = None
    instrument: str | None = None
    instrument_id: str | None = None
    symbol: str | None = None

    # Core order fields
    side: str | None = None
    type: str | None = None
    time_in_force: str | None = None
    trigger: str | None = None
    price: Decimal | None = None
    stop_price: Decimal | None = None
    quantity: Decimal | None = None
    cumulative_quantity: Decimal | None = None
    average_price: Decimal | None = None

    # Fees
    fees: Decimal | None = None
    sec_fees: Decimal | None = None
    taf_fees: Decimal | None = None
    cat_fees: Decimal | None = None
    sales_taxes: list[dict] = []

    # State
    state: str | None = None
    derived_state: str | None = None
    reject_reason: str | None = None
    pending_cancel_open_agent: str | None = None
    user_cancel_request_state: str | None = None

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_transaction_at: datetime | None = None
    stop_triggered_at: datetime | None = None

    # Executions
    executions: list[Execution] = []

    # Market hours
    extended_hours: bool | None = None
    market_hours: str | None = None

    # Trailing stop
    last_trail_price: Decimal | None = None
    last_trail_price_updated_at: datetime | None = None
    last_trail_price_source: str | None = None

    # Notional amounts
    dollar_based_amount: Decimal | None = None
    total_notional: Notional | None = None
    executed_notional: Notional | None = None
    requested_notional_amount: Decimal | None = None

    # Override flags
    override_dtbp_checks: bool | None = None
    override_day_trade_checks: bool | None = None

    # Order metadata
    order_form_version: int | None = None
    order_form_type: str | None = None
    position_effect: str | None = None
    placed_agent: str | None = None
    is_editable: bool | None = None
    is_visible_to_user: bool | None = None
    is_primary_account: bool | None = None
    preset_percent_limit: Decimal | None = None
    last_update_version: int | None = None
    replaces: str | None = None
    tax_lot_selection_type: str | None = None
    root_advanced_order_id: str | None = None
    investment_schedule_id: str | None = None

    # IPO access fields
    is_ipo_access_order: bool | None = None
    is_ipo_access_price_finalized: bool | None = None
    has_ipo_access_custom_price_limit: bool | None = None
    ipo_access_cancellation_reason: str | None = None
    ipo_access_lower_collared_price: Decimal | None = None
    ipo_access_upper_collared_price: Decimal | None = None
    ipo_access_upper_price: Decimal | None = None
    ipo_access_lower_price: Decimal | None = None

    response_category: str | None = None


class OrderFeeEstimate(BaseModel):
    """Individual fee line item from the fee calculation endpoint."""

    name: str | None = None
    rate: Decimal | None = None
    amount: Decimal | None = None


class OrderFeeResult(BaseModel):
    """Response from the order fee calculation endpoint."""

    instrument_id: str | None = None
    quantity: Decimal | None = None
    price: Decimal | None = None
    side: str | None = None
    fees: list[OrderFeeEstimate] = []
    total_fee: Decimal | None = None
    sales_taxes: list[dict] = []


class OrderSession(BaseModel):
    """Trading session behavior for a time window."""

    start_time: datetime | None = None
    end_time: datetime | None = None
    behavior: int | None = None


class OrderSessionInfo(BaseModel):
    """Trading session info with time-based behaviors."""

    session: str | None = None
    behaviors: list[OrderSession] = []
