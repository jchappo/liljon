"""Robinhood CLI — interactive testing tool for the Robinhood client library.

Usage:
    uv run python -m liljon auth status
    uv run python -m liljon stocks quote AAPL MSFT
    uv run python -m liljon --json account positions
"""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from functools import wraps
from typing import Any, AsyncIterator

import click
from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from liljon.client import RobinhoodClient
from liljon.exceptions import (
    AuthenticationError,
    ChallengeRequiredError,
    InvalidSymbolError,
    NotAuthenticatedError,
    OrderError,
    RateLimitError,
    RobinhoodError,
)

console = Console()

# ── Output Helpers ────────────────────────────────────────────────────────────


def _is_uuid(value: str) -> bool:
    """Return True if value looks like a UUID (8-4-4-4-12 hex pattern)."""
    import re
    return bool(re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", value, re.IGNORECASE))


def _format_value(v: Any) -> str:
    """Format a value for display in tables/panels."""
    if v is None:
        return "-"
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, Decimal):
        return f"{v:,.4f}".rstrip("0").rstrip(".")
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, (dict, list)):
        return json.dumps(v, default=str, indent=2)
    return str(v)


def model_table(
    items: list[BaseModel],
    columns: list[tuple[str, str]],
    title: str = "",
) -> Table:
    """Build a rich Table from a list of Pydantic models.

    columns: list of (field_name, display_header) tuples.
    """
    table = Table(title=title, show_lines=False)
    for _, header in columns:
        table.add_column(header, overflow="fold")
    for item in items:
        row = []
        for field, _ in columns:
            val = getattr(item, field, None)
            row.append(_format_value(val))
        table.add_row(*row)
    return table


def model_panel(item: BaseModel, title: str = "", fields: list[str] | None = None) -> Panel:
    """Render a single Pydantic model as a key-value panel."""
    data = item.model_dump()
    if fields:
        data = {k: v for k, v in data.items() if k in fields}
    lines = []
    for key, val in data.items():
        label = key.replace("_", " ").title()
        lines.append(f"[bold]{label}:[/bold] {_format_value(val)}")
    return Panel("\n".join(lines), title=title, expand=False)


def dict_table(items: list[dict[str, Any]], columns: list[tuple[str, str]], title: str = "") -> Table:
    """Build a rich Table from a list of dicts."""
    table = Table(title=title, show_lines=False)
    for _, header in columns:
        table.add_column(header, overflow="fold")
    for item in items:
        row = []
        for field, _ in columns:
            row.append(_format_value(item.get(field)))
        table.add_row(*row)
    return table


def dict_panel(data: dict[str, Any], title: str = "") -> Panel:
    """Render a dict as a key-value panel."""
    lines = []
    for key, val in data.items():
        label = key.replace("_", " ").title()
        lines.append(f"[bold]{label}:[/bold] {_format_value(val)}")
    return Panel("\n".join(lines), title=title, expand=False)


def output_json(data: Any) -> None:
    """Print raw JSON to stdout."""
    if isinstance(data, list):
        items = [item.model_dump() if isinstance(item, BaseModel) else item for item in data]
        click.echo(json.dumps(items, default=str, indent=2))
    elif isinstance(data, BaseModel):
        click.echo(json.dumps(data.model_dump(), default=str, indent=2))
    elif isinstance(data, dict):
        click.echo(json.dumps(data, default=str, indent=2))
    else:
        click.echo(json.dumps(data, default=str, indent=2))


# ── Auth Helpers ──────────────────────────────────────────────────────────────


@asynccontextmanager
async def get_authenticated_client() -> AsyncIterator[RobinhoodClient]:
    """Create a client, restore session or do interactive login, then yield it."""
    async with RobinhoodClient() as client:
        if await client.try_restore_session():
            yield client
            return

        console.print("[yellow]No cached session. Starting interactive login...[/yellow]")
        username = Prompt.ask("Username (email)")
        password = Prompt.ask("Password", password=True)

        result = await client.login(username, password)

        if result.status == "challenge_required":
            challenge = result.challenge
            assert challenge is not None
            console.print(f"[cyan]2FA required ({challenge.challenge_type}). Check your device.[/cyan]")
            code = Prompt.ask("Verification code")
            result = await client.submit_verification(code)

        if result.status != "logged_in":
            raise click.ClickException(f"Login failed: {result.message}")

        console.print(f"[green]Logged in as {result.username}[/green]")
        yield client


async def _resolve_instrument_id(client: RobinhoodClient, symbol_or_id: str) -> str:
    """Resolve a symbol or instrument UUID to an instrument ID."""
    if _is_uuid(symbol_or_id):
        return symbol_or_id
    inst = await client.stocks.get_instrument_by_symbol(symbol_or_id.upper())
    if not inst.id:
        raise click.ClickException(f"Could not resolve instrument ID for '{symbol_or_id}'")
    return inst.id


async def _resolve_account_id(client: RobinhoodClient) -> str:
    """Get the account number, fetching from API if needed."""
    account_number = client.get_account_number()
    if account_number:
        return account_number
    accounts = await client.account.get_accounts()
    if not accounts:
        raise click.ClickException("No accounts found")
    account_number = accounts[0].account_number
    if not account_number:
        raise click.ClickException("Account has no account number")
    client.set_account_number(account_number)
    return account_number


# ── Async → Click Bridge ─────────────────────────────────────────────────────


def async_command(fn):
    """Decorator: wraps an async function so click can invoke it synchronously."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        return asyncio.run(fn(*args, **kwargs))

    return wrapper


# ── Error Handler ─────────────────────────────────────────────────────────────


def handle_errors(fn):
    """Decorator: catches RobinhoodError subtypes and maps to click.ClickException."""

    @wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except NotAuthenticatedError:
            raise click.ClickException("Not authenticated. Run 'auth login' first.")
        except ChallengeRequiredError as e:
            raise click.ClickException(f"2FA challenge required ({e.challenge_type}). Use 'auth login'.")
        except InvalidSymbolError as e:
            raise click.ClickException(f"Invalid symbol: {e.symbol}")
        except RateLimitError as e:
            msg = f"Rate limited on {e.url}"
            if e.retry_after:
                msg += f" (retry after {e.retry_after}s)"
            raise click.ClickException(msg)
        except OrderError as e:
            raise click.ClickException(f"Order error: {e}")
        except AuthenticationError as e:
            raise click.ClickException(f"Authentication error: {e}")
        except RobinhoodError as e:
            raise click.ClickException(f"Robinhood error: {e}")

    return wrapper


# ── Top-Level Group ───────────────────────────────────────────────────────────


@click.group()
@click.option("--json", "use_json", is_flag=True, default=False, help="Output raw JSON instead of formatted tables.")
@click.pass_context
def cli(ctx: click.Context, use_json: bool) -> None:
    """Robinhood CLI — test and interact with the Robinhood API."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = use_json


def _use_json(ctx: click.Context) -> bool:
    return ctx.obj.get("json", False)


# ══════════════════════════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════════════════════════


@cli.group()
def auth():
    """Authentication commands."""


@auth.command()
@click.pass_context
@async_command
@handle_errors
async def login(ctx: click.Context):
    """Interactive login (tries cached session first)."""
    async with get_authenticated_client() as client:
        account_id = await _resolve_account_id(client)
        if _use_json(ctx):
            output_json({"status": "logged_in", "account_number": account_id, "authenticated": True})
        else:
            console.print(f"[green]Authenticated.[/green] Account: {account_id}")


@auth.command()
@click.pass_context
@async_command
@handle_errors
async def status(ctx: click.Context):
    """Show auth status, username, token expiry."""
    async with RobinhoodClient() as client:
        restored = await client.try_restore_session()
        if not restored:
            if _use_json(ctx):
                output_json({"authenticated": False})
            else:
                console.print("[red]Not authenticated.[/red] Run 'auth login' to connect.")
            return

        token_data = client._auth.token_data
        info = {
            "authenticated": True,
            "username": token_data.username if token_data else None,
            "account_number": client.get_account_number(),
            "expires_at": str(token_data.expires_at) if token_data and token_data.expires_at else None,
            "token_cache": str(client._token_cache.path),
        }
        if _use_json(ctx):
            output_json(info)
        else:
            console.print(dict_panel(info, title="Auth Status"))


@auth.command()
@click.pass_context
@async_command
@handle_errors
async def logout(ctx: click.Context):
    """Clear session and token cache."""
    async with RobinhoodClient() as client:
        await client.logout()
        if _use_json(ctx):
            output_json({"status": "logged_out"})
        else:
            console.print("[green]Logged out. Token cache cleared.[/green]")


# ══════════════════════════════════════════════════════════════════════════════
#  STOCKS
# ══════════════════════════════════════════════════════════════════════════════


@cli.group()
def stocks():
    """Stock quotes, fundamentals, historicals, news."""


@stocks.command()
@click.argument("symbols", nargs=-1, required=True)
@click.pass_context
@async_command
@handle_errors
async def quote(ctx: click.Context, symbols: tuple[str, ...]):
    """Real-time stock quotes."""
    async with get_authenticated_client() as client:
        quotes = await client.stocks.get_quotes(list(symbols))
        if _use_json(ctx):
            output_json(quotes)
        else:
            cols = [
                ("symbol", "Symbol"),
                ("last_trade_price", "Last"),
                ("bid_price", "Bid"),
                ("ask_price", "Ask"),
                ("previous_close", "Prev Close"),
                ("trading_halted", "Halted"),
                ("updated_at", "Updated"),
            ]
            console.print(model_table(quotes, cols, title="Stock Quotes"))


@stocks.command()
@click.argument("symbol")
@click.pass_context
@async_command
@handle_errors
async def fundamentals(ctx: click.Context, symbol: str):
    """Fundamentals: PE, market cap, sector, etc."""
    async with get_authenticated_client() as client:
        data = await client.stocks.get_fundamentals(symbol.upper())
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(model_panel(data, title=f"Fundamentals — {symbol.upper()}"))


