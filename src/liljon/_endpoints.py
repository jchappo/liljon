"""Pure URL string templates for the Robinhood API.

Every function returns a URL string. No side effects, no HTTP calls, no state.
Functions that need dynamic IDs take them as parameters.
"""

BASE = "https://api.robinhood.com"
NUMMUS_BASE = "https://nummus.robinhood.com"
BONFIRE_BASE = "https://bonfire.robinhood.com"
DORA_BASE = "https://dora.robinhood.com"

# ── Authentication ──────────────────────────────────────────────────────────

def login() -> str:
    return f"{BASE}/oauth2/token/"


def logout() -> str:
    return f"{BASE}/oauth2/revoke_token/"


def challenge_respond(challenge_id: str) -> str:
    return f"{BASE}/challenge/{challenge_id}/respond/"


def pathfinder_user_machine() -> str:
    return f"{BASE}/pathfinder/user_machine/"


def pathfinder_inquiry(machine_id: str) -> str:
    return f"{BASE}/pathfinder/inquiries/{machine_id}/user_view/"


# ── Accounts ────────────────────────────────────────────────────────────────

def accounts() -> str:
    return f"{BASE}/accounts/"


def account(account_id: str) -> str:
    return f"{BASE}/accounts/{account_id}/"


def portfolio(account_id: str) -> str:
    return f"{BASE}/accounts/{account_id}/portfolio/"


def phoenix_account() -> str:
    return f"{BASE}/phoenix/accounts/unified/"


def positions() -> str:
    return f"{BASE}/positions/"


def dividends() -> str:
    return f"{BASE}/dividends/"


def watchlists() -> str:
    return f"{BASE}/midlands/lists/default/"


def all_watchlists() -> str:
    return f"{BASE}/midlands/lists/"


def watchlist_items(list_id: str) -> str:
    """Items belonging to a specific watchlist."""
    return f"{BASE}/midlands/lists/items/?list_id={list_id}"


def watchlist_bulk_update() -> str:
    return f"{BASE}/midlands/lists/items/"


def portfolio_by_number(account_number: str) -> str:
    """Portfolio summary by account number."""
    return f"{BASE}/portfolios/{account_number}/"


def user() -> str:
    """Current user profile."""
    return f"{BASE}/user/"


def subscriptions() -> str:
    """Active subscriptions (Gold, etc.)."""
    return f"{BASE}/subscription/subscriptions/"


def stock_loan_payments() -> str:
    """Stock lending income payments."""
    return f"{BASE}/accounts/stock_loan_payments/"


def sweeps_interest() -> str:
    """Cash sweep interest info."""
    return f"{BASE}/accounts/sweeps/interest/"


def historical_activities() -> str:
    """Historical account activities (trades, dividends, transfers)."""
    return f"{BASE}/pluto/historical_activities/"


# ── Stocks ──────────────────────────────────────────────────────────────────

def quotes(
    symbols: str,
    bounds: str = "trading",
    include_bbo_source: bool = True,
    include_inactive: bool = False,
) -> str:
    """Comma-separated symbols → market-data quotes."""
    return (
        f"{BASE}/marketdata/quotes/"
        f"?symbols={symbols}&bounds={bounds}"
        f"&include_bbo_source={str(include_bbo_source).lower()}"
        f"&include_inactive={str(include_inactive).lower()}"
    )


def quotes_by_ids(
    ids: str,
    bounds: str = "trading",
    include_bbo_source: bool = True,
    include_inactive: bool = False,
) -> str:
    """Batch quotes by comma-separated instrument IDs with extended params."""
    return (
        f"{BASE}/marketdata/quotes/"
        f"?ids={ids}&bounds={bounds}"
        f"&include_bbo_source={str(include_bbo_source).lower()}"
        f"&include_inactive={str(include_inactive).lower()}"
    )


def instruments() -> str:
    return f"{BASE}/instruments/"


def instrument(instrument_id: str) -> str:
    return f"{BASE}/instruments/{instrument_id}/"


def fundamentals(symbol: str) -> str:
    return f"{BASE}/fundamentals/{symbol}/"


def historicals(symbol: str, interval: str, span: str, bounds: str = "regular") -> str:
    return f"{BASE}/marketdata/historicals/{symbol}/?interval={interval}&span={span}&bounds={bounds}"


def news(symbol: str | None = None) -> str:
    if symbol:
        return f"{BASE}/midlands/news/{symbol}/"
    return f"{BASE}/midlands/news/"


