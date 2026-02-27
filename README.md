# LIL JON

## WHAT?! An Async Robinhood API Client Library?! YEAH!!

LilJon is a **custom async-first Robinhood API client library** that replaced the third-party `robin_stocks` package. OOOK! It's built from the ground up with `httpx`, Pydantic models, and Fernet-encrypted token caching. Every call is async. Every response is typed. Every token is ENCRYPTED. YEAH!!

## WHAT'S IN THE BOX?!

```
python/src/liljon/
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
│   ├── stocks.py      # Quotes, fundamentals, historicals, news
│   ├── options.py     # Chains, instruments, market data, positions
│   ├── crypto.py      # Pairs, quotes, holdings, orders
│   ├── futures.py     # Contracts, quotes, accounts, orders
│   ├── indexes.py     # Index quotes, fundamentals, closes
│   ├── account.py     # Positions, portfolio, watchlists, dividends
│   ├── orders.py      # Place, cancel, list stock orders
│   ├── markets.py     # Market hours, movers, categories
│   └── screeners.py   # Stock screeners and scans
└── models/            # Pydantic response models for EVERYTHING
    ├── stocks.py      # StockQuote, Fundamentals, HistoricalBar, etc.
    ├── options.py     # OptionChain, OptionInstrument, etc.
    ├── crypto.py      # CryptoPair, CryptoQuote, CryptoHolding, etc.
    ├── futures.py     # FuturesContract, FuturesQuote, etc.
    ├── indexes.py     # IndexQuote, IndexFundamentals, etc.
    ├── account.py     # Position, PortfolioProfile, Watchlist, etc.
    ├── orders.py      # OrderResult
    ├── screeners.py   # Screener, ScanResult, Indicator, etc.
    └── common.py      # PaginatedResponse, TimestampMixin
```

## KEY FEATURES - TURN DOWN FOR WHAT?!

- **Async HTTP** — httpx-based transport with connection pooling. FAST!! OOOK!
- **Pydantic Models** — Every single API response is typed. No guessing. WHAT?! YEAH!!
- **Fernet-Encrypted Token Cache** — Your tokens are stored at `~/.tokens/liljon_tokens.enc`, encrypted with a machine-derived key. AIN'T NOBODY STEALING YOUR TOKENS!!
- **Two-Step MFA** — Supports SMS and email verification flows. SECURE!! OOOK!
- **Namespace APIs** — Clean `client.stocks`, `client.options`, `client.crypto` namespaces. ORGANIZED!!
- **Pagination** — Automatic URL-based and cursor-based pagination. GETS ALL THE DATA!! YEAH!!
- **Full CLI** — Interactive testing tool with Rich tables and panels. PRETTY!! WHAT?!
- **Exception Hierarchy** — All errors inherit from `RobinhoodError` for easy catching. OOOK!

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

# Get fundamentals - DO YOUR DD!! OOOK!
fundamentals = await client.stocks.get_fundamentals("NVDA")

# Get historicals - WHERE WE BEEN?! YEAH!!
bars = await client.stocks.get_historicals("AAPL", interval="day", span="month")

# Get news - WHAT'S HAPPENING?!
news = await client.stocks.get_news("TSLA")
```

### Options - OOOK! ADVANCED MOVES!!

```python
# Get option chains
chains = await client.options.get_chains("AAPL")

# Get specific instruments
instruments = await client.options.get_instruments(
    chain_id=chains[0].id,
    expiration_dates=["2026-03-20"],
    option_type="call"
)

# Get market data for an option - WHAT'S IT WORTH?!
data = await client.options.get_market_data(instrument.id)
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

# Get watchlist - WHAT AM I WATCHING?! OOOK!
watchlist = await client.account.get_default_watchlist()
```

### Orders - EXECUTE!! EXECUTE!!

```python
# Place a market buy - LET'S GOOO!!
order = await client.orders.place_order(
    account_id=account_id,
    instrument_url=instrument_url,
    symbol="AAPL",
    quantity=1,
    side="buy",
    order_type="market",
    time_in_force="gfd",
)

# Cancel an order - NEVERMIND!! WHAT?!
await client.orders.cancel_order(order_id)
```

### Futures - OOOK! BIG BOY MOVES!!

```python
# Get contracts
contracts = await client.futures.get_contracts()

# Get quote for a contract
quote = await client.futures.get_quote(contract_id)
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

## THE CLI - COMMAND LINE CRUNK!! OOOK!

Run the CLI with:

```bash
uv run python -m liljon [OPTIONS] COMMAND [ARGS]
```

### Global Options

| Option | Description |
|---|---|
| `--json` | Output raw JSON instead of Rich tables. YEAH!! |

### Auth Commands - OOOK! GOTTA GET IN FIRST!!

```bash
# Check auth status - AM I IN?! WHAT?!
uv run python -m liljon auth status

# Interactive login (prompts for credentials + 2FA)
uv run python -m liljon auth login

# Logout and clear cached tokens - PEACE OUT!!
uv run python -m liljon auth logout
```

### Stocks Commands - GET THAT MARKET DATA!!

