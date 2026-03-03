# LIL JON

## WHAT?! An Async Robinhood API Client Library?! YEAH!!

LilJon is a **custom async-first Robinhood API client library** that replaced the third-party `robin_stocks` package. OOOK! It's built from the ground up with `httpx`, Pydantic models, and Fernet-encrypted token caching. Every call is async. Every response is typed. Every token is ENCRYPTED. YEAH!!

## WHAT'S IN THE BOX?!

```
src/liljon/
├── client.py          # The main RobinhoodClient - THIS IS WHERE THE PARTY STARTS!!
├── cli.py             # Full CLI tool for testing - COMMAND LINE CRUNK!!
├── __main__.py        # Run it as a module, baby!
├── _http.py           # httpx transport with auth headers - OOOK!
├── _endpoints.py      # Pure URL templates, zero side effects - CLEAN!!
├── _pagination.py     # Handles paginated API responses - WHAT?!
├── exceptions.py      # Custom exception hierarchy - YEAH!!
├── auth/              # OAuth + MFA + token cache
│   ├── _flow.py       # Two-step auth flow (login → 2FA → done!)
│   ├── _token_cache.py # Fernet-encrypted storage - SECURE!! OOOK!
│   ├── _device_token.py # Device token generation
│   └── models.py      # TokenData, ChallengeInfo, LoginResult
├── api/               # API namespace modules
│   ├── stocks.py      # Quotes, fundamentals, historicals, news, batch lookups
│   ├── options.py     # Chains, instruments, market data, positions, strategies, P&L
│   ├── crypto.py      # Pairs, quotes, holdings, orders
│   ├── futures.py     # Contracts, quotes, accounts, orders, products, closes
│   ├── indexes.py     # Index quotes, fundamentals, closes
│   ├── account.py     # Positions, portfolio, watchlists, dividends, subscriptions, performance
│   ├── orders.py      # Place, cancel, list stock orders, combo orders, fee calculator
│   ├── markets.py     # Market hours, movers, categories
│   ├── screeners.py   # Stock screeners and scans
│   ├── discovery.py   # Analyst ratings, hedge funds, insiders, short interest, earnings, ETPs
│   └── alerts.py      # Price and indicator alerts (GET/POST/PATCH)
└── models/            # Pydantic response models for EVERYTHING
    ├── stocks.py      # StockQuote, Fundamentals, HistoricalBar, NewsArticle, etc.
    ├── options.py     # OptionChain, OptionInstrument, OptionMarketData, etc.
    ├── crypto.py      # CryptoPair, CryptoQuote, CryptoHolding, etc.
    ├── futures.py     # FuturesContract, FuturesQuote, FuturesOrder, etc.
    ├── indexes.py     # IndexQuote, IndexFundamentals, etc.
    ├── account.py     # Position, PortfolioProfile, LivePortfolio, UserProfile, etc.
    ├── orders.py      # OrderResult
    ├── screeners.py   # Screener, ScanResult, Indicator, etc.
    ├── discovery.py   # AnalystRating, HedgeFundSummary, InsiderSummary, ShortInterest, etc.
    ├── alerts.py      # AlertSettings, AlertSetting
    └── common.py      # PaginatedResponse, TimestampMixin
```

## KEY FEATURES - TURN DOWN FOR WHAT?!

- **Async HTTP** — httpx-based transport with connection pooling. FAST!! OOOK!
- **Pydantic Models** — Every single API response is typed. No guessing. WHAT?! YEAH!!
- **Fernet-Encrypted Token Cache** — Your tokens are stored at `~/.tokens/liljon_tokens.enc`, encrypted with a machine-derived key. AIN'T NOBODY STEALING YOUR TOKENS!!
- **Two-Step MFA** — Supports SMS and email verification flows. SECURE!! OOOK!
- **13 Namespace APIs** — Clean `client.stocks`, `client.options`, `client.crypto`, `client.discovery`, `client.alerts` and more. ORGANIZED!!
- **Pagination** — Automatic URL-based and cursor-based pagination. GETS ALL THE DATA!! YEAH!!
- **Full CLI** — Interactive testing tool with Rich tables and panels. PRETTY!! WHAT?!
- **Exception Hierarchy** — All errors inherit from `RobinhoodError` for easy catching. OOOK!
- **Discovery Engine** — Analyst ratings, hedge fund activity, insider trading, short interest, earnings, similar instruments. DEEP RESEARCH!!
- **Price Alerts** — Create and manage price and indicator alerts via API. NEVER MISS A MOVE!! YEAH!!