def fundamentals_by_id(instrument_id: str) -> str:
    """Fundamentals by instrument ID with session-aware bounds support."""
    return f"{BASE}/marketdata/fundamentals/{instrument_id}/"


def fundamentals_short() -> str:
    """Short fundamentals history (52-week daily data)."""
    return f"{BASE}/marketdata/fundamentals/short/v1/"


def earnings() -> str:
    """Earnings data for instruments."""
    return f"{BASE}/marketdata/earnings/"


def equity_summary(instrument_id: str) -> str:
    """Equity summary — daily buy/sell transaction flow."""
    return f"{BASE}/marketdata/equities/summary/robinhood/{instrument_id}/"


def historicals_by_ids() -> str:
    """Batch historicals by instrument IDs."""
    return f"{BASE}/marketdata/historicals/"


def shorting(instrument_id: str) -> str:
    """Short interest and fee data for an instrument."""
    return f"{BASE}/instruments/{instrument_id}/shorting/"


# ── Discovery & Analyst Data ────────────────────────────────────────────────

def ratings_overview(instrument_id: str) -> str:
    """Analyst ratings overview (buy/hold/sell counts, price targets)."""
    return f"{BASE}/discovery/ratings/{instrument_id}/overview/"


def ratings_batch() -> str:
    """Batch analyst ratings by instrument IDs."""
    return f"{BASE}/midlands/ratings/"


def ratings(instrument_id: str) -> str:
    """Analyst ratings for a specific instrument."""
    return f"{BASE}/midlands/ratings/{instrument_id}/"


def hedgefunds_summary(instrument_id: str) -> str:
    """Hedge fund activity summary for an instrument."""
    return f"{BASE}/marketdata/hedgefunds/summary/{instrument_id}/"


def hedgefunds_transactions(instrument_id: str) -> str:
    """Hedge fund buy/sell transactions for an instrument."""
    return f"{BASE}/marketdata/hedgefunds/transactions/{instrument_id}/"


def insiders_summary(instrument_id: str) -> str:
    """Insider trading summary for an instrument."""
    return f"{BASE}/marketdata/insiders/summary/{instrument_id}/"


def insiders_transactions(instrument_id: str) -> str:
    """Individual insider transactions for an instrument."""
    return f"{BASE}/marketdata/insiders/transactions/{instrument_id}/"


def similar_instruments(instrument_id: str) -> str:
    """Similar instruments (from dora.robinhood.com)."""
    return f"{DORA_BASE}/instruments/similar/{instrument_id}/"


def instrument_feed(instrument_id: str) -> str:
    """News/social feed for an instrument (from dora.robinhood.com)."""
    return f"{DORA_BASE}/feed/instrument/{instrument_id}/"


def feed() -> str:
    """General news/social feed (from dora.robinhood.com)."""
    return f"{DORA_BASE}/feed/"


# ── Options ─────────────────────────────────────────────────────────────────

def option_chains(instrument_id: str) -> str:
    return f"{BASE}/options/chains/?equity_instrument_ids={instrument_id}"


def option_chain_by_id(chain_id: str) -> str:
    return f"{BASE}/options/chains/{chain_id}/"


def option_instruments() -> str:
    return f"{BASE}/options/instruments/"


def option_instrument(option_id: str) -> str:
    return f"{BASE}/options/instruments/{option_id}/"


def option_marketdata(option_id: str) -> str:
    return f"{BASE}/marketdata/options/{option_id}/"


def option_positions() -> str:
    return f"{BASE}/options/positions/"


def option_orders() -> str:
    return f"{BASE}/options/orders/"


def option_order(order_id: str) -> str:
    return f"{BASE}/options/orders/{order_id}/"


def option_aggregate_positions() -> str:
    """Aggregated option positions grouped by strategy."""
    return f"{BASE}/options/aggregate_positions/"


def option_strategies() -> str:
    """Option strategy definitions/pricing."""
    return f"{BASE}/options/strategies/"


def option_chain_collateral(chain_id: str) -> str:
    """Collateral requirements for an option chain."""
    return f"{BASE}/options/chains/{chain_id}/collateral/"


def option_events() -> str:
    """Option events (expirations, assignments, exercises)."""
    return f"{BASE}/options/events/"


def option_marketdata_batch() -> str:
    """Batch option market data by IDs."""
    return f"{BASE}/marketdata/options/"