@stocks.command()
@click.argument("symbol")
@click.pass_context
@async_command
@handle_errors
async def instrument(ctx: click.Context, symbol: str):
    """Instrument metadata for a symbol."""
    async with get_authenticated_client() as client:
        data = await client.stocks.get_instrument_by_symbol(symbol.upper())
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(model_panel(data, title=f"Instrument — {symbol.upper()}"))


@stocks.command()
@click.argument("symbols", nargs=-1, required=True)
@click.option("--interval", default="day", help="Interval: 5minute, 10minute, hour, day, week.")
@click.option("--span", default="year", help="Span: day, week, month, 3month, year, 5year.")
@click.option("--bounds", default="regular", help="Session: regular, extended, trading, 24_5.")
@click.option("--last", type=int, default=None, help="Show only last N bars.")
@click.pass_context
@async_command
@handle_errors
async def historicals(ctx: click.Context, symbols: tuple[str, ...], interval: str, span: str, bounds: str, last: int | None):
    """OHLCV historical bars."""
    async with get_authenticated_client() as client:
        result = await client.stocks.get_historicals(list(symbols), interval=interval, span=span, bounds=bounds)
        if _use_json(ctx):
            output_json(result)
        else:
            cols = [
                ("begins_at", "Date"),
                ("open_price", "Open"),
                ("high_price", "High"),
                ("low_price", "Low"),
                ("close_price", "Close"),
                ("volume", "Volume"),
            ]
            for sym, bars in result.items():
                if last:
                    bars = bars[-last:]
                console.print(model_table(bars, cols, title=f"Historicals — {sym} ({interval}/{span})"))


@stocks.command()
@click.argument("symbol", required=False, default=None)
@click.option("--limit", type=int, default=10, help="Max articles to show.")
@click.pass_context
@async_command
@handle_errors
async def news(ctx: click.Context, symbol: str | None, limit: int):
    """News articles for a symbol, or market-wide news if no symbol given."""
    async with get_authenticated_client() as client:
        articles = await client.stocks.get_news(symbol.upper() if symbol else None)
        articles = articles[:limit]
        if _use_json(ctx):
            output_json(articles)
        else:
            cols = [
                ("published_at", "Published"),
                ("source", "Source"),
                ("title", "Title"),
            ]
            title = f"News — {symbol.upper()}" if symbol else "News — Market"
            console.print(model_table(articles, cols, title=title))


@stocks.command("quote-by-ids")
@click.argument("instrument_ids", nargs=-1, required=True)
@click.pass_context
@async_command
@handle_errors
async def quote_by_ids(ctx: click.Context, instrument_ids: tuple[str, ...]):
    """Quotes by instrument IDs."""
    async with get_authenticated_client() as client:
        quotes = await client.stocks.get_quotes_by_ids(list(instrument_ids))
        if _use_json(ctx):
            output_json(quotes)
        else:
            cols = [
                ("symbol", "Symbol"),
                ("last_trade_price", "Last"),
                ("bid_price", "Bid"),
                ("ask_price", "Ask"),
                ("previous_close", "Prev Close"),
                ("trading_halted", "Halted"),
                ("updated_at", "Updated"),
            ]
            console.print(model_table(quotes, cols, title="Quotes by ID"))


@stocks.command()
@click.argument("symbols", nargs=-1, required=True)
@click.pass_context
@async_command
@handle_errors
async def price(ctx: click.Context, symbols: tuple[str, ...]):
    """Quick latest price for symbols."""
    async with get_authenticated_client() as client:
        prices = await client.stocks.get_latest_price(list(symbols))
        if _use_json(ctx):
            output_json(prices)
        else:
            table = Table(title="Latest Prices")
            table.add_column("Symbol")
            table.add_column("Price")
            for sym, px in prices.items():
                table.add_row(sym, _format_value(Decimal(px)) if px else "-")
            console.print(table)


@stocks.command("fundamentals-by-id")
@click.argument("instrument_id")
@click.pass_context
@async_command
@handle_errors
async def fundamentals_by_id(ctx: click.Context, instrument_id: str):
    """Fundamentals by instrument ID."""
    async with get_authenticated_client() as client:
        data = await client.stocks.get_fundamentals_by_id(instrument_id)
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(model_panel(data, title=f"Fundamentals — {instrument_id[:8]}..."))


@stocks.command("fundamentals-history")
@click.argument("instrument_ids", nargs=-1, required=True)
@click.option("--start-date", default=None, help="Start date (YYYY-MM-DD).")
@click.pass_context
@async_command
@handle_errors
async def fundamentals_history(ctx: click.Context, instrument_ids: tuple[str, ...], start_date: str | None):
    """52-week fundamentals history for instrument IDs."""
    async with get_authenticated_client() as client:
        data = await client.stocks.get_fundamentals_history(list(instrument_ids), start_date=start_date)
        if _use_json(ctx):
            output_json(data)
        else:
            for item in data:
                inner = item.get("data", item)
                symbol = inner.get("symbol", "?")
                daily = inner.get("daily_data", [])
                console.print(f"\n[bold]{symbol}[/bold] — {len(daily)} data points")
                if daily:
                    last = daily[-1] if isinstance(daily[-1], dict) else {}
                    console.print(f"  Latest: {json.dumps(last, default=str)[:200]}")


# ══════════════════════════════════════════════════════════════════════════════
#  ACCOUNT
# ══════════════════════════════════════════════════════════════════════════════


@cli.group()
def account():
    """Account info, portfolio, positions, watchlists, dividends."""


@account.command()
@click.pass_context
@async_command
@handle_errors
async def info(ctx: click.Context):
    """Account profile (buying power, cash, etc.)."""
    async with get_authenticated_client() as client:
        account_id = await _resolve_account_id(client)
        data = await client.account.get_account(account_id)
        if _use_json(ctx):
            output_json(data)
        else:
            fields = [
                "account_number", "type", "state", "buying_power",
                "cash", "cash_held_for_orders", "uncleared_deposits", "sma",
            ]
            console.print(model_panel(data, title="Account Info", fields=fields))


@account.command()
@click.pass_context
@async_command
@handle_errors
async def portfolio(ctx: click.Context):
    """Portfolio P&L (equity, market value)."""
    async with get_authenticated_client() as client:
        account_id = await _resolve_account_id(client)
        data = await client.account.get_portfolio(account_id)
        if _use_json(ctx):
            output_json(data)
        else:
            fields = [
                "equity", "extended_hours_equity", "market_value",
                "extended_hours_market_value", "last_core_equity",
                "last_core_market_value", "withdrawable_amount",
                "excess_margin", "excess_maintenance", "start_date",
            ]
            console.print(model_panel(data, title="Portfolio", fields=fields))


@account.command()
@click.pass_context
@async_command
@handle_errors
async def positions(ctx: click.Context):
    """Open stock positions with qty/avg cost."""
    async with get_authenticated_client() as client:
        data = await client.account.get_positions(nonzero=True)
        if _use_json(ctx):
            output_json(data)
        else:
            cols = [
                ("symbol", "Symbol"),
                ("quantity", "Qty"),
                ("average_buy_price", "Avg Cost"),
                ("intraday_quantity", "Intraday Qty"),
                ("shares_held_for_sells", "Held (Sells)"),
                ("created_at", "Opened"),
            ]
            console.print(model_table(data, cols, title="Open Positions"))


@account.command()
@click.pass_context
@async_command
@handle_errors
async def watchlists(ctx: click.Context):
    """All watchlists with symbols."""
    async with get_authenticated_client() as client:
        data = await client.account.get_watchlists()
        if _use_json(ctx):
            output_json(data)
        else:
            for wl in data:
                name = wl.display_name or wl.name or "Unnamed"
                symbols = [item.symbol or item.instrument_id or "?" for item in wl.items]
                console.print(f"\n[bold]{name}[/bold] ({len(symbols)} items)")
                if symbols:
                    console.print("  " + ", ".join(symbols))


@account.command("watchlist-create")
@click.argument("name")
@click.pass_context
@async_command
@handle_errors
async def watchlist_create(ctx: click.Context, name: str):
    """Create a new watchlist."""
    async with get_authenticated_client() as client:
        wl = await client.account.create_watchlist(name)
        if _use_json(ctx):
            output_json(wl)
        else:
            display = wl.display_name or wl.name or name
            console.print(f"[green]Created watchlist '{display}'[/green]")


@account.command("watchlist-add")
@click.argument("symbols", nargs=-1, required=True)
@click.option("--name", default="My First List", help="Watchlist name.")
@click.pass_context
@async_command
@handle_errors
async def watchlist_add(ctx: click.Context, symbols: tuple[str, ...], name: str):
    """Add symbols to a watchlist."""
    async with get_authenticated_client() as client:
        result = await client.account.add_symbols_to_watchlist(list(symbols), name=name)
        if _use_json(ctx):
            output_json(result)
        else:
            console.print(f"[green]Added {', '.join(symbols)} to '{name}'[/green]")


@account.command("watchlist-remove")
@click.argument("symbols", nargs=-1, required=True)
@click.option("--name", default="My First List", help="Watchlist name.")
@click.pass_context
@async_command
@handle_errors
async def watchlist_remove(ctx: click.Context, symbols: tuple[str, ...], name: str):
    """Remove symbols from a watchlist."""
    async with get_authenticated_client() as client:
        result = await client.account.remove_symbols_from_watchlist(list(symbols), name=name)
        if _use_json(ctx):
            output_json(result)
        else:
            console.print(f"[green]Removed {', '.join(symbols)} from '{name}'[/green]")