## INSTALLATION - LET'S GET IT!! OOOK!

```bash
pip install liljon
```

Requires Python 3.12+. Dependencies: `httpx`, `pydantic`, `cryptography`, `click`, `rich`.

## USING THE LIBRARY - LET'S GOOO!!

### Basic Usage

```python
from liljon import RobinhoodClient

# YEAH!! Create a client and get some quotes!
async with RobinhoodClient() as client:
    await client.try_restore_session()
    quotes = await client.stocks.get_quotes(["AAPL", "MSFT", "NVDA"])
    for q in quotes:
        print(f"{q.symbol}: ${q.last_trade_price}")  # OOOK!
```

### Authentication - WHAT?! YOU GOTTA LOG IN FIRST!!

```python
from liljon import RobinhoodClient

async with RobinhoodClient() as client:
    # Try cached session first - SKRRT SKRRT!
    if await client.try_restore_session():
        print("Already logged in! YEAH!!")
    else:
        # Phase 1: Send credentials
        result = await client.login("your@email.com", "password")

        # Phase 2: Handle 2FA if needed - WHAT?!
        if result.status == "challenge_required":
            code = input("Enter your verification code: ")
            result = await client.submit_verification(code)

        if result.status == "logged_in":
            print(f"OOOK! Logged in as {result.username}!")
```

### Stocks - GET THAT BREAD!!

```python
# Get quotes - WHAT ARE THESE PRICES?!
quotes = await client.stocks.get_quotes(["AAPL", "TSLA"])

# Get a single quote
quote = await client.stocks.get_quote("AAPL")

# Get quotes by instrument IDs with session bounds
quotes = await client.stocks.get_quotes_by_ids(["id1", "id2"], bounds="24_5")

# Get latest prices - QUICK LOOK!! YEAH!!
prices = await client.stocks.get_latest_price(["AAPL", "TSLA"])

# Get fundamentals - DO YOUR DD!! OOOK!
fundamentals = await client.stocks.get_fundamentals("NVDA")

# Get fundamentals by instrument ID (session-aware)
fundamentals = await client.stocks.get_fundamentals_by_id(instrument_id, bounds="24_5")

# Get fundamentals history over time
history = await client.stocks.get_fundamentals_history(["id1", "id2"], start_date="2025-01-01")

# Get historicals - WHERE WE BEEN?! YEAH!!
bars = await client.stocks.get_historicals("AAPL", interval="day", span="month")

# Get batch historicals by instrument IDs
batch = await client.stocks.get_historicals_by_ids(["id1", "id2"], interval="5minute", span="day")

# Get news - WHAT'S HAPPENING?!
news = await client.stocks.get_news("TSLA")

# Get market-wide news (no symbol) - ALL THE NEWS!! OOOK!
news = await client.stocks.get_news()

# Resolve a symbol to its instrument
instrument = await client.stocks.get_instrument_by_symbol("AAPL")
```

### Options - OOOK! ADVANCED MOVES!!

```python
# Get option chains
chains = await client.options.get_chains(instrument_id)

# Get specific instruments
instruments = await client.options.get_instruments(
    chain_id=chains[0].id,
    expiration_dates=["2026-03-20"],
    option_type="call"
)

# Get market data for an option - WHAT'S IT WORTH?!
data = await client.options.get_market_data(instrument.id)

# Batch market data for multiple options - YEAH!!
batch = await client.options.get_market_data_batch(["opt_id1", "opt_id2"])

# Get aggregated positions grouped by strategy
positions = await client.options.get_aggregate_positions()

# Get option strategies
strategies = await client.options.get_strategies(["strategy_code"])

# Get strategy-level quotes with greeks
quotes = await client.options.get_strategy_quotes(ids=["opt_id1", "opt_id2"])

# Get chain collateral requirements - HOW MUCH MARGIN?! OOOK!
collateral = await client.options.get_chain_collateral(chain_id)

# Get option events (expirations, assignments, exercises)
events = await client.options.get_events()

# Get P&L chart data
pnl = await client.options.get_pnl_chart(legs="...", order_price="1.50", quantity="1")

# Get breakeven calculations
breakevens = await client.options.get_breakevens(strategy_code, average_cost="150.00")
```