def option_strategy_quotes() -> str:
    """Strategy-level quotes with greeks."""
    return f"{BASE}/marketdata/options/strategy/quotes/"


def option_pnl_chart() -> str:
    """Options profit-and-loss chart data."""
    return f"{BASE}/options/profit_and_loss_chart/"


def option_breakevens() -> str:
    """Breakeven price calculations for option positions."""
    return f"{BASE}/options/breakevens/"


# ── Crypto ──────────────────────────────────────────────────────────────────

def crypto_pairs() -> str:
    return f"{NUMMUS_BASE}/currency_pairs/"


def crypto_pair(pair_id: str) -> str:
    return f"{NUMMUS_BASE}/currency_pairs/{pair_id}/"


def crypto_quotes(pair_id: str) -> str:
    return f"{BASE}/marketdata/forex/quotes/{pair_id}/"


def crypto_holdings() -> str:
    return f"{NUMMUS_BASE}/holdings/"


def crypto_historicals(pair_id: str, interval: str, span: str, bounds: str = "24_7") -> str:
    return f"{BASE}/marketdata/forex/historicals/{pair_id}/?interval={interval}&span={span}&bounds={bounds}"


def crypto_orders() -> str:
    return f"{NUMMUS_BASE}/orders/"


# ── Futures ─────────────────────────────────────────────────────────────────

def futures_contracts() -> str:
    return f"{BASE}/arsenal/v1/futures/contracts/"


def futures_contract(contract_id: str) -> str:
    return f"{BASE}/arsenal/v1/futures/contracts/{contract_id}/"


def futures_quotes() -> str:
    return f"{BASE}/marketdata/futures/quotes/v1/"


def futures_quote(contract_id: str) -> str:
    return f"{BASE}/marketdata/futures/quotes/v1/{contract_id}/"


def futures_accounts() -> str:
    return f"{BASE}/ceres/v1/accounts/"


def futures_orders() -> str:
    return f"{BASE}/ceres/v1/orders/"


def futures_order(order_id: str) -> str:
    return f"{BASE}/ceres/v1/orders/{order_id}/"


def futures_products(product_id: str) -> str:
    """Futures product metadata (contract specs)."""
    return f"{BASE}/arsenal/v1/futures/products/{product_id}"


def futures_closes() -> str:
    """Previous close prices for futures contracts."""
    return f"{BASE}/marketdata/futures/closes/v1/"


def futures_closes_range() -> str:
    """Historical close range for a futures contract."""
    return f"{BASE}/marketdata/futures/closesrange/v1/"


def futures_user_settings() -> str:
    """Futures user settings."""
    return f"{BASE}/ceres/v1/user_settings"


def futures_pnl_cost_basis(account_id: str) -> str:
    """Futures P&L and cost basis."""
    return f"{BASE}/ceres/v1/accounts/{account_id}/pnl_cost_basis"


def futures_aggregated_positions(account_id: str) -> str:
    """Aggregated futures positions."""
    return f"{BASE}/ceres/v1/accounts/{account_id}/aggregated_positions"


# ── Indexes ─────────────────────────────────────────────────────────────────

def indexes() -> str:
    return f"{BASE}/indexes/"


def index_by_id(index_id: str) -> str:
    return f"{BASE}/indexes/{index_id}/"


def index_by_symbol(symbol: str) -> str:
    return f"{BASE}/indexes/?symbol={symbol}"


def index_quote(index_id: str) -> str:
    return f"{BASE}/marketdata/indexes/values/v1/{index_id}/"


def index_values(ids: str) -> str:
    """Batch index values by comma-separated instrument IDs."""
    return f"{BASE}/marketdata/indexes/values/v1/?ids={ids}"


def index_fundamentals(ids: str) -> str:
    """Index fundamentals (high/low, 52-week range) by comma-separated IDs."""
    return f"{BASE}/marketdata/indexes/fundamentals/v1/?ids={ids}"


def index_closes(ids: str) -> str:
    """Previous close values for indexes by comma-separated IDs."""
    return f"{BASE}/marketdata/indexes/closes/v1/?ids={ids}"


# ── Markets ─────────────────────────────────────────────────────────────────

def markets() -> str:
    return f"{BASE}/markets/"


def market_hours(market_code: str, date: str) -> str:
    return f"{BASE}/markets/{market_code}/hours/{date}/"


def movers(direction: str = "up") -> str:
    return f"{BASE}/midlands/movers/sp500/?direction={direction}"