@account.command()
@click.pass_context
@async_command
@handle_errors
async def dividends(ctx: click.Context):
    """Dividend history."""
    async with get_authenticated_client() as client:
        data = await client.account.get_dividends()
        if _use_json(ctx):
            output_json(data)
        else:
            cols = [
                ("payable_date", "Payable Date"),
                ("amount", "Amount"),
                ("rate", "Rate"),
                ("position", "Position"),
                ("state", "State"),
                ("withholding", "Withholding"),
            ]
            console.print(model_table(data, cols, title="Dividends"))


@account.command()
@click.pass_context
@async_command
@handle_errors
async def user(ctx: click.Context):
    """Current user profile."""
    async with get_authenticated_client() as client:
        data = await client.account.get_user()
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(model_panel(data, title="User Profile"))


@account.command("subscriptions")
@click.pass_context
@async_command
@handle_errors
async def subscriptions(ctx: click.Context):
    """Active subscriptions (Gold, etc.)."""
    async with get_authenticated_client() as client:
        data = await client.account.get_subscriptions()
        if _use_json(ctx):
            output_json(data)
        else:
            if not data:
                console.print("[dim]No active subscriptions.[/dim]")
            else:
                for sub in data:
                    console.print(model_panel(sub, title="Subscription"))


@account.command("live")
@click.pass_context
@async_command
@handle_errors
async def live_portfolio(ctx: click.Context):
    """Live portfolio with real-time market values."""
    async with get_authenticated_client() as client:
        account_number = await _resolve_account_id(client)
        data = await client.account.get_live_portfolio(account_number)
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(model_panel(data, title="Live Portfolio"))


@account.command("performance")
@click.option("--span", default="day", help="Span: day, week, month, 3month, year, 5year, all.")
@click.pass_context
@async_command
@handle_errors
async def performance(ctx: click.Context, span: str):
    """Portfolio performance chart data."""
    async with get_authenticated_client() as client:
        account_number = await _resolve_account_id(client)
        data = await client.account.get_portfolio_performance(account_number, display_span=span)
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(dict_panel(data, title=f"Portfolio Performance ({span})"))


@account.command("sweep-interest")
@click.pass_context
@async_command
@handle_errors
async def sweep_interest(ctx: click.Context):
    """Cash sweep interest rates."""
    async with get_authenticated_client() as client:
        account_number = await _resolve_account_id(client)
        data = await client.account.get_sweep_interest(account_number)
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(model_panel(data, title="Sweep Interest Rates"))


@account.command("activities")
@click.pass_context
@async_command
@handle_errors
async def activities(ctx: click.Context):
    """Historical account activities (trades, dividends, transfers)."""
    async with get_authenticated_client() as client:
        data = await client.account.get_historical_activities()
        if _use_json(ctx):
            output_json(data)
        else:
            if not data:
                console.print("[dim]No historical activities found.[/dim]")
            else:
                for item in data:
                    console.print(dict_panel(item))


@account.command("buying-power")
@click.argument("instrument_id")
@click.pass_context
@async_command
@handle_errors
async def buying_power(ctx: click.Context, instrument_id: str):
    """Buying power for a specific instrument."""
    async with get_authenticated_client() as client:
        account_number = await _resolve_account_id(client)
        data = await client.account.get_instrument_buying_power(account_number, instrument_id)
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(dict_panel(data, title=f"Buying Power — {instrument_id[:8]}..."))


# ══════════════════════════════════════════════════════════════════════════════
#  ORDERS
# ══════════════════════════════════════════════════════════════════════════════


@cli.group()
def orders():
    """Stock orders: list, get, buy, sell, cancel."""


@orders.command("list")
@click.pass_context
@async_command
@handle_errors
async def orders_list(ctx: click.Context):
    """Recent stock orders."""
    async with get_authenticated_client() as client:
        data = await client.orders.get_stock_orders()
        if _use_json(ctx):
            output_json(data)
        else:
            cols = [
                ("id", "Order ID"),
                ("symbol", "Symbol"),
                ("side", "Side"),
                ("type", "Type"),
                ("quantity", "Qty"),
                ("price", "Price"),
                ("state", "State"),
                ("created_at", "Created"),
            ]
            console.print(model_table(data, cols, title="Stock Orders"))


@orders.command("get")
@click.argument("order_id")
@click.pass_context
@async_command
@handle_errors
async def orders_get(ctx: click.Context, order_id: str):
    """Get details for a specific order."""
    async with get_authenticated_client() as client:
        data = await client.orders.get_stock_order(order_id)
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(model_panel(data, title=f"Order — {order_id}"))


@orders.command()
@click.argument("symbol")
@click.argument("qty", type=float)
@click.option("--type", "order_type", default="market", help="Order type: market, limit, stoploss, stoplimit.")
@click.option("--price", type=float, default=None, help="Limit price (required for limit/stoplimit).")
@click.option("--stop-price", type=float, default=None, help="Stop price (required for stoploss/stoplimit).")
@click.option("--tif", default="gfd", help="Time in force: gfd, gtc, ioc, opg.")
@click.option("--confirm", is_flag=True, required=True, help="Required flag to confirm the order.")
@click.pass_context
@async_command
@handle_errors
async def buy(
    ctx: click.Context, symbol: str, qty: float, order_type: str,
    price: float | None, stop_price: float | None, tif: str, confirm: bool,
):
    """Place a buy order."""
    async with get_authenticated_client() as client:
        result = await client.orders.place_stock_order(
            symbol=symbol.upper(),
            quantity=qty,
            side="buy",
            order_type=order_type,
            time_in_force=tif,
            price=price,
            stop_price=stop_price,
        )
        if _use_json(ctx):
            output_json(result)
        else:
            console.print(f"[green]Buy order placed.[/green] ID: {result.id}, State: {result.state}")
            console.print(model_panel(result, title="Order Details"))


@orders.command()
@click.argument("symbol")
@click.argument("qty", type=float)
@click.option("--type", "order_type", default="market", help="Order type: market, limit, stoploss, stoplimit.")
@click.option("--price", type=float, default=None, help="Limit price (required for limit/stoplimit).")
@click.option("--stop-price", type=float, default=None, help="Stop price (required for stoploss/stoplimit).")
@click.option("--tif", default="gfd", help="Time in force: gfd, gtc, ioc, opg.")
@click.option("--confirm", is_flag=True, required=True, help="Required flag to confirm the order.")
@click.pass_context
@async_command
@handle_errors
async def sell(
    ctx: click.Context, symbol: str, qty: float, order_type: str,
    price: float | None, stop_price: float | None, tif: str, confirm: bool,
):
    """Place a sell order."""
    async with get_authenticated_client() as client:
        result = await client.orders.place_stock_order(
            symbol=symbol.upper(),
            quantity=qty,
            side="sell",
            order_type=order_type,
            time_in_force=tif,
            price=price,
            stop_price=stop_price,
        )
        if _use_json(ctx):
            output_json(result)
        else:
            console.print(f"[green]Sell order placed.[/green] ID: {result.id}, State: {result.state}")
            console.print(model_panel(result, title="Order Details"))


@orders.command()
@click.argument("order_id")
@click.option("--confirm", is_flag=True, required=True, help="Required flag to confirm cancellation.")
@click.pass_context
@async_command
@handle_errors
async def cancel(ctx: click.Context, order_id: str, confirm: bool):
    """Cancel a pending stock order."""
    async with get_authenticated_client() as client:
        result = await client.orders.cancel_stock_order(order_id)
        if _use_json(ctx):
            output_json(result)
        else:
            console.print(f"[green]Order {order_id} cancelled.[/green]")


@orders.command("combo")
@click.option("--states", default=None, help="Filter by states (e.g. pending, filled).")
@click.pass_context
@async_command
@handle_errors
async def orders_combo(ctx: click.Context, states: str | None):
    """Combo/multi-leg orders."""
    async with get_authenticated_client() as client:
        data = await client.orders.get_combo_orders(states=states)
        if _use_json(ctx):
            output_json(data)
        else:
            if not data:
                console.print("[dim]No combo orders found.[/dim]")
                return
            cols = [
                ("id", "ID"),
                ("state", "State"),
                ("type", "Type"),
                ("created_at", "Created"),
            ]
            console.print(dict_table(data, cols, title="Combo Orders"))


@orders.command("fees")
@click.argument("instrument_id")
@click.argument("quantity")
@click.argument("price")
@click.argument("side", type=click.Choice(["buy", "sell"]))
@click.option("--otc", is_flag=True, default=False, help="Mark as OTC instrument.")
@click.pass_context
@async_command
@handle_errors
async def orders_fees(ctx: click.Context, instrument_id: str, quantity: str, price: str, side: str, otc: bool):
    """Calculate fees for a stock order before placing it."""
    async with get_authenticated_client() as client:
        data = await client.orders.calculate_fees(
            instrument_id=instrument_id,
            quantity=quantity,
            price=price,
            side=side,
            is_otc=otc,
        )
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(dict_panel(data, title="Estimated Fees"))


# ══════════════════════════════════════════════════════════════════════════════
#  CRYPTO
# ══════════════════════════════════════════════════════════════════════════════


@cli.group()
def crypto():
    """Crypto pairs, quotes, holdings, historicals."""


@crypto.command()
@click.pass_context
@async_command
@handle_errors
async def pairs(ctx: click.Context):
    """All tradable crypto pairs."""
    async with get_authenticated_client() as client:
        data = await client.crypto.get_pairs()
        if _use_json(ctx):
            output_json(data)
        else:
            cols = [
                ("symbol", "Symbol"),
                ("name", "Name"),
                ("code", "Code"),
                ("tradability", "Tradability"),
                ("min_order_size", "Min Order"),
            ]
            console.print(model_table(data, cols, title="Crypto Pairs"))