### Crypto - DIGITAL MONEY!! YEAH!!

```python
# List crypto pairs - WHAT COINS WE GOT?!
pairs = await client.crypto.get_pairs()

# Get a quote
quote = await client.crypto.get_quote(pair_id)

# Get holdings - SHOW ME THE CRYPTO!! OOOK!
holdings = await client.crypto.get_holdings()
```

### Account - WHERE'S MY MONEY AT?! WHAT?!

```python
# Get positions - WHAT AM I HOLDING?!
positions = await client.account.get_positions()

# Get portfolio - THE BIG PICTURE!! YEAH!!
account_id = client.get_account_number()
portfolio = await client.account.get_portfolio(account_id)

# Get live portfolio with real-time values - LIVE DATA!! OOOK!
live = await client.account.get_live_portfolio(account_number)

# Get portfolio performance chart data
perf = await client.account.get_portfolio_performance(account_number, display_span="month")

# Get Phoenix unified account snapshot
phoenix = await client.account.get_phoenix_account()

# Get user profile
user = await client.account.get_user()

# Get active subscriptions (Gold, etc.)
subs = await client.account.get_subscriptions()

# Get watchlists with items - WHAT AM I WATCHING?! OOOK!
watchlists = await client.account.get_watchlists()

# Add/remove symbols from watchlists
await client.account.add_symbols_to_watchlist(["AAPL", "MSFT"], name="Main")
await client.account.remove_symbols_from_watchlist(["TSLA"], name="Main")

# Get dividends
dividends = await client.account.get_dividends()

# Get cash sweep interest rates
interest = await client.account.get_sweep_interest(account_number)

# Get historical activities (trades, dividends, transfers)
activities = await client.account.get_historical_activities()

# Get stock lending income
payments = await client.account.get_stock_loan_payments()

# Get buying power for a specific instrument
bp = await client.account.get_instrument_buying_power(account_number, instrument_id)
```

### Orders - EXECUTE!! EXECUTE!!

```python
# Place a stock order - LET'S GOOO!!
order = await client.orders.place_stock_order(
    symbol="AAPL",
    quantity=1,
    side="buy",
    order_type="market",
    time_in_force="gfd",
)

# Convenience wrappers - QUICK AND EASY!! YEAH!!
await client.orders.buy_market("AAPL", 1)
await client.orders.buy_limit("AAPL", 1, price=150.00)
await client.orders.sell_market("AAPL", 1)
await client.orders.sell_stop_loss("AAPL", 1, stop_price=140.00)

# Cancel an order - NEVERMIND!! WHAT?!
await client.orders.cancel_stock_order(order_id)

# Get combo/multi-leg orders - COMPLEX TRADES!! OOOK!
combos = await client.orders.get_combo_orders(states="pending")

# Calculate fees before placing an order
fees = await client.orders.calculate_fees(
    instrument_id=inst_id, quantity="10", price="150.00", side="buy"
)
```

### Futures - OOOK! BIG BOY MOVES!!

