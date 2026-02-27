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
@click.argument("symbol")
@click.option("--interval", default="day", help="Interval: 5minute, 10minute, hour, day, week.")
@click.option("--span", default="year", help="Span: day, week, month, 3month, year, 5year.")
@click.option("--last", type=int, default=None, help="Show only last N bars.")
@click.pass_context
@async_command
@handle_errors
async def historicals(ctx: click.Context, symbol: str, interval: str, span: str, last: int | None):
    """OHLCV historical bars."""
    async with get_authenticated_client() as client:
        bars = await client.stocks.get_historicals(symbol.upper(), interval=interval, span=span)
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
            console.print(model_table(bars, cols, title=f"Historicals — {symbol.upper()} ({interval}/{span})"))


@stocks.command()
@click.argument("symbol")
@click.option("--limit", type=int, default=10, help="Max articles to show.")
@click.pass_context
@async_command
@handle_errors
async def news(ctx: click.Context, symbol: str, limit: int):
    """News articles for a symbol."""
    async with get_authenticated_client() as client:
        articles = await client.stocks.get_news(symbol.upper())
        articles = articles[:limit]
        if _use_json(ctx):
            output_json(articles)
        else:
            cols = [
                ("published_at", "Published"),
                ("source", "Source"),
                ("title", "Title"),
            ]
            console.print(model_table(articles, cols, title=f"News — {symbol.upper()}"))


@stocks.command("quote-by-ids")
@click.argument("instrument_ids", nargs=-1, required=True)
@click.option("--bounds", default="trading", help="Session: trading, regular, extended, 24_5.")
@click.pass_context
@async_command
@handle_errors
async def quote_by_ids(ctx: click.Context, instrument_ids: tuple[str, ...], bounds: str):
    """Quotes by instrument IDs with session bounds."""
    async with get_authenticated_client() as client:
        quotes = await client.stocks.get_quotes_by_ids(list(instrument_ids), bounds=bounds)
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
            console.print(model_table(quotes, cols, title=f"Quotes by ID (bounds={bounds})"))


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


# ══════════════════════════════════════════════════════════════════════════════
#  FUTURES
# ══════════════════════════════════════════════════════════════════════════════


@cli.group()
def futures():
    """Futures contracts, quotes, account, orders, P&L."""


@futures.command("contracts")
@click.option("--symbol", default=None, help="Filter by underlying symbol.")
@click.pass_context
@async_command
@handle_errors
async def futures_contracts(ctx: click.Context, symbol: str | None):
    """List futures contracts."""
    async with get_authenticated_client() as client:
        data = await client.futures.get_contracts(symbol=symbol)
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
@click.argument("symbol_or_id")
@click.pass_context
@async_command
@handle_errors
async def indexes_fundamentals(ctx: click.Context, symbol_or_id: str):
    """Index fundamentals (high/low, 52-week range). Accepts a symbol (VIX) or UUID."""
    async with get_authenticated_client() as client:
        if _is_uuid(symbol_or_id):
            results = await client.indexes.get_fundamentals([symbol_or_id])
            if not results:
                raise InvalidSymbolError(symbol_or_id)
            data = results[0]
        else:
            data = await client.indexes.get_fundamentals_by_symbol(symbol_or_id.upper())
        label = data.symbol or symbol_or_id
        if _use_json(ctx):
            output_json(data)
        else:
            console.print(model_panel(data, title=f"Index Fundamentals — {label}"))


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
            if not data:
                console.print(f"[dim]No instruments found for category: {tag}[/dim]")
                return
            cols = [
                ("symbol", "Symbol"),
                ("name", "Name"),
                ("simple_name", "Simple Name"),
            ]
            console.print(dict_table(data, cols, title=f"Category — {tag}"))


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


@screeners.command("query")
@click.option("--indicator", "-i", multiple=True, required=True, help="Indicator in KEY=VALUE format (e.g. price_earnings_ratio=5:30). Use 'indicators' command for available keys.")
@click.option("--sort", default=None, help="Column key to sort by.")
@click.option("--direction", type=click.Choice(["ASC", "DESC"]), default="DESC", help="Sort direction.")
@click.option("--limit", default=25, help="Max results to display.")
@click.pass_context
@async_command
@handle_errors
async def screeners_query(ctx: click.Context, indicator: tuple[str, ...], sort: str | None, direction: str, limit: int):
    """Run an ad-hoc screener scan with custom filters.

    Examples:

        screeners query -i price_earnings_ratio=5:30 -i market_cap_in_billions=10:

        screeners query -i sector=Technology -i percent_change=:0 --sort percent_change --direction ASC
    """
    async with get_authenticated_client() as client:
        indicators = []
        for spec in indicator:
            if "=" not in spec:
                raise click.ClickException(f"Invalid indicator format: '{spec}'. Use KEY=VALUE (e.g. price_earnings_ratio=5:30)")
            key, val = spec.split("=", 1)
            if ":" in val:
                parts = val.split(":", 1)
                filter_cfg: dict[str, Any] = {}
                if parts[0]:
                    filter_cfg["gte"] = parts[0]
                if parts[1]:
                    filter_cfg["lte"] = parts[1]
                indicators.append({"key": key, "filter": filter_cfg})
            else:
                indicators.append({"key": key, "filter": {"eq": val}})

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