@crypto.command("quote")
@click.argument("symbol")
@click.pass_context
@async_command
@handle_errors
async def crypto_quote(ctx: click.Context, symbol: str):
    """Quote for a crypto symbol (e.g. BTC). Resolves pair_id internally."""
    async with get_authenticated_client() as client:
        pair = await client.crypto.get_pair_by_symbol(symbol.upper())
        if not pair:
            raise click.ClickException(f"No crypto pair found for symbol: {symbol}")
        data = await client.crypto.get_quote(pair.id)
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(model_panel(data, title=f"Crypto Quote — {symbol.upper()}"))


@crypto.command()
@click.pass_context
@async_command
@handle_errors
async def holdings(ctx: click.Context):
    """Crypto holdings."""
    async with get_authenticated_client() as client:
        data = await client.crypto.get_holdings()
        if _use_json(ctx):
            output_json(data)
        else:
            cols = [
                ("id", "ID"),
                ("quantity", "Qty"),
                ("quantity_available", "Available"),
                ("created_at", "Created"),
            ]
            console.print(model_table(data, cols, title="Crypto Holdings"))


@crypto.command("historicals")
@click.argument("symbol")
@click.option("--interval", default="day", help="Interval: 15second, 5minute, 10minute, hour, day, week.")
@click.option("--span", default="year", help="Span: hour, day, week, month, 3month, year, 5year.")
@click.option("--last", type=int, default=None, help="Show only last N bars.")
@click.pass_context
@async_command
@handle_errors
async def crypto_historicals(ctx: click.Context, symbol: str, interval: str, span: str, last: int | None):
    """Crypto OHLCV historical bars."""
    async with get_authenticated_client() as client:
        pair = await client.crypto.get_pair_by_symbol(symbol.upper())
        if not pair:
            raise click.ClickException(f"No crypto pair found for symbol: {symbol}")
        bars = await client.crypto.get_historicals(pair.id, interval=interval, span=span)
        if last:
            bars = bars[-last:]
        if _use_json(ctx):
            output_json(bars)
        else:
            cols = [
                ("begins_at", "Date"),
                ("open_price", "Open"),
                ("high_price", "High"),
                ("low_price", "Low"),
                ("close_price", "Close"),
                ("volume", "Volume"),
            ]
            console.print(model_table(bars, cols, title=f"Crypto Historicals — {symbol.upper()} ({interval}/{span})"))


# ══════════════════════════════════════════════════════════════════════════════
#  OPTIONS
# ══════════════════════════════════════════════════════════════════════════════


@cli.group()
def options():
    """Option chains, instruments, market data, positions, orders."""


@options.command("chains")
@click.argument("symbol")
@click.pass_context
@async_command
@handle_errors
async def options_chains(ctx: click.Context, symbol: str):
    """Option chains for a stock symbol (resolves instrument_id from symbol)."""
    async with get_authenticated_client() as client:
        inst = await client.stocks.get_instrument_by_symbol(symbol.upper())
        data = await client.options.get_chains(inst.id)
        if _use_json(ctx):
            output_json(data)
        else:
            for chain in data:
                console.print(model_panel(chain, title=f"Option Chain — {chain.symbol}"))


@options.command("instruments")
@click.argument("chain_id")
@click.option("--expiration", default=None, help="Filter by expiration date (YYYY-MM-DD).")
@click.option("--type", "option_type", default=None, help="Filter by type: call or put.")
@click.pass_context
@async_command
@handle_errors
async def options_instruments(ctx: click.Context, chain_id: str, expiration: str | None, option_type: str | None):
    """Option contracts for a chain."""
    async with get_authenticated_client() as client:
        exp_dates = [expiration] if expiration else None
        data = await client.options.get_instruments(chain_id, expiration_dates=exp_dates, option_type=option_type)
        if _use_json(ctx):
            output_json(data)
        else:
            cols = [
                ("id", "ID"),
                ("chain_symbol", "Symbol"),
                ("type", "Type"),
                ("strike_price", "Strike"),
                ("expiration_date", "Expiration"),
                ("state", "State"),
                ("tradability", "Tradability"),
            ]
            console.print(model_table(data, cols, title="Option Instruments"))


@options.command("market-data")
@click.argument("option_id")
@click.pass_context
@async_command
@handle_errors
async def options_market_data(ctx: click.Context, option_id: str):
    """Greeks, IV, and prices for an option."""
    async with get_authenticated_client() as client:
        data = await client.options.get_market_data(option_id)
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(model_panel(data, title=f"Option Market Data — {option_id}"))


@options.command("positions")
@click.pass_context
@async_command
@handle_errors
async def options_positions(ctx: click.Context):
    """Open option positions."""
    async with get_authenticated_client() as client:
        data = await client.options.get_positions()
        if _use_json(ctx):
            output_json(data)
        else:
            cols = [
                ("chain_symbol", "Symbol"),
                ("type", "Type"),
                ("quantity", "Qty"),
                ("average_price", "Avg Price"),
                ("pending_buy_quantity", "Pending Buy"),
                ("pending_sell_quantity", "Pending Sell"),
                ("created_at", "Created"),
            ]
            console.print(model_table(data, cols, title="Option Positions"))


@options.command("orders")
@click.pass_context
@async_command
@handle_errors
async def options_orders(ctx: click.Context):
    """Option order history."""
    async with get_authenticated_client() as client:
        data = await client.options.get_orders()
        if _use_json(ctx):
            output_json(data)
        else:
            if not data:
                console.print("[dim]No option orders found.[/dim]")
                return
            cols = [
                ("id", "ID"),
                ("chain_symbol", "Symbol"),
                ("type", "Type"),
                ("state", "State"),
                ("quantity", "Qty"),
                ("price", "Price"),
                ("created_at", "Created"),
            ]
            console.print(dict_table(data, cols, title="Option Orders"))


@options.command("aggregate")
@click.option("--nonzero/--all", default=True, help="Only non-zero positions (default: non-zero).")
@click.pass_context
@async_command
@handle_errors
async def options_aggregate(ctx: click.Context, nonzero: bool):
    """Aggregated option positions grouped by strategy."""
    async with get_authenticated_client() as client:
        data = await client.options.get_aggregate_positions(nonzero=nonzero)
        if _use_json(ctx):
            output_json(data)
        else:
            if not data:
                console.print("[dim]No aggregate option positions found.[/dim]")
                return
            cols = [
                ("id", "ID"),
                ("strategy", "Strategy"),
                ("symbol", "Symbol"),
                ("direction", "Direction"),
                ("quantity", "Qty"),
                ("average_open_price", "Avg Price"),
            ]
            console.print(dict_table(data, cols, title="Aggregate Option Positions"))


@options.command("events")
@click.option("--chain-id", default=None, help="Filter by chain ID.")
@click.pass_context
@async_command
@handle_errors
async def options_events(ctx: click.Context, chain_id: str | None):
    """Option events (expirations, assignments, exercises)."""
    async with get_authenticated_client() as client:
        chain_ids = [chain_id] if chain_id else None
        data = await client.options.get_events(chain_ids=chain_ids)
        if _use_json(ctx):
            output_json(data)
        else:
            if not data:
                console.print("[dim]No option events found.[/dim]")
                return
            cols = [
                ("id", "ID"),
                ("type", "Type"),
                ("state", "State"),
                ("chain_id", "Chain"),
                ("event_date", "Date"),
            ]
            console.print(dict_table(data, cols, title="Option Events"))


@options.command("strategies")
@click.argument("strategy_codes", nargs=-1, required=True)
@click.pass_context
@async_command
@handle_errors
async def options_strategies(ctx: click.Context, strategy_codes: tuple[str, ...]):
    """Option strategy definitions/pricing by strategy codes."""
    async with get_authenticated_client() as client:
        data = await client.options.get_strategies(list(strategy_codes))
        if _use_json(ctx):
            output_json(data)
        else:
            if not data:
                console.print("[dim]No strategies found.[/dim]")
                return
            for strat in data:
                console.print(dict_panel(strat, title="Strategy"))


@options.command("market-data-batch")
@click.argument("option_ids", nargs=-1, required=True)
@click.pass_context
@async_command
@handle_errors
async def options_market_data_batch(ctx: click.Context, option_ids: tuple[str, ...]):
    """Batch option market data (greeks, prices) for multiple contracts."""
    async with get_authenticated_client() as client:
        data = await client.options.get_market_data_batch(list(option_ids))
        if _use_json(ctx):
            output_json(data)
        else:
            if not data:
                console.print("[dim]No market data found.[/dim]")
                return
            for md in data:
                console.print(model_panel(md, title="Option Market Data"))


@options.command("strategy-quotes")
@click.argument("ids", nargs=-1, required=True)
@click.option("--ratios", default=None, help="Comma-separated ratio quantities for each leg.")
@click.option("--types", default=None, help="Comma-separated position types (long, short) for each leg.")
@click.pass_context
@async_command
@handle_errors
async def options_strategy_quotes(ctx: click.Context, ids: tuple[str, ...], ratios: str | None, types: str | None):
    """Strategy-level quotes with greeks."""
    async with get_authenticated_client() as client:
        ratio_list = ratios.split(",") if ratios else None
        type_list = types.split(",") if types else None
        data = await client.options.get_strategy_quotes(
            ids=list(ids), ratios=ratio_list, types=type_list,
        )
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(dict_panel(data, title="Strategy Quotes"))


@options.command("pnl-chart")
@click.argument("legs")
@click.argument("order_price")
@click.argument("quantity")
@click.option("--underlying-price", default=None, help="Current underlying price.")
@click.pass_context
@async_command
@handle_errors
async def options_pnl_chart(ctx: click.Context, legs: str, order_price: str, quantity: str, underlying_price: str | None):
    """Options profit-and-loss chart data."""
    async with get_authenticated_client() as client:
        data = await client.options.get_pnl_chart(
            legs=legs, order_price=order_price, quantity=quantity, underlying_price=underlying_price,
        )
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(dict_panel(data, title="P&L Chart"))