```python
# Get contracts by product ID
contracts = await client.futures.get_contracts(product_ids=["ES"])

# Get quote for a contract
quote = await client.futures.get_quote(contract_id)

# Batch quotes
quotes = await client.futures.get_quotes(["id1", "id2"])

# Get futures account
account = await client.futures.get_account()

# Get futures orders
orders = await client.futures.get_orders()

# Calculate realized P&L - AM I WINNING?! YEAH!!
pnl = await client.futures.calculate_pnl()

# Get product metadata (contract specs)
product = await client.futures.get_product(product_id)

# Get previous closes
closes = await client.futures.get_closes(["id1", "id2"])

# Get historical close range
closes = await client.futures.get_closes_range(contract_id, start="2025-01-01T00:00:00Z")

# Get futures user settings
settings = await client.futures.get_user_settings()

# Get P&L cost basis
pnl = await client.futures.get_pnl_cost_basis(account_id)

# Get aggregated positions
positions = await client.futures.get_aggregated_positions(account_id)
```

### Indexes - TRACK THE MARKET!! YEAH!!

```python
# Get index quotes (S&P 500, NASDAQ, etc.)
quotes = await client.indexes.get_values(ids="SPX,NDX")

# Get index fundamentals - THE FUNDAMENTALS!! WHAT?!
fundies = await client.indexes.get_fundamentals(ids="SPX")
```

### Screeners - FIND THE GEMS!! OOOK!

```python
# List available screeners
screeners = await client.screeners.get_screeners()

# Get presets - PRE-BUILT FILTERS!! YEAH!!
presets = await client.screeners.get_presets()

# Run a scan - SCAN THE MARKET!! WHAT?!
results = await client.screeners.scan(screener_id, filters=my_filters)
```

### Discovery - DEEP RESEARCH!! WHAT?! YEAH!!

```python
# Analyst ratings (buy/hold/sell, price targets)
ratings = await client.discovery.get_ratings(instrument_id)
ratings_batch = await client.discovery.get_ratings_batch(["id1", "id2"])

# Hedge fund activity - WHAT ARE THE BIG BOYS DOING?! OOOK!
summary = await client.discovery.get_hedgefund_summary(instrument_id)
transactions = await client.discovery.get_hedgefund_transactions(instrument_id)

# Insider trading - WHO'S BUYING THEIR OWN STOCK?! YEAH!!
insiders = await client.discovery.get_insider_summary(instrument_id)
insider_txns = await client.discovery.get_insider_transactions(instrument_id)

# Short interest - WHO'S BETTING AGAINST IT?! WHAT?!
short = await client.discovery.get_short_interest(instrument_id)

# Equity summary — daily net buy/sell flow
equity = await client.discovery.get_equity_summary(instrument_id)

# Earnings data
earnings = await client.discovery.get_earnings(instrument_id)

# Similar instruments - FIND MORE LIKE THIS!! OOOK!
similar = await client.discovery.get_similar(instrument_id)

# Market indices (S&P 500, Nasdaq, Dow, VIX, Russell)
indices = await client.discovery.get_market_indices(symbols=["SPX", "NDX", "DJX"])

# ETP (ETF/ETN) details — AUM, expense ratio, holdings
etp = await client.discovery.get_etp_details(instrument_id)

# NBBO (National Best Bid/Offer) summary
nbbo = await client.discovery.get_nbbo_summary(instrument_id)

# Chart time bounds
bounds = await client.discovery.get_chart_bounds()

# Unified search across stocks, crypto, futures - FIND ANYTHING!! YEAH!!
results = await client.discovery.search("AAPL")
```

### Alerts - NEVER MISS A MOVE!! OOOK!

```python
# Get all alerts for an instrument
alerts = await client.alerts.get_alerts(instrument_id)

# Create a price alert - TELL ME WHEN IT HITS!! YEAH!!
await client.alerts.create_alert(instrument_id, [
    {"enabled": True, "price": "200.00", "setting_type": "price_above"}
])

# Update an alert - CHANGE THE TARGET!! WHAT?!
await client.alerts.update_alert(instrument_id, [
    {"id": alert_id, "setting_type": "price_above", "enabled": False}
])
```

## THE CLI - COMMAND LINE CRUNK!! OOOK!

Run the CLI with:

```bash
uv run python -m liljon [OPTIONS] COMMAND [ARGS]
```

Or if installed via pip:

```bash
liljon [OPTIONS] COMMAND [ARGS]
```

### Global Options

| Option | Description |
|---|---|
| `--json` | Output raw JSON instead of Rich tables. YEAH!! |

