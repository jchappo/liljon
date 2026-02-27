"""AccountAPI: profiles, positions, watchlists, dividends."""

from __future__ import annotations

from liljon import _endpoints as ep
from liljon._http import HttpTransport
from liljon._pagination import paginate_results
from liljon.api.stocks import StocksAPI
from liljon.models.account import (
    AccountProfile,
    Dividend,
    PhoenixAccount,
    PortfolioProfile,
    Position,
    Watchlist,
    WatchlistItem,
)


class AccountAPI:
    """Account data: profiles, positions, watchlists, and dividends."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    async def get_accounts(self) -> list[AccountProfile]:
        """Fetch all accounts for the authenticated user."""
        results = await paginate_results(self._transport, ep.accounts())
        return [AccountProfile(**r) for r in results]

    async def get_account(self, account_id: str) -> AccountProfile:
        """Fetch a specific account by ID."""
        data = await self._transport.get(ep.account(account_id))
        return AccountProfile(**data)

    async def get_portfolio(self, account_id: str) -> PortfolioProfile:
        """Fetch portfolio profile (balances, P&L) for an account."""
        data = await self._transport.get(ep.portfolio(account_id))
        return PortfolioProfile(**data)

    async def get_phoenix_account(self) -> PhoenixAccount:
        """Fetch the unified Phoenix account snapshot."""
        data = await self._transport.get(ep.phoenix_account())
        return PhoenixAccount(**data)

    async def get_positions(self, nonzero: bool = True) -> list[Position]:
        """Fetch stock positions, optionally only non-zero quantity."""
        params = {"nonzero": "true"} if nonzero else {}
        results = await paginate_results(self._transport, ep.positions(), params=params)
        return [Position(**r) for r in results]

    async def get_open_stock_positions(self, account_number: str | None = None) -> list[Position]:
        """Fetch open stock positions (non-zero quantity)."""
        params: dict[str, str] = {"nonzero": "true"}
        if account_number:
            params["account_number"] = account_number
        results = await paginate_results(self._transport, ep.positions(), params=params)
        return [Position(**r) for r in results]

    async def get_watchlists(self) -> list[Watchlist]:
        """Fetch all watchlists with their items for the authenticated user.

        The list endpoint only returns watchlist metadata (names/IDs), so we
        fetch each watchlist's items via the /midlands/lists/items/ endpoint.
        Some watchlist types (e.g. options) don't support the items endpoint.
        """
        data = await self._transport.get(ep.all_watchlists(), params={"owner_type": "custom"})
        results = data.get("results", [])
        watchlists: list[Watchlist] = []
        for r in results:
            wl_id = r.get("id")
            items: list[WatchlistItem] = []
            if wl_id:
                try:
                    items_data = await self._transport.get(ep.watchlist_items(wl_id))
                    raw_items = items_data.get("results", [])
                    items = [WatchlistItem(**i) for i in raw_items if isinstance(i, dict)]
                except Exception:
                    pass
            watchlists.append(Watchlist(
                id=wl_id,
                url=r.get("url"),
                name=r.get("name"),
                display_name=r.get("display_name"),
                items=items,
            ))
        return watchlists

    async def create_watchlist(self, name: str) -> Watchlist:
        """Create a new custom watchlist with the given name."""
        payload = {"display_name": name}
        data = await self._transport.post(ep.all_watchlists(), json=payload)
        raw_items = data.get("instruments", data.get("items", []))
        items = [
            WatchlistItem(**i) if isinstance(i, dict) else WatchlistItem(instrument_url=i)
            for i in raw_items
        ]
        return Watchlist(
            id=data.get("id"),
            url=data.get("url"),
            name=data.get("name"),
            display_name=data.get("display_name"),
            items=items,
        )

    async def add_symbols_to_watchlist(
        self, symbols: list[str], name: str = "Main"
    ) -> dict:
        """Add symbols to a named watchlist via the midlands bulk-update endpoint."""
        watchlist_id = await self._resolve_watchlist_id(name)
        stocks_api = StocksAPI(self._transport)
        items = []
        for symbol in symbols:
            instrument = await stocks_api.get_instrument_by_symbol(symbol)
            items.append({
                "object_type": "instrument",
                "object_id": instrument.id,
                "operation": "create",
            })
        payload = {watchlist_id: items}
        return await self._transport.post(ep.watchlist_bulk_update(), json=payload)

    async def remove_symbols_from_watchlist(
        self, symbols: list[str], name: str = "Main"
    ) -> dict:
        """Remove symbols from a named watchlist via the midlands bulk-update endpoint."""
        watchlist_id = await self._resolve_watchlist_id(name) 
        stocks_api = StocksAPI(self._transport)
        items = []
        for symbol in symbols:
            instrument = await stocks_api.get_instrument_by_symbol(symbol)
            items.append({
                "object_type": "instrument",
                "object_id": instrument.id,
                "operation": "delete",
            })
        payload = {watchlist_id: items}
        return await self._transport.post(ep.watchlist_bulk_update(), json=payload)

    async def _resolve_watchlist_id(self, name: str) -> str:
        """Find a watchlist by display_name and return its id, or raise ValueError."""
        watchlists = await self.get_watchlists()
        for wl in watchlists:
            if wl.display_name == name:
                if wl.id is None:
                    raise ValueError(f"Watchlist '{name}' has no id")
                return wl.id
        raise ValueError(f"Watchlist '{name}' not found")

    async def get_dividends(self) -> list[Dividend]:
        """Fetch dividend history."""
        results = await paginate_results(self._transport, ep.dividends())
        return [Dividend(**r) for r in results]