@options.command("breakevens")
@click.argument("strategy_code")
@click.argument("average_cost")
@click.pass_context
@async_command
@handle_errors
async def options_breakevens(ctx: click.Context, strategy_code: str, average_cost: str):
    """Breakeven price calculations for an option position."""
    async with get_authenticated_client() as client:
        data = await client.options.get_breakevens(strategy_code=strategy_code, average_cost=average_cost)
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(dict_panel(data, title="Breakevens"))


# ══════════════════════════════════════════════════════════════════════════════
#  FUTURES
# ══════════════════════════════════════════════════════════════════════════════


@cli.group()
def futures():
    """Futures contracts, quotes, account, orders, P&L."""


@futures.command("contracts")
@click.argument("product_ids", nargs=-1, required=True)
@click.pass_context
@async_command
@handle_errors
async def futures_contracts(ctx: click.Context, product_ids: tuple[str, ...]):
    """List futures contracts by product UUIDs."""
    async with get_authenticated_client() as client:
        data = await client.futures.get_contracts(product_ids=list(product_ids))
        if _use_json(ctx):
            output_json(data)
        else:
            cols = [
                ("id", "ID"),
                ("symbol", "Symbol"),
                ("underlying", "Underlying"),
                ("expiration_date", "Expiration"),
                ("contract_size", "Size"),
                ("tick_size", "Tick"),
                ("state", "State"),
                ("active", "Active"),
            ]
            console.print(model_table(data, cols, title="Futures Contracts"))


@futures.command("quote")
@click.argument("contract_id")
@click.pass_context
@async_command
@handle_errors
async def futures_quote(ctx: click.Context, contract_id: str):
    """Quote for a futures contract."""
    async with get_authenticated_client() as client:
        data = await client.futures.get_quote(contract_id)
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(model_panel(data, title=f"Futures Quote — {data.symbol or contract_id}"))


@futures.command("account")
@click.pass_context
@async_command
@handle_errors
async def futures_account(ctx: click.Context):
    """Futures account summary."""
    async with get_authenticated_client() as client:
        data = await client.futures.get_account()
        if _use_json(ctx):
            output_json(data)
        else:
            if data is None:
                console.print("[dim]No futures account found.[/dim]")
                return
            console.print(model_panel(data, title="Futures Account"))


@futures.command("orders")
@click.pass_context
@async_command
@handle_errors
async def futures_orders(ctx: click.Context):
    """Futures order history."""
    async with get_authenticated_client() as client:
        data = await client.futures.get_orders()
        if _use_json(ctx):
            output_json(data)
        else:
            cols = [
                ("id", "ID"),
                ("symbol", "Symbol"),
                ("side", "Side"),
                ("order_type", "Type"),
                ("quantity", "Qty"),
                ("price", "Price"),
                ("state", "State"),
                ("created_at", "Created"),
            ]
            console.print(model_table(data, cols, title="Futures Orders"))


@futures.command("pnl")
@click.pass_context
@async_command
@handle_errors
async def futures_pnl(ctx: click.Context):
    """Realized P&L from closing futures orders."""
    async with get_authenticated_client() as client:
        data = await client.futures.calculate_pnl()
        if _use_json(ctx):
            output_json({k: str(v) for k, v in data.items()})
        else:
            table = Table(title="Futures Realized P&L")
            table.add_column("Symbol")
            table.add_column("P&L")
            for sym, pnl in data.items():
                color = "green" if pnl >= 0 else "red"
                table.add_row(sym, f"[{color}]{_format_value(pnl)}[/{color}]")
            console.print(table)


@futures.command("product")
@click.argument("product_id")
@click.pass_context
@async_command
@handle_errors
async def futures_product(ctx: click.Context, product_id: str):
    """Futures product metadata (contract specs)."""
    async with get_authenticated_client() as client:
        data = await client.futures.get_product(product_id)
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(dict_panel(data, title=f"Futures Product — {product_id}"))


@futures.command("closes")
@click.argument("contract_ids", nargs=-1, required=True)
@click.pass_context
@async_command
@handle_errors
async def futures_closes(ctx: click.Context, contract_ids: tuple[str, ...]):
    """Previous close prices for futures contracts."""
    async with get_authenticated_client() as client:
        data = await client.futures.get_closes(list(contract_ids))
        if _use_json(ctx):
            output_json(data)
        else:
            if not data:
                console.print("[dim]No close data found.[/dim]")
                return
            for item in data:
                console.print(dict_panel(item, title="Futures Close"))


@futures.command("closes-range")
@click.argument("contract_id")
@click.argument("start")
@click.pass_context
@async_command
@handle_errors
async def futures_closes_range(ctx: click.Context, contract_id: str, start: str):
    """Historical close range for a futures contract.

    START should be an ISO datetime (e.g. 2026-01-01T00:00:00Z).
    """
    async with get_authenticated_client() as client:
        data = await client.futures.get_closes_range(contract_id, start)
        if _use_json(ctx):
            output_json(data)
        else:
            if not data:
                console.print("[dim]No close range data found.[/dim]")
                return
            for item in data:
                console.print(dict_panel(item, title="Futures Close"))


@futures.command("settings")
@click.pass_context
@async_command
@handle_errors
async def futures_settings(ctx: click.Context):
    """Futures user settings."""
    async with get_authenticated_client() as client:
        data = await client.futures.get_user_settings()
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(dict_panel(data, title="Futures User Settings"))


@futures.command("pnl-cost-basis")
@click.argument("account_id")
@click.option("--contract-id", default=None, help="Optional contract ID filter.")
@click.pass_context
@async_command
@handle_errors
async def futures_pnl_cost_basis(ctx: click.Context, account_id: str, contract_id: str | None):
    """Futures P&L and cost basis."""
    async with get_authenticated_client() as client:
        data = await client.futures.get_pnl_cost_basis(account_id, contract_id=contract_id)
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(dict_panel(data, title="Futures P&L Cost Basis"))


@futures.command("aggregated-positions")
@click.argument("account_id")
@click.pass_context
@async_command
@handle_errors
async def futures_aggregated_positions(ctx: click.Context, account_id: str):
    """Aggregated futures positions."""
    async with get_authenticated_client() as client:
        data = await client.futures.get_aggregated_positions(account_id)
        if _use_json(ctx):
            output_json(data)
        else:
            if not data:
                console.print("[dim]No aggregated positions found.[/dim]")
                return
            for item in data:
                console.print(dict_panel(item, title="Futures Position"))


# ══════════════════════════════════════════════════════════════════════════════
#  INDEXES
# ══════════════════════════════════════════════════════════════════════════════


@cli.group()
def indexes():
    """Index quotes, instruments, option chains."""


@indexes.command("quote")
@click.argument("symbol_or_id")
@click.pass_context
@async_command
@handle_errors
async def indexes_quote(ctx: click.Context, symbol_or_id: str):
    """Index value. Accepts a symbol (SPX) or UUID."""
    async with get_authenticated_client() as client:
        if _is_uuid(symbol_or_id):
            data = await client.indexes.get_quote(symbol_or_id)
        else:
            data = await client.indexes.get_quote_by_symbol(symbol_or_id.upper())
        label = data.symbol or symbol_or_id
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(model_panel(data, title=f"Index Quote — {label}"))


@indexes.command("instrument")
@click.argument("symbol_or_id")
@click.pass_context
@async_command
@handle_errors
async def indexes_instrument(ctx: click.Context, symbol_or_id: str):
    """Index instrument metadata. Accepts a symbol (SPX) or UUID."""
    async with get_authenticated_client() as client:
        if _is_uuid(symbol_or_id):
            data = await client.indexes.get_instrument_by_id(symbol_or_id)
        else:
            data = await client.indexes.get_instrument(symbol_or_id.upper())
        label = data.symbol or symbol_or_id
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(model_panel(data, title=f"Index Instrument — {label}"))


@indexes.command("fundamentals")
@click.argument("symbols_or_ids", nargs=-1, required=True)
@click.pass_context
@async_command
@handle_errors
async def indexes_fundamentals(ctx: click.Context, symbols_or_ids: tuple[str, ...]):
    """Index fundamentals (high/low, 52-week range). Accepts symbols (SPX NDX VIX) or UUIDs."""
    async with get_authenticated_client() as client:
        # Resolve any symbols to IDs, collect all IDs for a single batch call
        ids: list[str] = []
        for s in symbols_or_ids:
            if _is_uuid(s):
                ids.append(s)
            else:
                inst = await client.indexes.get_instrument(s.upper())
                ids.append(inst.id)
        results = await client.indexes.get_fundamentals(ids)
        if _use_json(ctx):
            output_json(results)
        else:
            if len(results) == 1:
                label = results[0].symbol or symbols_or_ids[0]
                console.print(model_panel(results[0], title=f"Index Fundamentals — {label}"))
            else:
                cols = [
                    ("symbol", "Symbol"),
                    ("open", "Open"),
                    ("high", "High"),
                    ("low", "Low"),
                    ("previous_close", "Prev Close"),
                    ("high_52_weeks", "52W High"),
                    ("low_52_weeks", "52W Low"),
                ]
                console.print(model_table(results, cols, title="Index Fundamentals"))


@indexes.command("closes")
@click.argument("symbol_or_id")
@click.pass_context
@async_command
@handle_errors
async def indexes_closes(ctx: click.Context, symbol_or_id: str):
    """Previous close for an index. Accepts a symbol (VIX) or UUID."""
    async with get_authenticated_client() as client:
        if _is_uuid(symbol_or_id):
            results = await client.indexes.get_closes([symbol_or_id])
            if not results:
                raise InvalidSymbolError(symbol_or_id)
            data = results[0]
        else:
            data = await client.indexes.get_close_by_symbol(symbol_or_id.upper())
        label = data.symbol or symbol_or_id
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(model_panel(data, title=f"Index Close — {label}"))