### Auth Commands - OOOK! GOTTA GET IN FIRST!!

```bash
# Check auth status - AM I IN?! WHAT?!
liljon auth status

# Interactive login (prompts for credentials + 2FA)
liljon auth login

# Logout and clear cached tokens - PEACE OUT!!
liljon auth logout
```

### Stocks Commands - GET THAT MARKET DATA!!

```bash
# Get quotes for one or more symbols - WHAT'S THE PRICE?!
liljon stocks quote AAPL MSFT NVDA

# Quick latest price
liljon stocks price AAPL TSLA

# Get quotes by instrument IDs (with session bounds)
liljon stocks quote-by-ids <id1> <id2> --bounds 24_5

# Get fundamentals - DO YOUR HOMEWORK!! OOOK!
liljon stocks fundamentals AAPL

# Get fundamentals by instrument ID (session-aware)
liljon stocks fundamentals-by-id <instrument_id> --bounds 24_5

# Get 52-week fundamentals history
liljon stocks fundamentals-history <instrument_id1> <instrument_id2> --start-date 2025-01-01

# Get historical bars - YEAH!!
liljon stocks historicals AAPL --interval day --span month --last 30

# Get instrument metadata
liljon stocks instrument AAPL

# Get news for a ticker
liljon stocks news TSLA --limit 20

# Get market-wide news (no symbol) - ALL THE NEWS!! OOOK!
liljon stocks news
```

### Account Commands - SHOW ME THE MONEY!! WHAT?!

```bash
# View account info (buying power, cash, etc.)
liljon account info

# View portfolio - THE WHOLE THING!! YEAH!!
liljon account portfolio

# View positions
liljon account positions

# View dividends - PASSIVE INCOME!! OOOK!
liljon account dividends

# View all watchlists with symbols
liljon account watchlists

# Create a watchlist
liljon account watchlist-create "My List"

# Add symbols to a watchlist
liljon account watchlist-add AAPL MSFT --name "My First List"

# Remove symbols from a watchlist
liljon account watchlist-remove TSLA --name "My First List"

# View user profile
liljon account user

# View active subscriptions (Gold, etc.)
liljon account subscriptions

# View live portfolio with real-time values
liljon account live

# View portfolio performance chart data
liljon account performance --span month

# View cash sweep interest rates
liljon account sweep-interest

# View historical activities (trades, dividends, transfers)
liljon account activities

# View buying power for a specific instrument
liljon account buying-power <instrument_id>
```

### Orders Commands - MAKE MOVES!! WHAT?!

```bash
# List recent orders
liljon orders list

# Get specific order - WHAT HAPPENED?!
liljon orders get <order_id>

# Place a market buy - LET'S GOOO!!
liljon orders buy AAPL 1 --type market --confirm

# Place a limit buy
liljon orders buy AAPL 1 --type limit --price 150.00 --confirm

# Place a stop-loss sell
liljon orders sell AAPL 1 --type stoploss --stop-price 140.00 --confirm

# Place a market sell - TAKE PROFITS!! YEAH!!
liljon orders sell AAPL 1 --type market --confirm

# Cancel an order - OOOK! CHANGED MY MIND!!
liljon orders cancel <order_id> --confirm

# View combo/multi-leg orders
liljon orders combo --states pending

# Calculate fees before placing an order
liljon orders fees <instrument_id> 10 150.00 buy
```

### Options Commands - YEAH!! DERIVATIVES!!

```bash
# Get option chains for a symbol
liljon options chains AAPL

# Search option instruments
liljon options instruments <chain_id> --expiration 2026-03-20 --type call

# Get market data for an option (greeks, IV, prices)
liljon options market-data <option_id>

# Batch market data for multiple options
liljon options market-data-batch <option_id1> <option_id2>

# View option positions - WHAT AM I HOLDING?!
liljon options positions

# View aggregated positions by strategy
liljon options aggregate

# View option orders - WHAT DID I DO?! OOOK!
liljon options orders

# View option events (expirations, assignments, exercises)
liljon options events --chain-id <chain_id>

# Get option strategies
liljon options strategies <strategy_code1> <strategy_code2>

# Get strategy-level quotes
liljon options strategy-quotes <opt_id1> <opt_id2> --ratios 1,1 --types long,short

# Get P&L chart data
liljon options pnl-chart --legs "..." --order-price 1.50 --quantity 1

# Get breakeven calculations
liljon options breakevens <strategy_code> <average_cost>
```