```bash
# Get quotes for one or more symbols - WHAT'S THE PRICE?!
uv run python -m liljon stocks quote AAPL MSFT NVDA

# Get quotes by instrument IDs
uv run python -m liljon stocks quote-by-ids <id1> <id2>

# Get fundamentals - DO YOUR HOMEWORK!! OOOK!
uv run python -m liljon stocks fundamentals AAPL

# Get historical bars - YEAH!!
uv run python -m liljon stocks historicals AAPL --interval day --span month

# Get news for a ticker
uv run python -m liljon stocks news TSLA

# Get instrument info
uv run python -m liljon stocks instrument <instrument_id>
```

### Account Commands - SHOW ME THE MONEY!! WHAT?!

```bash
# View positions
uv run python -m liljon account positions

# View portfolio - THE WHOLE THING!! YEAH!!
uv run python -m liljon account portfolio

# View dividends - PASSIVE INCOME!! OOOK!
uv run python -m liljon account dividends

# View default watchlist
uv run python -m liljon account watchlists

# Create a watchlist
uv run python -m liljon account watchlist-create "My List"

# Add to watchlist
uv run python -m liljon account watchlist-add <list_id> <instrument_url>

# Remove from watchlist
uv run python -m liljon account watchlist-remove <item_id>

# View account details
uv run python -m liljon account details
```

### Orders Commands - MAKE MOVES!! WHAT?!

```bash
# List recent orders
uv run python -m liljon orders list

# Get specific order - WHAT HAPPENED?!
uv run python -m liljon orders get <order_id>

# Place a market buy - LET'S GOOO!!
uv run python -m liljon orders buy AAPL --quantity 1 --type market

# Place a market sell - TAKE PROFITS!! YEAH!!
uv run python -m liljon orders sell AAPL --quantity 1 --type market

# Cancel an order - OOOK! CHANGED MY MIND!!
uv run python -m liljon orders cancel <order_id>
```

### Options Commands - YEAH!! DERIVATIVES!!

```bash
# Get option chains for a symbol
uv run python -m liljon options chains AAPL

# Search option instruments
uv run python -m liljon options instruments --chain-id <id> --expiration 2026-03-20 --type call

# Get market data for an option
uv run python -m liljon options market-data <option_id>

# View option positions - WHAT AM I HOLDING?!
uv run python -m liljon options positions

# View option orders - WHAT DID I DO?! OOOK!
uv run python -m liljon options orders
```

### Crypto Commands - DIGITAL ASSETS!! WHAT?!

```bash
# List available crypto pairs
uv run python -m liljon crypto pairs

# Get a crypto quote
uv run python -m liljon crypto quote <pair_id>

# View crypto holdings - HOW MUCH CRYPTO?! YEAH!!
uv run python -m liljon crypto holdings

# Get crypto historicals
uv run python -m liljon crypto historicals <pair_id> --interval hour --span week
```

### Futures Commands - OOOK! THE FUTURE IS NOW!!

```bash
# List futures contracts
uv run python -m liljon futures contracts

# Get a futures quote
uv run python -m liljon futures quote <contract_id>

# View futures account
uv run python -m liljon futures account

# View futures orders
uv run python -m liljon futures orders

# View futures P&L - AM I WINNING?! WHAT?!
uv run python -m liljon futures pnl
```

### Indexes Commands - MARKET BENCHMARKS!! YEAH!!

```bash
# Get index quote
uv run python -m liljon indexes quote SPX NDX

# Get index instrument info
uv run python -m liljon indexes instrument SPX

# Get index fundamentals - THE NUMBERS!! OOOK!
uv run python -m liljon indexes fundamentals SPX NDX

# Get previous closes
uv run python -m liljon indexes closes SPX NDX

# Get index option chains
uv run python -m liljon indexes chains SPX
```

### Markets Commands - WHAT TIME IS IT?!

```bash
# List all markets
uv run python -m liljon markets list

# Get market hours for a date - WHEN'S IT OPEN?! YEAH!!
uv run python -m liljon markets hours XNYS 2026-02-27

# Get S&P 500 movers - WHO'S MOVING?! OOOK!
uv run python -m liljon markets movers --direction up

# List discovery categories
uv run python -m liljon markets categories

# Get instruments in a category
uv run python -m liljon markets category <tag>
```

### Screeners Commands - FIND THE WINNERS!! WHAT?!

```bash
# List all screeners
uv run python -m liljon screeners list

# Get preset screeners - EASY MODE!! YEAH!!
uv run python -m liljon screeners presets

# Get a specific screener
uv run python -m liljon screeners get <screener_id>

# List available indicators
uv run python -m liljon screeners indicators

# Run a screener scan - SCAN IT!! OOOK!
uv run python -m liljon screeners scan <screener_id>

# Run a custom query
uv run python -m liljon screeners query --indicator <name> --min <val> --max <val>
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
uv run pytest tests/test_liljon/ --cov=python/src/liljon -v
```

83 tests covering the client, auth flow, HTTP transport, pagination, models, endpoints, and API namespaces. YEAH!! THAT'S THOROUGH!! OOOK!

---

**LilJon** — TURN DOWN FOR WHAT?! Your async Robinhood API client that GETS. IT. DONE. OOOK!! YEAH!! WHAT?!
