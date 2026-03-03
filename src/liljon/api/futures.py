"""FuturesAPI: contracts, quotes, orders, P&L."""

from __future__ import annotations

from decimal import Decimal

from liljon import _endpoints as ep
from liljon._http import HttpTransport
from liljon._pagination import paginate_cursor, paginate_results
from liljon.models.futures import FuturesAccount, FuturesContract, FuturesOrder, FuturesQuote

# Required header for futures endpoints
_FUTURES_HEADERS = {"Rh-Contract-Protected": "true"}


class FuturesAPI:
    """Futures data: contracts, quotes, orders, and P&L."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    async def get_contracts(
        self,
        contract_ids: list[str] | None = None,
        product_ids: list[str] | None = None,
    ) -> list[FuturesContract]:
        """Fetch futures contracts by contract or product IDs.

        Args:
            contract_ids: Specific contract UUIDs to fetch.
            product_ids: Product IDs to fetch all contracts for (e.g. 'BTC', 'ES').
                          At least one of contract_ids or product_ids must be provided.
        """
        params: dict[str, str] = {}
        if contract_ids:
            params["contract_ids"] = ",".join(contract_ids)
        if product_ids:
            params["product_ids"] = ",".join(product_ids)
        if not params:
            raise ValueError("At least one of contract_ids or product_ids must be provided")
        results = await paginate_results(
            self._transport, ep.futures_contracts(), params=params, headers=_FUTURES_HEADERS
        )
        return [FuturesContract(**r) for r in results]

    async def get_contract(self, contract_id: str) -> FuturesContract:
        """Fetch a specific futures contract by ID."""
        data = await self._transport.get(ep.futures_contract(contract_id), headers=_FUTURES_HEADERS)
        return FuturesContract(**data)

    async def get_quote(self, contract_id: str) -> FuturesQuote:
        """Fetch a real-time quote for a futures contract."""
        data = await self._transport.get(ep.futures_quote(contract_id), headers=_FUTURES_HEADERS)
        return FuturesQuote(**data)

    async def get_quotes(self, contract_ids: list[str]) -> list[FuturesQuote]:
        """Fetch quotes for multiple futures contracts."""
        ids_param = ",".join(contract_ids)
        data = await self._transport.get(
            ep.futures_quotes(), params={"ids": ids_param}, headers=_FUTURES_HEADERS
        )
        results = data.get("results", [])
        return [FuturesQuote(**r) for r in results if r is not None]

    async def get_account(self) -> FuturesAccount | None:
        """Fetch the user's futures account summary."""
        results = await paginate_results(self._transport, ep.futures_accounts(), headers=_FUTURES_HEADERS)
        if results:
            return FuturesAccount(**results[0])
        return None

    async def get_orders(self) -> list[FuturesOrder]:
        """Fetch futures order history using cursor-based pagination."""
        results = await paginate_cursor(self._transport, ep.futures_orders(), headers=_FUTURES_HEADERS)
        return [FuturesOrder(**r) for r in results]

    async def get_order(self, order_id: str) -> FuturesOrder:
        """Fetch a specific futures order by ID."""
        data = await self._transport.get(ep.futures_order(order_id), headers=_FUTURES_HEADERS)
        return FuturesOrder(**data)

    async def calculate_pnl(self) -> dict[str, Decimal]:
        """Calculate realized P&L from closing futures orders.

        Only counts orders with a closing_strategy to avoid double-counting.
        """
        orders = await self.get_orders()
        realized_pnl = Decimal("0")

        for order in orders:
            if order.state != "filled" or not order.closing_strategy:
                continue
            if order.average_price and order.filled_quantity:
                value = order.average_price * order.filled_quantity
                if order.side == "sell":
                    realized_pnl += value
                else:
                    realized_pnl -= value

        return {"realized_pnl": realized_pnl}

    async def get_product(self, product_id: str) -> dict:
        """Fetch futures product metadata (contract specs).

        Args:
            product_id: Futures product ID (e.g. for /ES, /NQ).
        """
        return await self._transport.get(ep.futures_products(product_id), headers=_FUTURES_HEADERS)

    async def get_closes(self, contract_ids: list[str]) -> list[dict]:
        """Fetch previous close prices for futures contracts."""
        params = {"ids": ",".join(contract_ids)}
        data = await self._transport.get(ep.futures_closes(), params=params, headers=_FUTURES_HEADERS)
        return data.get("results", [])

    async def get_closes_range(self, contract_id: str, start: str) -> list[dict]:
        """Fetch historical close range for a futures contract.

        Args:
            contract_id: Futures contract ID.
            start: Start datetime (ISO format).
        """
        params = {"ids": contract_id, "start": start}
        data = await self._transport.get(ep.futures_closes_range(), params=params, headers=_FUTURES_HEADERS)
        return data.get("results", [])

    async def get_user_settings(self) -> dict:
        """Fetch futures user settings."""
        return await self._transport.get(ep.futures_user_settings(), headers=_FUTURES_HEADERS)

    async def get_pnl_cost_basis(self, account_id: str, contract_id: str | None = None) -> dict:
        """Fetch futures P&L and cost basis.

        Args:
            account_id: Futures account UUID.
            contract_id: Optional contract ID filter.
        """
        params = {}
        if contract_id:
            params["contractId"] = contract_id
        return await self._transport.get(
            ep.futures_pnl_cost_basis(account_id), params=params, headers=_FUTURES_HEADERS
        )

    async def get_aggregated_positions(self, account_id: str) -> list[dict]:
        """Fetch aggregated futures positions.

        Args:
            account_id: Futures account UUID.
        """
        data = await self._transport.get(
            ep.futures_aggregated_positions(account_id), headers=_FUTURES_HEADERS
        )
        return data.get("results", [data]) if "results" in data else [data]
