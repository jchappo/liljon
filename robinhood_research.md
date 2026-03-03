# Robinhood API — Endpoint Discovery & Implementation Status

## Capture History

| Date | Session | Total Requests | Unique Endpoints | Pages Visited |
|------|---------|----------------|------------------|---------------|
| 2026-02-27 | rh_network_capture.py | 510 | ~97 | GME, VIX stock detail pages |
| 2026-03-02 | rh_full_capture.py | 4,308 | 235 | Home, NVDA, SLV, Options chains, Screeners, Account, Index pages |

Second capture used enhanced Playwright script with full request/response body capture including headers, POST data, and JSON responses. Results in `scripts/rh_full_capture_results.json` (19MB) and `scripts/rh_full_capture_summary.json` (662KB).

### Domains Discovered

| Domain | Endpoints | Purpose |
|--------|-----------|---------|
| `api.robinhood.com` | 108 | Primary REST API (auth, market data, orders, accounts) |
| `bonfire.robinhood.com` | 115 | Enriched UI/chart data, portfolio, search, screeners |
| `dora.robinhood.com` | 6 | News feed, similar instruments **(NEW)** |
| `nummus.robinhood.com` | 5 | Crypto accounts, holdings, portfolios |
| `minerva.robinhood.com` | 1 | Advisory/robo accounts **(NEW)** |

---

## Implementation Status

### Implemented in liljon (v0.1.0+)

Checkmarks indicate endpoints with full client methods, models, and endpoint URL functions.

#### Stocks (`client.stocks`)
- [x] `GET /marketdata/quotes/?symbols=` — quotes by symbol
- [x] `GET /marketdata/quotes/?ids=` — quotes by instrument IDs (batch)
- [x] `GET /marketdata/quotes/{symbol}/` — single quote by symbol
- [x] `GET /marketdata/quotes/{instrument_id}/` — single quote by instrument ID **(NEW)**
- [x] `GET /instruments/` — instrument search
- [x] `GET /instruments/{id}/` — instrument by ID
- [x] `GET /fundamentals/{symbol}/` — fundamentals by symbol
- [x] `GET /marketdata/fundamentals/{instrument_id}/` — fundamentals by ID with session bounds **(NEW)**
- [x] `GET /marketdata/fundamentals/short/v1/` — 52-week fundamentals history **(NEW)**
- [x] `GET /marketdata/historicals/{symbol}/` — historicals by symbol
- [x] `GET /marketdata/historicals/?ids=` — batch historicals by instrument IDs **(NEW)**
- [x] `GET /midlands/news/{symbol}/` — news articles

#### Discovery (`client.discovery`) **(NEW NAMESPACE)**
- [x] `GET /midlands/ratings/{instrument_id}/` — analyst ratings (single)
- [x] `GET /midlands/ratings/?ids=` — analyst ratings (batch)
- [x] `GET /marketdata/hedgefunds/summary/{instrument_id}/` — hedge fund summary & sentiment
- [x] `GET /marketdata/hedgefunds/transactions/{instrument_id}/` — individual hedge fund trades
- [x] `GET /marketdata/insiders/summary/{instrument_id}/` — insider trading summary & sentiment
- [x] `GET /marketdata/insiders/transactions/{instrument_id}/` — individual insider trades
- [x] `GET /instruments/{instrument_id}/shorting/` — short interest, fee, inventory
- [x] `GET /marketdata/equities/summary/robinhood/{instrument_id}/` — daily buy/sell flow
- [x] `GET /marketdata/earnings/?instrument=` — earnings data
- [x] `GET dora:/instruments/similar/{instrument_id}/` — similar instruments
- [x] `GET dora:/feed/instrument/{instrument_id}/` — instrument news feed
- [x] `GET dora:/feed/` — general news feed
- [x] `GET bonfire:/market_indices?keys=` — market index summaries (S&P 500, Nasdaq)
- [x] `GET bonfire:/instruments/chart-bounds/` — chart time bounds (market hours)
- [x] `GET bonfire:/instruments/{id}/etp-details/` — ETF/ETN details (AUM, expense ratio, performance)
- [x] `GET bonfire:/instruments/{id}/nbbo-summary/` — NBBO bid/ask summary
- [x] `GET bonfire:/search/` — unified search (stocks, crypto, lists, futures)

