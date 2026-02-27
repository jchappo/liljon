"""Pure URL string templates for the Robinhood API.

Every function returns a URL string. No side effects, no HTTP calls, no state.
Functions that need dynamic IDs take them as parameters.
"""

BASE = "https://api.robinhood.com"
NUMMUS_BASE = "https://nummus.robinhood.com"
BONFIRE_BASE = "https://bonfire.robinhood.com"

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


# ── Stocks ──────────────────────────────────────────────────────────────────

def quotes(symbols: str) -> str:
    """Comma-separated symbols → market-data quotes."""
    return f"{BASE}/marketdata/quotes/?symbols={symbols}"


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


def quote(symbol: str) -> str:
    return f"{BASE}/marketdata/quotes/{symbol}/"


def instruments() -> str:
    return f"{BASE}/instruments/"


def instrument(instrument_id: str) -> str:
    return f"{BASE}/instruments/{instrument_id}/"


def instrument_by_url(url: str) -> str:
    return url


def fundamentals(symbol: str) -> str:
    return f"{BASE}/fundamentals/{symbol}/"


def historicals(symbol: str, interval: str, span: str, bounds: str = "regular") -> str:
    return f"{BASE}/marketdata/historicals/{symbol}/?interval={interval}&span={span}&bounds={bounds}"


def news(symbol: str) -> str:
    return f"{BASE}/midlands/news/{symbol}/"


def latest_price(symbols: str) -> str:
    return f"{BASE}/marketdata/quotes/?symbols={symbols}"


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