@indexes.command("chains")
@click.argument("symbol_or_id")
@click.pass_context
@async_command
@handle_errors
async def indexes_chains(ctx: click.Context, symbol_or_id: str):
    """Option chains for an index. Accepts a symbol (SPX) or UUID."""
    async with get_authenticated_client() as client:
        if _is_uuid(symbol_or_id):
            data = await client.indexes.get_option_chains_by_id(symbol_or_id)
        else:
            data = await client.indexes.get_option_chains(symbol_or_id.upper())
        if _use_json(ctx):
            output_json(data)
        else:
            for chain in data:
                console.print(model_panel(chain, title=f"Index Option Chain — {chain.symbol}"))


# ══════════════════════════════════════════════════════════════════════════════
#  MARKETS
# ══════════════════════════════════════════════════════════════════════════════


@cli.group()
def markets():
    """Market info, hours, movers, categories."""


@markets.command("list")
@click.pass_context
@async_command
@handle_errors
async def markets_list(ctx: click.Context):
    """Available markets."""
    async with get_authenticated_client() as client:
        data = await client.markets.get_markets()
        if _use_json(ctx):
            output_json(data)
        else:
            cols = [
                ("acronym", "Code"),
                ("name", "Name"),
                ("city", "City"),
                ("country", "Country"),
                ("operating_mic", "MIC"),
            ]
            console.print(dict_table(data, cols, title="Markets"))


@markets.command("hours")
@click.argument("market")
@click.argument("date")
@click.pass_context
@async_command
@handle_errors
async def markets_hours(ctx: click.Context, market: str, date: str):
    """Market hours for a date (e.g. XNYS 2026-02-26)."""
    async with get_authenticated_client() as client:
        data = await client.markets.get_market_hours(market.upper(), date)
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(dict_panel(data, title=f"Market Hours — {market.upper()} {date}"))


@markets.command("movers")
@click.option("--direction", default="up", help="Direction: up or down.")
@click.pass_context
@async_command
@handle_errors
async def markets_movers(ctx: click.Context, direction: str):
    """S&P 500 movers."""
    async with get_authenticated_client() as client:
        data = await client.markets.get_movers(direction=direction)
        if _use_json(ctx):
            output_json(data)
        else:
            if not data:
                console.print("[dim]No movers found.[/dim]")
                return
            cols = [
                ("symbol", "Symbol"),
                ("price_movement", "Movement"),
                ("description", "Description"),
            ]
            console.print(dict_table(data, cols, title=f"S&P 500 Movers — {direction.upper()}"))


@markets.command("categories")
@click.pass_context
@async_command
@handle_errors
async def markets_categories(ctx: click.Context):
    """Discovery categories."""
    async with get_authenticated_client() as client:
        data = await client.markets.get_categories()
        if _use_json(ctx):
            output_json(data)
        else:
            if not data:
                console.print("[dim]No categories found.[/dim]")
                return
            cols = [
                ("name", "Name"),
                ("slug", "Tag"),
            ]
            console.print(dict_table(data, cols, title="Categories"))


@markets.command("category")
@click.argument("tag")
@click.pass_context
@async_command
@handle_errors
async def markets_category(ctx: click.Context, tag: str):
    """Instruments in a discovery category."""
    async with get_authenticated_client() as client:
        data = await client.markets.get_category_instruments(tag)
        if _use_json(ctx):
            output_json(data)
        else:
            instrument_urls = data.get("instruments", [])
            if not instrument_urls:
                console.print(f"[dim]No instruments found for category: {tag}[/dim]")
                return
            name = data.get("name", tag)
            desc = data.get("canonical_examples", "")
            console.print(f"[bold]{name}[/bold] ({len(instrument_urls)} instruments)")
            if desc:
                console.print(f"  [dim]{desc}[/dim]")
            # Fetch instrument details for each URL
            instruments = []
            for url in instrument_urls:
                try:
                    inst = await client.stocks.get_instrument_by_id(url)
                    instruments.append(inst)
                except Exception:
                    continue
            if instruments:
                cols = [
                    ("symbol", "Symbol"),
                    ("name", "Name"),
                    ("simple_name", "Simple Name"),
                    ("state", "State"),
                ]
                console.print(model_table(instruments, cols, title=f"Category — {name}"))


# ══════════════════════════════════════════════════════════════════════════════
#  SCREENERS
# ══════════════════════════════════════════════════════════════════════════════


@cli.group()
def screeners():
    """Stock screeners: saved, presets, indicators, and scan."""


@screeners.command("list")
@click.pass_context
@async_command
@handle_errors
async def screeners_list(ctx: click.Context):
    """List your saved screeners."""
    async with get_authenticated_client() as client:
        data = await client.screeners.get_screeners()
        if _use_json(ctx):
            output_json(data)
        else:
            if not data:
                console.print("[dim]No saved screeners found.[/dim]")
                return
            cols = [
                ("id", "ID"),
                ("display_name", "Name"),
                ("sort_by", "Sort By"),
                ("sort_direction", "Direction"),
            ]
            console.print(model_table(data, cols, title="Saved Screeners"))
            for s in data:
                if s.filters:
                    filter_lines = []
                    for f in s.filters:
                        if not f.is_hidden:
                            filter_lines.append(f"  {f.key}: {json.dumps(f.filter, default=str)}")
                    if filter_lines:
                        console.print(f"\n[bold]{s.display_name}[/bold] filters:")
                        for line in filter_lines:
                            console.print(line)


@screeners.command("presets")
@click.pass_context
@async_command
@handle_errors
async def screeners_presets(ctx: click.Context):
    """List available preset screeners from Robinhood."""
    async with get_authenticated_client() as client:
        data = await client.screeners.get_presets()
        if _use_json(ctx):
            output_json(data)
        else:
            if not data:
                console.print("[dim]No presets found.[/dim]")
                return
            cols = [
                ("id", "ID"),
                ("display_name", "Name"),
                ("sort_by", "Sort By"),
                ("sort_direction", "Direction"),
            ]
            console.print(model_table(data, cols, title="Preset Screeners"))


@screeners.command("get")
@click.argument("screener_id")
@click.pass_context
@async_command
@handle_errors
async def screeners_get(ctx: click.Context, screener_id: str):
    """Show details for a saved or preset screener by ID."""
    async with get_authenticated_client() as client:
        data = await client.screeners.get_screener(screener_id)
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(model_panel(data, title=f"Screener — {data.display_name}"))
            if data.filters:
                console.print("\n[bold]Filters:[/bold]")
                for f in data.filters:
                    hidden = " [dim](hidden)[/dim]" if f.is_hidden else ""
                    console.print(f"  {f.key}: {json.dumps(f.filter, default=str)}{hidden}")


@screeners.command("indicators")
@click.pass_context
@async_command
@handle_errors
async def screeners_indicators(ctx: click.Context):
    """List all available screener filter indicators."""
    async with get_authenticated_client() as client:
        data = await client.screeners.get_indicators()
        if _use_json(ctx):
            output_json(data)
        else:
            if not data:
                console.print("[dim]No indicators found.[/dim]")
                return
            for cat in data:
                console.print(f"\n[bold]{cat.title}[/bold]")
                for ind in cat.indicators:
                    ftype = ""
                    if ind.filter_parameters:
                        ftype = f" [dim]({ind.filter_parameters.type})[/dim]"
                    console.print(f"  [cyan]{ind.key}[/cyan]{ftype} — {ind.title}")
                    desc = ind.description
                    if isinstance(desc, dict):
                        desc = desc.get("text", "")
                    if desc:
                        console.print(f"    [dim]{desc}[/dim]")
                    if ind.filter_parameters and ind.filter_parameters.options:
                        for opt in ind.filter_parameters.options:
                            if opt.id:
                                title = opt.title or ""
                                subtitle = f" ({opt.subtitle})" if opt.subtitle else ""
                                console.print(f"      [yellow]{opt.id}[/yellow] {title}{subtitle}")


@screeners.command("scan")
@click.argument("screener_id")
@click.option("--limit", default=25, help="Max results to display.")
@click.pass_context
@async_command
@handle_errors
async def screeners_scan(ctx: click.Context, screener_id: str, limit: int):
    """Run a saved/preset screener and display results.

    SCREENER_ID is the ID of a saved or preset screener. Use 'screeners list'
    or 'screeners presets' to find IDs.
    """
    async with get_authenticated_client() as client:
        screener = await client.screeners.get_screener(screener_id)
        indicators = [{"key": f.key, "filter": f.filter} for f in screener.filters]
        result = await client.screeners.scan(
            indicators=indicators,
            columns=screener.columns or None,
            sort_by=screener.sort_by,
            sort_direction=screener.sort_direction or "DESC",
        )
        if _use_json(ctx):
            output_json(result)
        else:
            if not result.results:
                console.print(f"[dim]No results for screener: {screener.display_name}[/dim]")
                return
            title = f"{screener.display_name} ({result.subtitle})" if result.subtitle else screener.display_name
            table = Table(title=title)
            table.add_column("Symbol")
            table.add_column("Name")
            display_cols = [c for c in result.columns if c.id != "instrument_symbol"]
            for col in display_cols:
                table.add_column(col.id.replace("_", " ").title(), justify="right")
            for sr in result.results[:limit]:
                row = [sr.symbol, sr.name]
                for v in sr.values:
                    row.append(v)
                table.add_row(*row)
            console.print(table)


# ══════════════════════════════════════════════════════════════════════════════
#  DISCOVERY
# ══════════════════════════════════════════════════════════════════════════════


@cli.group()
def discovery():
    """Analyst ratings, hedge funds, insiders, short interest, earnings, and more."""