#### Options (`client.options`)
- [x] `GET /options/chains/?equity_instrument_ids=` — chains by equity ID
- [x] `GET /options/chains/{chain_id}/` — chain by ID
- [x] `GET /options/chains/{chain_id}/collateral/` — collateral requirements **(NEW)**
- [x] `GET /options/instruments/` — option instruments
- [x] `GET /options/instruments/{id}/` — option instrument by ID
- [x] `GET /marketdata/options/{id}/` — single option market data
- [x] `GET /marketdata/options/?ids=` — batch option market data **(NEW)**
- [x] `GET /marketdata/options/strategy/quotes/` — strategy-level quotes with greeks **(NEW)**
- [x] `GET /options/positions/` — option positions
- [x] `GET /options/aggregate_positions/` — aggregated positions by strategy **(NEW)**
- [x] `GET /options/strategies/` — strategy definitions/pricing **(NEW)**
- [x] `GET /options/events/` — option events (expirations, assignments) **(NEW)**
- [x] `GET /options/orders/` — option order history
- [x] `GET /options/profit_and_loss_chart/` — P&L chart data **(NEW)**
- [x] `GET /options/breakevens/` — breakeven calculations **(NEW)**

#### Account (`client.account`)
- [x] `GET /accounts/` — all accounts
- [x] `GET /accounts/{id}/` — account by ID
- [x] `GET /accounts/{id}/portfolio/` — portfolio by account ID
- [x] `GET /portfolios/{account_number}/` — portfolio by account number **(NEW)**
- [x] `GET /phoenix/accounts/unified/` — Phoenix unified account
- [x] `GET /positions/` — stock positions
- [x] `GET /midlands/lists/default/` — default watchlist
- [x] `GET /midlands/lists/` — all watchlists
- [x] `POST /midlands/lists/items/` — watchlist add/remove
- [x] `GET /dividends/` — dividend history
- [x] `GET /user/` — current user profile **(NEW)**
- [x] `GET /subscription/subscriptions/` — active subscriptions (Gold, etc.) **(NEW)**
- [x] `GET /accounts/sweeps/interest/` — cash sweep interest rates **(NEW)**
- [x] `GET /accounts/stock_loan_payments/` — stock lending income **(NEW)**
- [x] `GET /pluto/historical_activities/` — historical activities (trades, dividends) **(NEW)**
- [x] `GET bonfire:/portfolio/account/{acct}/live` — live portfolio real-time values **(NEW)**
- [x] `GET bonfire:/portfolio/performance/{acct}` — portfolio performance chart data **(NEW)**
- [x] `GET bonfire:/accounts/{acct}/instrument_buying_power/{id}/` — buying power per instrument **(NEW)**

#### Orders (`client.orders`)
- [x] `POST /orders/` — place stock order
- [x] `POST /orders/{id}/cancel/` — cancel stock order
- [x] `GET /orders/` — stock order history
- [x] `GET /orders/{id}/` — stock order by ID
- [x] `GET /orders/session/` — session order behavior (market hours) **(NEW)**
- [x] `GET /combo/orders/` — combo/multi-leg orders **(NEW)**
- [x] `POST /orders/fees/` — calculate order fees before placing **(NEW)**

#### Crypto (`client.crypto`)
- [x] `GET nummus:/currency_pairs/` — crypto pairs
- [x] `GET nummus:/currency_pairs/{id}/` — crypto pair by ID
- [x] `GET /marketdata/forex/quotes/{id}/` — crypto quote
- [x] `GET nummus:/holdings/` — crypto holdings
- [x] `GET /marketdata/forex/historicals/{id}/` — crypto historicals