def categories() -> str:
    return f"{BASE}/midlands/tags/discovery/"


def category_instruments(tag: str) -> str:
    return f"{BASE}/midlands/tags/tag/{tag}/"


# ── Orders ─────────────────────────────────────────────────────────────────

def orders() -> str:
    return f"{BASE}/orders/"


def stock_orders() -> str:
    return f"{BASE}/orders/"


def order(order_id: str) -> str:
    return f"{BASE}/orders/{order_id}/"


def cancel_order(order_id: str) -> str:
    return f"{BASE}/orders/{order_id}/cancel/"


def cancel_stock_order(order_id: str) -> str:
    return f"{BASE}/orders/{order_id}/cancel/"


def combo_orders() -> str:
    """Combo/multi-leg orders."""
    return f"{BASE}/combo/orders/"


def orders_fees() -> str:
    """Order fee calculation (POST)."""
    return f"{BASE}/orders/fees/"


# ── Screeners ─────────────────────────────────────────────────────────────

def screeners(include_filters: bool = True) -> str:
    return f"{BONFIRE_BASE}/screeners?include_filters={str(include_filters).lower()}"


def screener_presets() -> str:
    return f"{BONFIRE_BASE}/screeners/presets/"


def screener(screener_id: str) -> str:
    return f"{BONFIRE_BASE}/screeners/{screener_id}/"


def screener_indicators() -> str:
    return f"{BONFIRE_BASE}/screeners/indicators/"


def screener_scan() -> str:
    return f"{BONFIRE_BASE}/screeners/scan/"


# ── Bonfire (enriched UI data) ─────────────────────────────────────────────

def bonfire_live_portfolio(account_number: str) -> str:
    """Live portfolio data with real-time market values."""
    return f"{BONFIRE_BASE}/portfolio/account/{account_number}/live"


def bonfire_performance(account_number: str) -> str:
    """Portfolio performance chart data."""
    return f"{BONFIRE_BASE}/portfolio/performance/{account_number}"


def bonfire_positions_v2(account_number: str) -> str:
    """Enriched positions with UI metadata."""
    return f"{BONFIRE_BASE}/portfolio/{account_number}/positions_v2"


def bonfire_market_indices() -> str:
    """Market index summaries (S&P 500, Nasdaq, etc.)."""
    return f"{BONFIRE_BASE}/market_indices"


def bonfire_chart_bounds() -> str:
    """Chart time bounds based on market hours."""
    return f"{BONFIRE_BASE}/instruments/chart-bounds/"


def bonfire_search() -> str:
    """Unified search (stocks, crypto, lists, futures)."""
    return f"{BONFIRE_BASE}/search/"


def bonfire_nbbo_summary(instrument_id: str) -> str:
    """NBBO (National Best Bid/Offer) summary for an instrument."""
    return f"{BONFIRE_BASE}/instruments/{instrument_id}/nbbo-summary/"


def bonfire_etp_details(instrument_id: str) -> str:
    """ETP (ETF/ETN) details — AUM, expense ratio, holdings, performance."""
    return f"{BONFIRE_BASE}/instruments/{instrument_id}/etp-details/"


def bonfire_historical_chart(instrument_id: str) -> str:
    """Pre-rendered chart data for an instrument."""
    return f"{BONFIRE_BASE}/instruments/{instrument_id}/historical-chart/"


def bonfire_sparkline(instrument_id: str) -> str:
    """1-day sparkline chart data for an instrument."""
    return f"{BONFIRE_BASE}/instruments/{instrument_id}/1d-sparkline/"


def bonfire_instrument_buying_power(account_number: str, instrument_id: str) -> str:
    """Buying power for a specific instrument in an account."""
    return f"{BONFIRE_BASE}/accounts/{account_number}/instrument_buying_power/{instrument_id}/"


def bonfire_margin_settings(account_number: str) -> str:
    """Margin account settings."""
    return f"{BONFIRE_BASE}/margin/{account_number}/settings/"


def bonfire_margin_eligibility(account_number: str) -> str:
    """Margin eligibility for an account."""
    return f"{BONFIRE_BASE}/margin/{account_number}/eligibility"


# ── Alerts & Notification Settings ─────────────────────────────────────────

def notification_settings(instrument_id: str) -> str:
    """Alert settings (price & indicator alerts) for an instrument."""
    return f"{BASE}/midlands/notification_settings/instruments/{instrument_id}/"