### Crypto Commands - DIGITAL ASSETS!! WHAT?!

```bash
# List available crypto pairs
liljon crypto pairs

# Get a crypto quote (by symbol, e.g. BTC)
liljon crypto quote BTC

# View crypto holdings - HOW MUCH CRYPTO?! YEAH!!
liljon crypto holdings

# Get crypto historicals
liljon crypto historicals BTC --interval hour --span week --last 48
```

### Futures Commands - OOOK! THE FUTURE IS NOW!!

```bash
# List futures contracts by product ID
liljon futures contracts ES NQ

# Get a futures quote
liljon futures quote <contract_id>

# View futures account
liljon futures account

# View futures orders
liljon futures orders

# View futures P&L - AM I WINNING?! WHAT?!
liljon futures pnl

# Get product metadata (contract specs)
liljon futures product <product_id>

# Get previous close prices
liljon futures closes <contract_id1> <contract_id2>

# Get historical close range
liljon futures closes-range <contract_id> <start_datetime>

# View futures user settings
liljon futures settings

# Get P&L cost basis
liljon futures pnl-cost-basis <account_id> --contract-id <contract_id>

# Get aggregated positions
liljon futures aggregated-positions <account_id>
```

### Indexes Commands - MARKET BENCHMARKS!! YEAH!!

```bash
# Get index quote
liljon indexes quote SPX

# Get index instrument info
liljon indexes instrument SPX

# Get index fundamentals - THE NUMBERS!! OOOK!
liljon indexes fundamentals SPX NDX

# Get previous closes
liljon indexes closes SPX

# Get index option chains
liljon indexes chains SPX
```

### Markets Commands - WHAT TIME IS IT?!

```bash
# List all markets
liljon markets list

# Get market hours for a date - WHEN'S IT OPEN?! YEAH!!
liljon markets hours XNYS 2026-02-27

# Get S&P 500 movers - WHO'S MOVING?! OOOK!
liljon markets movers --direction up

# List discovery categories
liljon markets categories

# Get instruments in a category
liljon markets category <tag>
```

### Screeners Commands - FIND THE WINNERS!! WHAT?!

```bash
# List all screeners
liljon screeners list

# Get preset screeners - EASY MODE!! YEAH!!
liljon screeners presets

# Get a specific screener
liljon screeners get <screener_id>

# List available indicators
liljon screeners indicators

# Run a screener scan - SCAN IT!! OOOK!
liljon screeners scan <screener_id>

# Run a custom query with filters
liljon screeners query -i pe_ratio=pe_ratio_more_than_5
liljon screeners query -i market_cap=mkt_cap_large_cap,mkt_cap_mega_cap --sort market_cap
liljon screeners query -i sector=Technology -i 1d_price_change=daily_price_is_up
```

### Discovery Commands - DEEP RESEARCH!! YEAH!!

```bash
# Analyst ratings for an instrument
liljon discovery ratings <instrument_id>

# Batch analyst ratings
liljon discovery ratings-batch <id1> <id2>

# Hedge fund activity summary
liljon discovery hedgefunds <instrument_id>

# Detailed hedge fund transactions - WHO'S BUYING?! OOOK!
liljon discovery hedgefund-transactions <instrument_id>

# Insider trading summary
liljon discovery insiders <instrument_id>

# Detailed insider transactions
liljon discovery insider-transactions <instrument_id>

# Short interest data - WHAT?!
liljon discovery short-interest <instrument_id>

# Equity summary (daily buy/sell flow)
liljon discovery equity-summary <instrument_id>

# Earnings data
liljon discovery earnings <instrument_id>

# Similar instruments - FIND MORE!! YEAH!!
liljon discovery similar <instrument_id>

# Unified search across stocks, crypto, futures
liljon discovery search "apple"

# Market index summaries (S&P 500, Nasdaq, Dow, VIX, Russell)
liljon discovery market-indices --symbols SPX,NDX,DJX,VIX,RUT

# ETP (ETF/ETN) details — AUM, expense ratio, holdings
liljon discovery etp-details <instrument_id>

# NBBO summary - OOOK!
liljon discovery nbbo <instrument_id>

# Chart time bounds
liljon discovery chart-bounds
```