#### Futures (`client.futures`)
- [x] `GET /arsenal/v1/futures/contracts/` — contracts
- [x] `GET /arsenal/v1/futures/contracts/{id}/` — contract by ID
- [x] `GET /arsenal/v1/futures/products/{id}` — product metadata/specs **(NEW)**
- [x] `GET /marketdata/futures/quotes/v1/` — quotes
- [x] `GET /marketdata/futures/quotes/v1/{id}/` — single quote
- [x] `GET /marketdata/futures/closes/v1/` — previous close prices **(NEW)**
- [x] `GET /marketdata/futures/closesrange/v1/` — historical close range **(NEW)**
- [x] `GET /ceres/v1/accounts/` — futures accounts
- [x] `GET /ceres/v1/orders/` — futures orders
- [x] `GET /ceres/v1/orders/{id}/` — futures order by ID
- [x] `GET /ceres/v1/user_settings` — futures user settings **(NEW)**
- [x] `GET /ceres/v1/accounts/{id}/pnl_cost_basis` — futures P&L and cost basis **(NEW)**
- [x] `GET /ceres/v1/accounts/{id}/aggregated_positions` — aggregated positions **(NEW)**

#### Indexes (`client.indexes`)
- [x] `GET /indexes/` — all indexes
- [x] `GET /indexes/{id}/` — index by ID
- [x] `GET /marketdata/indexes/values/v1/` — index values
- [x] `GET /marketdata/indexes/fundamentals/v1/` — index fundamentals
- [x] `GET /marketdata/indexes/closes/v1/` — index closes

#### Markets (`client.markets`)
- [x] `GET /markets/` — markets
- [x] `GET /markets/{code}/hours/{date}/` — market hours
- [x] `GET /midlands/movers/sp500/` — S&P 500 movers

#### Screeners (`client.screeners`)
- [x] `GET bonfire:/screeners` — all screeners
- [x] `GET bonfire:/screeners/presets/` — preset screeners
- [x] `GET bonfire:/screeners/{id}/` — screener by ID
- [x] `GET bonfire:/screeners/indicators/` — available indicators
- [x] `POST bonfire:/screeners/scan/` — execute screener scan

---

### Not Implemented — Captured but Low Priority

These endpoints were captured but intentionally not implemented because they are UI-specific, analytics, or low-value for programmatic use.