@discovery.command("ratings")
@click.argument("instrument_id")
@click.pass_context
@async_command
@handle_errors
async def discovery_ratings(ctx: click.Context, instrument_id: str):
    """Analyst ratings (buy/hold/sell, price targets) for an instrument."""
    async with get_authenticated_client() as client:
        data = await client.discovery.get_ratings(instrument_id)
        if _use_json(ctx):
            output_json(data)
        else:
            if data.summary:
                console.print(dict_panel(data.summary, title="Rating Summary"))
            if data.ratings:
                cols = [
                    ("type", "Type"),
                    ("text", "Text"),
                    ("published_at", "Published"),
                ]
                console.print(dict_table(data.ratings, cols, title="Individual Ratings"))


@discovery.command("ratings-batch")
@click.argument("instrument_ids", nargs=-1, required=True)
@click.pass_context
@async_command
@handle_errors
async def discovery_ratings_batch(ctx: click.Context, instrument_ids: tuple[str, ...]):
    """Analyst ratings for multiple instruments."""
    async with get_authenticated_client() as client:
        data = await client.discovery.get_ratings_batch(list(instrument_ids))
        if _use_json(ctx):
            output_json(data)
        else:
            for rating in data:
                label = rating.instrument_id or "?"
                if rating.summary:
                    console.print(dict_panel(rating.summary, title=f"Ratings — {label[:8]}..."))


@discovery.command("hedgefunds")
@click.argument("instrument_id")
@click.pass_context
@async_command
@handle_errors
async def discovery_hedgefunds(ctx: click.Context, instrument_id: str):
    """Hedge fund activity summary (sentiment, quarterly aggregates)."""
    async with get_authenticated_client() as client:
        data = await client.discovery.get_hedgefund_summary(instrument_id)
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(f"[bold]Sentiment:[/bold] {data.sentiment_score or '-'}")
            if data.quarterly_aggregate_transactions:
                cols = [
                    ("date", "Quarter"),
                    ("total_shares_held", "Shares Held"),
                    ("shares_bought", "Bought"),
                    ("shares_sold", "Sold"),
                ]
                console.print(model_table(data.quarterly_aggregate_transactions, cols, title="Hedge Fund Quarterly Activity"))


@discovery.command("hedgefund-transactions")
@click.argument("instrument_id")
@click.pass_context
@async_command
@handle_errors
async def discovery_hedgefund_transactions(ctx: click.Context, instrument_id: str):
    """Detailed hedge fund transactions (individual manager trades)."""
    async with get_authenticated_client() as client:
        data = await client.discovery.get_hedgefund_transactions(instrument_id)
        if _use_json(ctx):
            output_json(data)
        else:
            if not data.detailed_transactions:
                console.print("[dim]No hedge fund transactions found.[/dim]")
                return
            cols = [
                ("institution_name", "Institution"),
                ("manager_name", "Manager"),
                ("action", "Action"),
                ("shares_traded", "Shares"),
                ("market_value", "Mkt Value"),
                ("portfolio_percentage", "Port %"),
            ]
            console.print(model_table(data.detailed_transactions, cols, title="Hedge Fund Transactions"))


@discovery.command("insiders")
@click.argument("instrument_id")
@click.pass_context
@async_command
@handle_errors
async def discovery_insiders(ctx: click.Context, instrument_id: str):
    """Insider trading summary (sentiment, monthly aggregates)."""
    async with get_authenticated_client() as client:
        data = await client.discovery.get_insider_summary(instrument_id)
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(f"[bold]Sentiment:[/bold] {data.sentiment_score or '-'}")
            if data.monthly_aggregate_transactions:
                cols = [
                    ("date", "Month"),
                    ("shares_bought", "Bought"),
                    ("shares_sold", "Sold"),
                    ("buy_transactions", "Buy Txns"),
                    ("sell_transactions", "Sell Txns"),
                ]
                console.print(model_table(data.monthly_aggregate_transactions, cols, title="Insider Monthly Activity"))


@discovery.command("insider-transactions")
@click.argument("instrument_id")
@click.pass_context
@async_command
@handle_errors
async def discovery_insider_transactions(ctx: click.Context, instrument_id: str):
    """Detailed insider transactions (individual trades by officers)."""
    async with get_authenticated_client() as client:
        data = await client.discovery.get_insider_transactions(instrument_id)
        if _use_json(ctx):
            output_json(data)
        else:
            if not data.detailed_transactions:
                console.print("[dim]No insider transactions found.[/dim]")
                return
            cols = [
                ("name", "Name"),
                ("position", "Position"),
                ("transaction_type", "Type"),
                ("number_of_shares", "Shares"),
                ("amount", "Amount"),
                ("date", "Date"),
            ]
            console.print(model_table(data.detailed_transactions, cols, title="Insider Transactions"))


@discovery.command("short-interest")
@click.argument("instrument_id")
@click.pass_context
@async_command
@handle_errors
async def discovery_short_interest(ctx: click.Context, instrument_id: str):
    """Short interest data (fee, inventory, daily fee)."""
    async with get_authenticated_client() as client:
        data = await client.discovery.get_short_interest(instrument_id)
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(model_panel(data, title="Short Interest"))


@discovery.command("equity-summary")
@click.argument("instrument_id")
@click.pass_context
@async_command
@handle_errors
async def discovery_equity_summary(ctx: click.Context, instrument_id: str):
    """Equity summary — daily net buy/sell transaction flow."""
    async with get_authenticated_client() as client:
        data = await client.discovery.get_equity_summary(instrument_id)
        if _use_json(ctx):
            output_json(data)
        else:
            if not data.daily_transactions:
                console.print("[dim]No equity summary data.[/dim]")
                return
            cols = [
                ("date", "Date"),
                ("net_buy_percentage", "Net Buy %"),
                ("net_sell_percentage", "Net Sell %"),
                ("buy_volume_percentage_change", "Buy Vol Change %"),
                ("sell_volume_percentage_change", "Sell Vol Change %"),
            ]
            console.print(model_table(data.daily_transactions, cols, title="Equity Summary"))


@discovery.command("earnings")
@click.argument("instrument_id")
@click.pass_context
@async_command
@handle_errors
async def discovery_earnings(ctx: click.Context, instrument_id: str):
    """Earnings data for an instrument."""
    async with get_authenticated_client() as client:
        data = await client.discovery.get_earnings(instrument_id)
        if _use_json(ctx):
            output_json(data)
        else:
            if not data.results:
                console.print("[dim]No earnings data found.[/dim]")
                return
            table = Table(title="Earnings")
            table.add_column("Year")
            table.add_column("Qtr")
            table.add_column("Symbol")
            table.add_column("EPS Est")
            table.add_column("EPS Actual")
            table.add_column("Report Date")
            table.add_column("Timing")
            for r in data.results:
                eps = r.get("eps", {}) or {}
                report = r.get("report", {}) or {}
                table.add_row(
                    str(r.get("year", "")),
                    str(r.get("quarter", "")),
                    r.get("symbol", ""),
                    eps.get("estimate", "-"),
                    eps.get("actual", "-"),
                    report.get("date", "-"),
                    report.get("timing", "-"),
                )
            console.print(table)


@discovery.command("similar")
@click.argument("instrument_id")
@click.pass_context
@async_command
@handle_errors
async def discovery_similar(ctx: click.Context, instrument_id: str):
    """Similar instrument recommendations."""
    async with get_authenticated_client() as client:
        data = await client.discovery.get_similar(instrument_id)
        if _use_json(ctx):
            output_json(data)
        else:
            if not data.similar:
                console.print("[dim]No similar instruments found.[/dim]")
                return
            cols = [
                ("symbol", "Symbol"),
                ("name", "Name"),
                ("simple_name", "Simple Name"),
            ]
            console.print(model_table(data.similar, cols, title="Similar Instruments"))


@discovery.command("search")
@click.argument("query")
@click.pass_context
@async_command
@handle_errors
async def discovery_search(ctx: click.Context, query: str):
    """Unified search for stocks, crypto, lists, futures."""
    async with get_authenticated_client() as client:
        data = await client.discovery.search(query)
        if _use_json(ctx):
            output_json(data)
        else:
            if not data:
                console.print("[dim]No search results.[/dim]")
                return
            for section in data:
                content = section.get("content", {})
                content_type = content.get("content_type", "unknown")
                items = content.get("data", [])
                if not items:
                    continue
                title = section.get("display_title") or content_type.replace("_", " ").title()
                console.print(f"\n[bold]{title}[/bold] ({len(items)} results)")
                for item in items[:10]:
                    # Items may nest the real data under an "item" key
                    detail = item.get("item", item)
                    symbol = detail.get("symbol") or ""
                    name = detail.get("simple_name") or detail.get("name") or ""
                    console.print(f"  {symbol:10s} {name}")


@discovery.command("market-indices")
@click.option("--symbols", default=None, help="Comma-separated index symbols (e.g. SPX,NDX,DJX,VIX,RUT).")
@click.pass_context
@async_command
@handle_errors
async def discovery_market_indices(ctx: click.Context, symbols: str | None):
    """Market index summaries (S&P 500, Nasdaq, Dow Jones, etc.)."""
    async with get_authenticated_client() as client:
        sym_list = symbols.split(",") if symbols else None
        data = await client.discovery.get_market_indices(symbols=sym_list)
        if _use_json(ctx):
            output_json(data)
        else:
            if not data:
                console.print("[dim]No market indices found.[/dim]")
                return
            cols = [
                ("key", "Symbol"),
                ("name", "Name"),
                ("value", "Value"),
                ("previous_close", "Prev Close"),
                ("percent_change", "Change %"),
            ]
            console.print(model_table(data, cols, title="Market Indices"))