### Alerts Commands - SET IT AND FORGET IT!! OOOK!

```bash
# List all alerts for an instrument (accepts symbol or instrument ID)
liljon alerts list AAPL

# Create a price alert - TELL ME WHEN!! YEAH!!
liljon alerts create AAPL price_above --price 200.00

# Create an indicator alert
liljon alerts create AAPL rsi_above --interval 5m

# Update an alert (enable/disable, change price) - WHAT?!
liljon alerts update AAPL <alert_id> --disabled
liljon alerts update AAPL <alert_id> --price 250.00
```

## EXCEPTION HIERARCHY - WHEN THINGS GO WRONG!! WHAT?!

All exceptions inherit from `RobinhoodError` so you can catch the whole family. OOOK!

```
RobinhoodError                    # Base exception - THE BOSS!!
├── AuthenticationError           # Login/2FA/token refresh failed
│   ├── NotAuthenticatedError     # No valid session (HTTP 401) - LOG IN!! WHAT?!
│   └── ChallengeRequiredError    # Additional verification needed
├── APIError                      # Non-2xx HTTP response - OOOK!
│   └── RateLimitError            # HTTP 429 - SLOW DOWN!! YEAH!!
├── InvalidSymbolError            # Bad ticker symbol
├── OrderError                    # Order placement/cancellation failed
└── ValidationError               # Client-side validation failure
```

### Example Error Handling

```python
from liljon import RobinhoodClient, RobinhoodError, NotAuthenticatedError, RateLimitError

async with RobinhoodClient() as client:
    try:
        quotes = await client.stocks.get_quotes(["AAPL"])
    except NotAuthenticatedError:
        print("You ain't logged in! WHAT?!")
    except RateLimitError as e:
        print(f"Slow down! Retry after {e.retry_after}s. OOOK!")
    except RobinhoodError as e:
        print(f"Something went wrong: {e}. YEAH... that's not good.")
```

## TOKEN CACHE - KEEP YOUR SECRETS SAFE!! OOOK!

Tokens are stored encrypted at `~/.tokens/liljon_tokens.enc` using Fernet symmetric encryption. WHAT?! YEAH, THAT'S RIGHT — ENCRYPTED!!

- **Default key derivation**: SHA-256 hash of `{hostname}:{username}:{platform}` — machine-specific. OOOK!
- **Custom passphrase**: Pass `passphrase="your_secret"` to `RobinhoodClient()` for extra security. YEAH!!
- **Atomic writes**: Uses write-then-rename to prevent corruption. SAFE!!
- **Auto-refresh**: Tokens near expiry are automatically refreshed on session restore. SMART!! WHAT?!

```python
# Custom cache location - PUT IT WHERE YOU WANT!! OOOK!
client = RobinhoodClient(cache_path="/custom/path/tokens.enc")

# Custom passphrase - EXTRA SECURITY!! YEAH!!
client = RobinhoodClient(passphrase="TURN_DOWN_FOR_WHAT")
```

## RUNNING TESTS - MAKE SURE IT WORKS!! YEAH!!

```bash
# Run all LilJon tests - TEST EVERYTHING!! OOOK!
uv run pytest tests/test_liljon/ -v

# Run a specific test file
uv run pytest tests/test_liljon/test_client.py -v

# Run with coverage - HOW MUCH WE COVERING?! WHAT?!
uv run pytest tests/test_liljon/ --cov=src/liljon -v
```

---

**LilJon** — TURN DOWN FOR WHAT?! Your async Robinhood API client that GETS. IT. DONE. OOOK!! YEAH!! WHAT?!