#### Internal / Feature Flags / Analytics
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/kaizen/experiments/{id}/` | A/B test experiment flags |
| GET | `/hippo/ux-flags` | UX feature flags |
| GET | `/pathfinder/issues/` | Support issues |
| GET | `/pathfinder/support_chats/` | Support chat sessions |
| GET | `/pathfinder/concierge/plus/status/` | Concierge status |
| GET | `/inbox/notifications/badge` | Notification badge count |
| GET | `/inbox/threads/` | Message threads |
| GET | `/midlands/notifications/stack/` | Notification stack |
| POST | `/midlands/notifications/stack/{id}/impression/` | Mark notification seen |
| GET | `/wonka/promotions/upsell_configs/BADGE` | Promotion configs |
| GET | `/settings/education_state/{acct}/` | Education state |

#### Bonfire UI/UX Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `bonfire:/region` | User region/locale |
| GET | `bonfire:/gold/pill` | Gold subscription pill UI |
| GET | `bonfire:/gold/sweep_flow_splash/` | Gold sweep splash |
| GET | `bonfire:/recurring_schedules/` | Recurring investment schedules |
| GET | `bonfire:/recurring_tradability/equity/{id}/` | Recurring tradability |
| GET | `bonfire:/recurring_trade_logs/` | Recurring trade logs |
| GET | `bonfire:/rewards/sdp_referral/card/{id}` | Referral reward cards |
| GET | `bonfire:/equity_trading/order_type_selector/{side}/` | Order type selector UI |
| POST | `bonfire:/equity_trading/orders/checks/` | Pre-order validation checks |
| GET | `bonfire:/feature-discovery/features/` | Feature discovery cards |
| GET | `bonfire:/education/tool_tips` | Educational tooltips |
| GET | `bonfire:/education/tour/` | Feature tours |
| GET | `bonfire:/sdui/info_sheet/` | Server-driven UI info sheets |
| GET | `bonfire:/slip/eligibility/` | Stock lending eligibility |
| GET | `bonfire:/slip/updated-agreements-required/` | Stock lending agreements |
| GET | `bonfire:/tax_info/instrument/{id}/withholding_status/` | Tax withholding |
| GET | `bonfire:/psp/eligible_programs` | Eligible promotional programs |
| GET | `bonfire:/psp/gifts/history/` | Gift stock history |
| GET | `bonfire:/questionnaire/` | Investment questionnaire |
| GET | `bonfire:/onboarding/resume_application_enabled/` | Onboarding resume |
| GET | `bonfire:/app-comms/surface/*` | Status banners, alerts, hero cards |
| POST | `bonfire:/app-comms/receipt/seen/{id}/` | Mark app comm as seen |
| GET | `bonfire:/options/should_show_options_upgrade_on_sdp/` | Options upgrade prompt |
| GET | `bonfire:/options/simulated/today_total_return/` | Simulated options returns |
| GET | `bonfire:/instruments/{id}/disclosures/` | Regulatory disclosures |
| GET | `bonfire:/instruments/{id}/margin-requirements/` | Margin requirements |
| GET | `bonfire:/instruments/{id}/v2/warnings/` | Trading warnings |
| GET | `bonfire:/instruments/{id}/qa/event-info/` | Q&A event info |
| GET | `bonfire:/instruments/spans/` | Available chart span options |
| GET | `bonfire:/instruments/stock-advanced-chart-config/` | Advanced chart config |
| GET | `bonfire:/investment_profile_settings/profile/` | Investment profile |
| GET | `bonfire:/lists/{id}/disclosures/` | List disclosures |
| GET | `bonfire:/margin/{acct}/settings/` | Margin settings (endpoint exists but not high-value) |
| GET | `bonfire:/margin/{acct}/eligibility` | Margin eligibility |
| GET | `bonfire:/portfolio/{acct}/positions_v2` | Enriched positions (SDUI format) |
| GET | `bonfire:/portfolio/acats/bonus-promo-info/` | ACATS bonus info |
| GET | `bonfire:/portfolio/performance/{acct}/settings_v2/` | Performance chart settings |
| GET | `bonfire:/rhy/accounts/` | Robinhood Yield accounts |
| GET | `bonfire:/account_switcher/*` | Account switcher UI |
| GET | `bonfire:/home/account_switcher/v2` | Home account switcher |

#### Options Product Onboarding
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/options-product/onboarding/next_screens` | Options onboarding flow |
| POST | `/options-product/onboarding/update_suitability_info` | Update options suitability |
| GET | `/options-product/simulated-returns/` | Simulated returns |
| GET | `/options-product/tooltips/odp/` | Options tooltips |
| GET | `/options/option_settings/{acct}/` | Options settings per account |
| GET | `/options/corp_actions/` | Options corporate actions |
| GET | `/options/fees/` | Options fee calculation |

#### Corporate Actions / Misc
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/corp_actions/adr_fees/` | ADR fee charges |
| GET | `/corp_actions/v2/split_payments/` | Stock split payments |
| GET | `/accounts/{id}/day_trade_checks/` | Day trade check |
| GET | `/orders/calculate_expiration/` | Order expiration calculation |
| GET | `/midlands/notification_settings/instruments/{id}/` | Notification settings |
| PATCH | `/midlands/notification_settings/instruments/{id}/` | Update notification settings |

#### Nummus (Crypto) Extended
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `nummus:/accounts/` | Crypto accounts |
| GET | `nummus:/portfolios/{id}/` | Crypto portfolio by ID |
| GET | `nummus:/activations/` | Crypto activation status |

#### New Domain: minerva.robinhood.com
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `minerva:/accounts/` | Advisory/robo accounts (empty for non-advisory users) |

#### New Domain: dora.robinhood.com (partially implemented)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `dora:/feed/` | General news feed (implemented) |
| GET | `dora:/feed/instrument/{id}/` | Instrument news feed (implemented) |
| GET | `dora:/instruments/similar/{id}/` | Similar instruments (implemented) |

---

## Response Shape Reference

Key response shapes captured with full JSON bodies. See `scripts/rh_full_capture_summary.json` for all 235 endpoints.

### Short Interest (`/instruments/{id}/shorting/`)
```json
{
  "instrument_id": "740de869-...",
  "fee": "0.0000",
  "fee_timestamp": "2026-03-02T22:00:00Z",
  "inventory_range": ">1M",
  "daily_fee": "0.0000"
}
```

### Hedge Fund Summary (`/marketdata/hedgefunds/summary/{id}/`)
```json
{
  "instrument_id": "a4ecd608-...",
  "sentiment_score": "Positive Sentiment",
  "quarterly_aggregate_transactions": [
    {"date": "2024-03-31", "total_shares_held": 248815020, "shares_bought": 11783930, "shares_sold": 59961800}
  ]
}
```

### Hedge Fund Transactions (`/marketdata/hedgefunds/transactions/{id}/`)
```json
{
  "instrument_id": "a4ecd608-...",
  "detailed_transactions": [
    {"manager_name": "Ken Fisher", "institution_name": "Fisher Asset Management LLC",
     "portfolio_percentage": 5.5, "change_percentage": 1.77, "action": "Added",
     "market_value": 16049730650, "total_shares": 86057537, "shares_traded": 1493962}
  ]
}
```

### Insider Summary (`/marketdata/insiders/summary/{id}/`)
```json
{
  "instrument_id": "a4ecd608-...",
  "sentiment_score": "Negative Sentiment",
  "monthly_aggregate_transactions": [
    {"date": "2025-06-01", "shares_bought": 21588, "shares_sold": 4785391,
     "buy_transactions": 12, "sell_transactions": 20}
  ]
}
```

### Insider Transactions (`/marketdata/insiders/transactions/{id}/`)
```json
{
  "instrument_id": "a4ecd608-...",
  "detailed_transactions": [
    {"name": "Colette Kress", "position": "EVP & CFO", "transaction_type": "Uninformative Sell",
     "amount": 8371082.36, "number_of_shares": 47640, "date": "2026-02-06"}
  ]
}
```

### Equity Summary (`/marketdata/equities/summary/robinhood/{id}/`)
```json
{
  "instrument_id": "a4ecd608-...",
  "daily_transactions": [
    {"date": "2026-02-02", "net_buy_percentage": 3.44, "net_sell_percentage": -3.44,
     "buy_volume_percentage_change": null, "sell_volume_percentage_change": null}
  ]
}
```

### Strategy Quotes (`/marketdata/options/strategy/quotes/`)
```json
{
  "adjusted_mark_price": "5.430000", "ask_price": "5.600000", "bid_price": "5.250000",
  "break_even_price": "65.430000", "delta": "0.403679", "gamma": "0.014753",
  "implied_volatility": "0.703260", "theta": "-0.016970", "vega": "0.144545",
  "chance_of_profit_long": "0.150799", "open_interest": 2542, "volume": 750
}
```

### Similar Instruments (`dora:/instruments/similar/{id}/`)
```json
{
  "id": "740de869-...",
  "similar": [
    {"symbol": "GLD", "instrument_id": "90999f47-...", "name": "SPDR Gold Trust",
     "simple_name": "SPDR Gold Trust", "tags": [{"name": "ETF", "slug": "etf"}]}
  ]
}
```

### Market Indices (`bonfire:/market_indices`)
```json
{
  "indicators": [
    {"key": "sp_500", "value": "6881.62", "percent_change": "0.04"}
  ]
}
```

### ETP Details (`bonfire:/instruments/{id}/etp-details/`)
```json
{
  "instrument_id": "740de869-...", "symbol": "SLV", "aum": "46246496323.000000",
  "gross_expense_ratio": "0.500000", "nav": "81.505990", "category": "Commodities Focused",
  "total_holdings": 1, "inception_date": "2006-04-21", "index_tracked": "LBMA Silver Price USD",
  "quarter_end_performance": {"market": {"1Y": "144.66", "5Y": "21.26"}, "nav": {"1Y": "147.86"}}
}
```

### Live Portfolio (`bonfire:/portfolio/account/{acct}/live`)
```json
{
  "deposit_adjusted_market_value": "4.94", "equity_market_value": "4.94",
  "forex_market_value": "0", "futures_market_value": "0", "option_market_value": "0",
  "cash": "0", "brokerage_cash": "0", "pending_deposits": "0", "margin_used": "0",
  "account_number": "937525228", "currency": "USD"
}
```

### User Profile (`/user/`)
```json
{
  "id": "3c676dca-...", "username": "awww_yeah", "email": "jeff.chappo@gmail.com",
  "first_name": "Jeffery", "last_name": "Chappo", "profile_name": "awww_yeah",
  "created_at": "2026-01-15T05:16:41.493829-05:00"
}
```

### Sweep Interest (`/accounts/sweeps/interest/`)
```json
{
  "interest_rate": "0.00", "non_gold_interest_rate": "0.00",
  "gold_interest_rate": "3.35", "gold_boosted_rate": "3.75",
  "gold_boosted_high_rate": "3.85"
}
```

---

## Implementation Summary

### What's New in This Update (2026-03-02)

**New API namespace: `client.discovery`** — 17 methods covering analyst ratings, hedge fund activity, insider trading, short interest, equity flow, earnings, similar instruments, market indices, chart bounds, ETP details, NBBO, and search.

**Extended `client.stocks`** — 4 new methods: `get_quote_by_id()`, `get_fundamentals_by_id()`, `get_fundamentals_history()`, `get_historicals_by_ids()`.

**Extended `client.options`** — 8 new methods: `get_aggregate_positions()`, `get_strategies()`, `get_chain_collateral()`, `get_events()`, `get_market_data_batch()`, `get_strategy_quotes()`, `get_pnl_chart()`, `get_breakevens()`.

**Extended `client.account`** — 8 new methods: `get_portfolio_by_number()`, `get_user()`, `get_subscriptions()`, `get_live_portfolio()`, `get_portfolio_performance()`, `get_sweep_interest()`, `get_stock_loan_payments()`, `get_historical_activities()`, `get_instrument_buying_power()`.

**Extended `client.orders`** — 3 new methods: `get_order_session()`, `get_combo_orders()`, `calculate_fees()`.

**Extended `client.futures`** — 6 new methods: `get_product()`, `get_closes()`, `get_closes_range()`, `get_user_settings()`, `get_pnl_cost_basis()`, `get_aggregated_positions()`.

**New Pydantic models** (25+): `ShortInterest`, `HedgeFundSummary`, `HedgeFundTransactions`, `HedgeFundTransaction`, `InsiderSummary`, `InsiderTransactions`, `InsiderTransaction`, `AnalystRating`, `EquitySummary`, `Earnings`, `SimilarInstruments`, `SimilarInstrument`, `MarketIndex`, `ChartBounds`, `EtpDetails`, `NbboSummary`, `UserProfile`, `Subscription`, `LivePortfolio`, `SweepInterest`.

**New endpoint URL functions**: 50+ new functions in `_endpoints.py` including new `DORA_BASE` domain.

**New domain**: `dora.robinhood.com` — discovered for news feeds and similar instrument recommendations.

**Total endpoints**: 57 new endpoint URL functions added. Combined with existing, liljon now covers ~120 endpoint patterns across 5 Robinhood API domains.