@discovery.command("etp-details")
@click.argument("instrument_id")
@click.pass_context
@async_command
@handle_errors
async def discovery_etp_details(ctx: click.Context, instrument_id: str):
    """ETP (ETF/ETN) details — AUM, expense ratio, holdings, performance."""
    async with get_authenticated_client() as client:
        data = await client.discovery.get_etp_details(instrument_id)
        if _use_json(ctx):
            output_json(data)
        else:
            fields = [
                "symbol", "aum", "nav", "gross_expense_ratio", "sec_yield",
                "inception_date", "category", "index_tracked", "total_holdings",
                "is_leveraged", "is_inverse", "is_actively_managed",
            ]
            console.print(model_panel(data, title=f"ETP Details — {data.symbol or instrument_id[:8]}", fields=fields))


@discovery.command("nbbo")
@click.argument("instrument_id")
@click.pass_context
@async_command
@handle_errors
async def discovery_nbbo(ctx: click.Context, instrument_id: str):
    """National Best Bid/Offer summary."""
    async with get_authenticated_client() as client:
        data = await client.discovery.get_nbbo_summary(instrument_id)
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(model_panel(data, title="NBBO Summary"))


@discovery.command("chart-bounds")
@click.pass_context
@async_command
@handle_errors
async def discovery_chart_bounds(ctx: click.Context):
    """Chart time bounds based on current market hours."""
    async with get_authenticated_client() as client:
        data = await client.discovery.get_chart_bounds()
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(model_panel(data, title="Chart Bounds"))


@discovery.command("feed")
@click.option("--limit", type=int, default=10, help="Max articles to show.")
@click.pass_context
@async_command
@handle_errors
async def discovery_feed(ctx: click.Context, limit: int):
    """General news feed (from dora.robinhood.com)."""
    async with get_authenticated_client() as client:
        articles = await client.discovery.get_feed()
        articles = articles[:limit]
        if _use_json(ctx):
            output_json(articles)
        else:
            cols = [
                ("published_at", "Published"),
                ("source", "Source"),
                ("title", "Title"),
            ]
            console.print(dict_table(articles, cols, title="News Feed"))


@discovery.command("instrument-feed")
@click.argument("instrument_id")
@click.option("--limit", type=int, default=10, help="Max articles to show.")
@click.pass_context
@async_command
@handle_errors
async def discovery_instrument_feed(ctx: click.Context, instrument_id: str, limit: int):
    """News feed for a specific instrument (from dora.robinhood.com)."""
    async with get_authenticated_client() as client:
        articles = await client.discovery.get_instrument_feed(instrument_id)
        articles = articles[:limit]
        if _use_json(ctx):
            output_json(articles)
        else:
            cols = [
                ("published_at", "Published"),
                ("source", "Source"),
                ("title", "Title"),
            ]
            console.print(dict_table(articles, cols, title=f"News Feed — {instrument_id[:8]}..."))


@screeners.command("query")
@click.option("--indicator", "-i", multiple=True, required=True, help="Indicator in KEY=OPTION_ID format. For MULTI_SELECT, comma-separate IDs. Use 'screeners indicators' to find valid keys and option IDs.")
@click.option("--sort", default=None, help="Column key to sort by.")
@click.option("--direction", type=click.Choice(["ASC", "DESC"]), default="DESC", help="Sort direction.")
@click.option("--limit", default=25, help="Max results to display.")
@click.pass_context
@async_command
@handle_errors
async def screeners_query(ctx: click.Context, indicator: tuple[str, ...], sort: str | None, direction: str, limit: int):
    """Run an ad-hoc screener scan with custom filters.

    Each -i flag takes KEY=OPTION_ID format. Use 'screeners indicators' to find
    valid keys and option IDs. For MULTI_SELECT indicators, comma-separate IDs.

    Examples:

        screeners query -i pe_ratio=pe_ratio_more_than_5

        screeners query -i market_cap=mkt_cap_large_cap,mkt_cap_mega_cap --sort market_cap

        screeners query -i sector=Technology -i 1d_price_change=daily_price_is_up
    """
    async with get_authenticated_client() as client:
        # First fetch indicator definitions to determine filter types
        indicator_catalog = await client.screeners.get_indicators()
        type_map: dict[str, str] = {}
        for cat in indicator_catalog:
            for ind in cat.indicators:
                if ind.filter_parameters:
                    type_map[ind.key] = ind.filter_parameters.type

        indicators = []
        for spec in indicator:
            if "=" not in spec:
                raise click.ClickException(f"Invalid format: '{spec}'. Use KEY=OPTION_ID")
            key, val = spec.split("=", 1)
            filter_type = type_map.get(key)

            if filter_type == "MULTI_SELECT":
                ids = val.split(",")
                indicators.append({
                    "key": key,
                    "filter": {"type": "MULTI_SELECT", "selections": [{"id": v} for v in ids]},
                })
            else:
                indicators.append({
                    "key": key,
                    "filter": {"type": "SINGLE_SELECT", "selection": {"id": val, "secondary_filter": None}},
                })

        result = await client.screeners.scan(
            indicators=indicators,
            sort_by=sort,
            sort_direction=direction,
        )
        if _use_json(ctx):
            output_json(result)
        else:
            if not result.results:
                console.print("[dim]No results matching filters.[/dim]")
                return
            table = Table(title=f"Scan Results ({result.subtitle})" if result.subtitle else "Scan Results")
            table.add_column("Symbol")
            table.add_column("Name")
            display_cols = [c for c in result.columns if c.id != "instrument_symbol"]
            for col in display_cols:
                table.add_column(col.id.replace("_", " ").title(), justify="right")
            for sr in result.results[:limit]:
                row = [sr.symbol, sr.name]
                for v in sr.values:
                    row.append(v)
                table.add_row(*row)
            console.print(table)


# ══════════════════════════════════════════════════════════════════════════════
#  ALERTS
# ══════════════════════════════════════════════════════════════════════════════


@cli.group()
def alerts():
    """Custom price and indicator alerts for instruments."""


@alerts.command("list")
@click.argument("instrument_id")
@click.pass_context
@async_command
@handle_errors
async def alerts_list(ctx: click.Context, instrument_id: str):
    """List all alerts for an instrument."""
    async with get_authenticated_client() as client:
        instrument_id = await _resolve_instrument_id(client, instrument_id)
        data = await client.alerts.get_alerts(instrument_id)
        if _use_json(ctx):
            output_json(data)
        else:
            if data.cooldown_description:
                console.print(f"[dim]{data.cooldown_description}[/dim]")
            if data.price_alerts_limit_reached:
                console.print("[yellow]Price alerts limit reached[/yellow]")
            if data.indicator_alerts_limit_reached:
                console.print("[yellow]Indicator alerts limit reached[/yellow]")
            if not data.settings:
                console.print("[dim]No alerts configured.[/dim]")
                return
            table = Table(title=f"Alerts — {instrument_id[:8]}...")
            table.add_column("ID")
            table.add_column("Type")
            table.add_column("Enabled")
            table.add_column("Price")
            table.add_column("Interval")
            table.add_column("Updated")
            for s in data.settings:
                table.add_row(
                    (s.id or "-")[:8],
                    s.setting_type or "-",
                    "Yes" if s.enabled else "No",
                    str(s.price) if s.price is not None else "-",
                    s.interval or "-",
                    _format_value(s.updated_at),
                )
            console.print(table)


@alerts.command("create")
@click.argument("instrument_id")
@click.argument("setting_type")
@click.option("--price", type=str, default=None, help="Target price (for price alerts).")
@click.option("--interval", type=str, default=None, help="Interval (for indicator alerts, e.g. '5m').")
@click.pass_context
@async_command
@handle_errors
async def alerts_create(
    ctx: click.Context,
    instrument_id: str,
    setting_type: str,
    price: str | None,
    interval: str | None,
):
    """Create a price or indicator alert.

    SETTING_TYPE is e.g. price_above, price_below, rsi_above, price_above_vwap, etc.
    """
    async with get_authenticated_client() as client:
        instrument_id = await _resolve_instrument_id(client, instrument_id)
        setting: dict = {"enabled": True, "setting_type": setting_type}
        if price is not None:
            setting["price"] = price
        if interval is not None:
            setting["interval"] = interval
        data = await client.alerts.create_alert(instrument_id, [setting])
        if _use_json(ctx):
            output_json(data)
        else:
            console.print("[green]Alert created.[/green]")
            for s in data.settings:
                if s.setting_type == setting_type and s.enabled:
                    console.print(model_panel(s, title=f"Alert — {setting_type}"))
                    break


@alerts.command("update")
@click.argument("instrument_id")
@click.argument("alert_id")
@click.option("--enabled/--disabled", default=None, help="Enable or disable the alert.")
@click.option("--price", type=str, default=None, help="New target price.")
@click.pass_context
@async_command
@handle_errors
async def alerts_update(
    ctx: click.Context,
    instrument_id: str,
    alert_id: str,
    enabled: bool | None,
    price: str | None,
):
    """Update an existing alert by its ID."""
    async with get_authenticated_client() as client:
        instrument_id = await _resolve_instrument_id(client, instrument_id)
        current = await client.alerts.get_alerts(instrument_id)
        target = None
        for s in current.settings:
            if s.id == alert_id:
                target = s
                break
        if target is None:
            raise click.ClickException(f"Alert ID '{alert_id}' not found on this instrument.")

        setting: dict = {"id": alert_id, "setting_type": target.setting_type}
        if enabled is not None:
            setting["enabled"] = enabled
        if price is not None:
            setting["price"] = price
        data = await client.alerts.update_alert(instrument_id, [setting])
        if _use_json(ctx):
            output_json(data)
        else:
            console.print("[green]Alert updated.[/green]")
            for s in data.settings:
                if s.id == alert_id:
                    console.print(model_panel(s, title=f"Alert — {alert_id[:8]}..."))
                    break
