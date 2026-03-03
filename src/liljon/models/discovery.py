"""Pydantic models for discovery, analyst, hedge fund, and insider data."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class AnalystRating(BaseModel):
    """Analyst rating for an instrument from midlands/ratings."""

    summary: dict | None = None
    ratings: list[dict] = []
    instrument_id: str | None = None
    ratings_published_at: str | None = None


class HedgeFundQuarterlyTransaction(BaseModel):
    """Quarterly aggregate hedge fund transaction."""

    date: str | None = None
    total_shares_held: int | None = None
    shares_bought: int | None = None
    shares_sold: int | None = None


class HedgeFundSummary(BaseModel):
    """Hedge fund activity summary for an instrument."""

    instrument_id: str | None = None
    sentiment_score: str | None = None
    quarterly_aggregate_transactions: list[HedgeFundQuarterlyTransaction] = []


class HedgeFundTransaction(BaseModel):
    """Individual hedge fund transaction detail."""

    manager_name: str | None = None
    institution_name: str | None = None
    portfolio_percentage: float | None = None
    change_percentage: float | None = None
    action: str | None = None
    market_value: int | None = None
    total_shares: int | None = None
    shares_traded: int | None = None


class HedgeFundTransactions(BaseModel):
    """Detailed hedge fund transactions for an instrument."""

    instrument_id: str | None = None
    detailed_transactions: list[HedgeFundTransaction] = []


class InsiderMonthlyTransaction(BaseModel):
    """Monthly aggregate insider transaction."""

    date: str | None = None
    shares_bought: int | None = None
    shares_sold: int | None = None
    buy_transactions: int | None = None
    sell_transactions: int | None = None


class InsiderSummary(BaseModel):
    """Insider trading summary for an instrument."""

    instrument_id: str | None = None
    sentiment_score: str | None = None
    monthly_aggregate_transactions: list[InsiderMonthlyTransaction] = []


class InsiderTransaction(BaseModel):
    """Individual insider transaction detail."""

    name: str | None = None
    position: str | None = None
    description: str | None = None
    transaction_type: str | None = None
    amount: float | None = None
    number_of_shares: int | None = None
    date: str | None = None


class InsiderTransactions(BaseModel):
    """Detailed insider transactions for an instrument."""

    instrument_id: str | None = None
    detailed_transactions: list[InsiderTransaction] = []


class ShortInterest(BaseModel):
    """Short interest and borrowing data for an instrument."""

    instrument: str | None = None
    instrument_id: str | None = None
    fee: Decimal | None = None
    fee_timestamp: datetime | None = None
    inventory_range: str | None = None
    inventory_timestamp: datetime | None = None
    daily_fee: Decimal | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class EquitySummaryDailyTransaction(BaseModel):
    """Daily net buy/sell transaction flow."""

    date: str | None = None
    net_buy_percentage: float | None = None
    net_sell_percentage: float | None = None
    buy_volume_percentage_change: float | None = None
    sell_volume_percentage_change: float | None = None


class EquitySummary(BaseModel):
    """Equity summary — Robinhood user transaction flow for an instrument."""

    instrument_id: str | None = None
    daily_transactions: list[EquitySummaryDailyTransaction] = []


class Earnings(BaseModel):
    """Earnings data for an instrument."""

    results: list[dict] = []


class SimilarInstrument(BaseModel):
    """A similar instrument recommendation."""

    symbol: str | None = None
    instrument_id: str | None = None
    name: str | None = None
    simple_name: str | None = None
    logo_url: str | None = None
    tags: list[dict] = []


class SimilarInstruments(BaseModel):
    """Similar instruments for a given instrument ID."""

    id: str | None = None
    similar: list[SimilarInstrument] = []


class MarketIndex(BaseModel):
    """A single market index value (S&P 500, Nasdaq, etc.)."""

    key: str
    name: str | None = None
    value: Decimal | None = None
    previous_close: Decimal | None = None
    percent_change: Decimal | None = None


class ChartBounds(BaseModel):
    """Chart time bounds based on market hours."""

    first_timestamp: str | None = None
    last_timestamp: str | None = None
    extended_open_timestamp: str | None = None
    extended_close_timestamp: str | None = None
    next_refresh: str | None = None
    utc_offset: int | None = None
    previous_close_date: str | None = None


class EtpDetails(BaseModel):
    """ETP (ETF/ETN) details — AUM, expense ratio, performance."""

    instrument_id: str | None = None
    symbol: str | None = None
    is_inverse: bool | None = None
    is_leveraged: bool | None = None
    aum: Decimal | None = None
    sec_yield: Decimal | None = None
    gross_expense_ratio: Decimal | None = None
    nav: Decimal | None = None
    inception_date: str | None = None
    index_tracked: str | None = None
    category: str | None = None
    total_holdings: int | None = None
    is_actively_managed: bool | None = None
    quarter_end_performance: dict | None = None
    month_end_performance: dict | None = None
    sectors: list[dict] = []
    holdings: list[dict] = []


class NbboSummary(BaseModel):
    """National Best Bid/Offer summary."""

    instrument_id: str | None = None
    bid_price: str | None = None
    ask_price: str | None = None
    nbbo_prices_copy: str | None = None
    nbbo_updated_at_timestamp: datetime | None = None
    bid_price_money: dict | None = None
    ask_price_money: dict | None = None
