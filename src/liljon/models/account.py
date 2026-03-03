"""Pydantic models for account-related API responses."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class AccountProfile(BaseModel):
    """Top-level account profile information."""

    url: str | None = None
    account_number: str | None = None
    type: str | None = None
    state: str | None = None
    buying_power: Decimal | None = None
    cash: Decimal | None = None
    cash_held_for_orders: Decimal | None = None
    uncleared_deposits: Decimal | None = None
    sma: Decimal | None = None
    sma_held_for_orders: Decimal | None = None
    margin_balances: dict | None = None
    user_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PortfolioProfile(BaseModel):
    """Portfolio-level balances and P&L."""

    url: str | None = None
    account_url: str | None = None
    account: str | None = None
    equity: Decimal | None = None
    extended_hours_equity: Decimal | None = None
    market_value: Decimal | None = None
    extended_hours_market_value: Decimal | None = None
    extended_hours_portfolio_equity: Decimal | None = None
    last_core_equity: Decimal | None = None
    last_core_market_value: Decimal | None = None
    last_core_portfolio_equity: Decimal | None = None
    equity_previous_close: Decimal | None = None
    portfolio_equity_previous_close: Decimal | None = None
    adjusted_equity_previous_close: Decimal | None = None
    adjusted_portfolio_equity_previous_close: Decimal | None = None
    withdrawable_amount: Decimal | None = None
    unwithdrawable_deposits: Decimal | None = None
    unwithdrawable_grants: Decimal | None = None
    excess_margin: Decimal | None = None
    excess_maintenance: Decimal | None = None
    excess_margin_with_uncleared_deposits: Decimal | None = None
    display_currency: str | None = None
    start_date: str | None = None


class Position(BaseModel):
    """A stock position in the user's account."""

    url: str | None = None
    instrument_url: str | None = None
    instrument_id: str | None = None
    account_url: str | None = None
    account_number: str | None = None
    symbol: str | None = None
    quantity: Decimal | None = None
    average_buy_price: Decimal | None = None
    pending_average_buy_price: Decimal | None = None
    shares_held_for_buys: Decimal | None = None
    shares_held_for_sells: Decimal | None = None
    shares_held_for_stock_grants: Decimal | None = None
    shares_pending_from_options_events: Decimal | None = None
    intraday_quantity: Decimal | None = None
    intraday_average_buy_price: Decimal | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PhoenixAccount(BaseModel):
    """Unified account snapshot from the Phoenix endpoint."""

    account_buying_power: dict | None = None
    cash_balances: dict | None = None
    equity: Decimal | None = None
    extended_hours_equity: Decimal | None = None
    previous_close: Decimal | None = None
    total_return: dict | None = None
    uninvested_cash: dict | None = None


class WatchlistItem(BaseModel):
    """A single item in a watchlist."""

    id: str | None = None
    list_id: str | None = None
    object_id: str | None = None
    object_type: str | None = None
    symbol: str | None = None
    name: str | None = None
    price: Decimal | None = None
    previous_close: Decimal | None = None
    one_day_percent_change: float | None = None
    created_at: datetime | None = None


class Watchlist(BaseModel):
    """A named watchlist."""

    id: str | None = None
    url: str | None = None
    name: str | None = None
    display_name: str | None = None
    items: list[WatchlistItem] = []


class Dividend(BaseModel):
    """A dividend payment record."""

    id: str | None = None
    url: str | None = None
    instrument_url: str | None = None
    account: str | None = None
    amount: Decimal | None = None
    rate: Decimal | None = None
    position: Decimal | None = None
    state: str | None = None
    payable_date: str | None = None
    record_date: str | None = None
    paid_at: datetime | None = None
    withholding: Decimal | None = None


class UserProfile(BaseModel):
    """Current user profile."""

    url: str | None = None
    id: str | None = None
    username: str | None = None
    email: str | None = None
    email_verified: bool | None = None
    first_name: str | None = None
    last_name: str | None = None
    profile_name: str | None = None
    created_at: datetime | None = None
    origin: dict | None = None


class Subscription(BaseModel):
    """Active subscription (Gold, etc.)."""

    id: str | None = None
    plan_id: str | None = None
    plan: dict | None = None
    status: str | None = None
    created_at: datetime | None = None
    expires_at: datetime | None = None


class LivePortfolio(BaseModel):
    """Live portfolio data with real-time values from bonfire."""

    deposit_adjusted_market_value: Decimal | None = None
    equity_market_value: Decimal | None = None
    forex_market_value: Decimal | None = None
    futures_market_value: Decimal | None = None
    futures_cash: Decimal | None = None
    event_contracts_market_value: Decimal | None = None
    option_market_value: Decimal | None = None
    cash: Decimal | None = None
    brokerage_cash: Decimal | None = None
    pending_deposits: Decimal | None = None
    early_access_amount: Decimal | None = None
    last_core_portfolio_equity: Decimal | None = None
    margin_used: Decimal | None = None
    account_number: str | None = None
    currency: str | None = None


class SweepInterest(BaseModel):
    """Cash sweep interest rate info."""

    interest_rate: Decimal | None = None
    non_gold_interest_rate: Decimal | None = None
    gold_interest_rate: Decimal | None = None
    gold_boosted_rate: Decimal | None = None
    gold_boosted_high_rate: Decimal | None = None
    ram_interest_rate: Decimal | None = None
