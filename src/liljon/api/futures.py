"""FuturesAPI: contracts, products, quotes, orders, historicals, sessions, P&L."""

from __future__ import annotations

import uuid
from decimal import Decimal

from liljon import _endpoints as ep
from liljon._http import HttpTransport
from liljon._pagination import paginate_cursor, paginate_results
from liljon.models.futures import (
    FuturesAccount,
    FuturesBuyingPower,
    FuturesClose,
    FuturesCloseRange,
    FuturesContract,
    FuturesFundamentals,
    FuturesHistoricalBar,
    FuturesMarginRequirement,
    FuturesOrder,
    FuturesProduct,
    FuturesQuote,
    FuturesTradingSession,
)

# Required header for futures endpoints
_FUTURES_HEADERS = {"Rh-Contract-Protected": "true"}


def _unwrap_marketdata(data: dict) -> list[dict]:
    """Unwrap the nested status/data structure used by marketdata futures endpoints.

    Shape: {"status": "SUCCESS", "data": [{"status": "SUCCESS", "data": <payload>}, ...]}
    Returns the list of inner payloads.
    """
    items = data.get("data", [])
    return [item["data"] for item in items if isinstance(item, dict) and item.get("data") is not None]


class FuturesAPI:
    """Futures data: contracts, products, quotes, orders, historicals, sessions, and P&L."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    # ── Contracts ─────────────────────────────────────────────────────────────

    async def get_contracts(
        self,
        contract_ids: list[str] | None = None,
        product_ids: list[str] | None = None,
    ) -> list[FuturesContract]:
        """Fetch futures contracts by contract or product IDs.

        Args:
            contract_ids: Specific contract UUIDs to fetch.
            product_ids: Product IDs to fetch all contracts for.
        """
        params: dict[str, str] = {}
        if contract_ids:
            params["contractIds"] = ",".join(contract_ids)
        if product_ids:
            params["productIds"] = ",".join(product_ids)
        if not params:
            raise ValueError("At least one of contract_ids or product_ids must be provided")
        data = await self._transport.get(ep.futures_contracts(), params=params, headers=_FUTURES_HEADERS)
        results = data.get("results", [])
        return [FuturesContract(**r) for r in results if r is not None]

    async def get_contract(self, contract_id: str) -> FuturesContract:
        """Fetch a specific futures contract by ID."""
        data = await self._transport.get(ep.futures_contract(contract_id), headers=_FUTURES_HEADERS)
        return FuturesContract(**data)

    async def get_contract_by_symbol(self, symbol: str) -> FuturesContract:
        """Fetch a futures contract by symbol (e.g. SILK26, MNQH26, ESH26).

        The symbol should be without the leading slash and exchange suffix.
        """
        data = await self._transport.get(
            ep.futures_contract_by_symbol(symbol.upper()), headers=_FUTURES_HEADERS
        )
        return FuturesContract(**data["result"])

    # ── Products ──────────────────────────────────────────────────────────────

    async def get_product(self, product_id: str) -> FuturesProduct:
        """Fetch futures product metadata (contract specs).

        Args:
            product_id: Futures product UUID.
        """
        data = await self._transport.get(ep.futures_products(product_id), headers=_FUTURES_HEADERS)
        return FuturesProduct(**data)

    # ── Quotes ────────────────────────────────────────────────────────────────

    async def get_quote(self, contract_id: str) -> FuturesQuote:
        """Fetch a real-time quote for a futures contract."""
        data = await self._transport.get(
            ep.futures_quotes(), params={"ids": contract_id}, headers=_FUTURES_HEADERS
        )
        payloads = _unwrap_marketdata(data)
        if payloads:
            return FuturesQuote(**payloads[0])
        return FuturesQuote(instrument_id=contract_id)

    async def get_quotes(self, contract_ids: list[str]) -> list[FuturesQuote]:
        """Fetch quotes for multiple futures contracts."""
        ids_param = ",".join(contract_ids)
        data = await self._transport.get(
            ep.futures_quotes(), params={"ids": ids_param}, headers=_FUTURES_HEADERS
        )
        return [FuturesQuote(**p) for p in _unwrap_marketdata(data)]

    # ── Closes ────────────────────────────────────────────────────────────────

    async def get_closes(self, contract_ids: list[str]) -> list[FuturesClose]:
        """Fetch previous close prices for futures contracts."""
        params = {"ids": ",".join(contract_ids)}
        data = await self._transport.get(ep.futures_closes(), params=params, headers=_FUTURES_HEADERS)
        return [FuturesClose(**p) for p in _unwrap_marketdata(data)]

    async def get_closes_range(self, contract_id: str, start: str) -> list[FuturesCloseRange]:
        """Fetch historical close range for a futures contract.

        Args:
            contract_id: Futures contract UUID.
            start: Start datetime (ISO format, e.g. 2026-01-01T00:00:00Z).
        """
        params = {"ids": contract_id, "start": start}
        data = await self._transport.get(ep.futures_closes_range(), params=params, headers=_FUTURES_HEADERS)
        # closesrange inner data is an array of daily entries
        payloads = _unwrap_marketdata(data)
        if payloads and isinstance(payloads[0], list):
            return [FuturesCloseRange(**entry) for entry in payloads[0]]
        return [FuturesCloseRange(**p) for p in payloads]

    # ── Historicals ───────────────────────────────────────────────────────────

    async def get_historicals(
        self,
        contract_id: str,
        interval: str = "5minute",
        start: str | None = None,
    ) -> list[FuturesHistoricalBar]:
        """Fetch historical OHLCV bars for a futures contract.

        Args:
            contract_id: Futures contract UUID.
            interval: Candle interval (e.g. '5minute', '10minute', 'hour', 'day').
            start: Start datetime (ISO format). Defaults to current session.
        """
        params: dict[str, str] = {"ids": contract_id, "interval": interval}
        if start:
            params["start"] = start
        data = await self._transport.get(ep.futures_historicals(), params=params, headers=_FUTURES_HEADERS)
        payloads = _unwrap_marketdata(data)
        if payloads and isinstance(payloads[0], dict):
            return [FuturesHistoricalBar(**bar) for bar in payloads[0].get("data_points", [])]
        return []

    # ── Fundamentals ──────────────────────────────────────────────────────────

    async def get_fundamentals(self, contract_ids: list[str]) -> list[FuturesFundamentals]:
        """Fetch session fundamentals (open/high/low/volume) for futures contracts.

        Args:
            contract_ids: One or more contract UUIDs.
        """
        params = {"ids": ",".join(contract_ids)}
        data = await self._transport.get(ep.futures_fundamentals(), params=params, headers=_FUTURES_HEADERS)
        return [FuturesFundamentals(**p) for p in _unwrap_marketdata(data)]

    # ── Margin ────────────────────────────────────────────────────────────────

    async def get_margin_requirement(
        self,
        contract_id: str,
        margin_type: str = "MARGIN_TYPE_OVERNIGHT",
        account_type: str = "ACCOUNT_TYPE_CASH",
    ) -> FuturesMarginRequirement:
        """Fetch margin requirement for a futures contract.

        Args:
            contract_id: Contract UUID.
            margin_type: Margin type (default MARGIN_TYPE_OVERNIGHT).
            account_type: Account type (default ACCOUNT_TYPE_CASH).
        """
        params = {
            "contractId": contract_id,
            "marginType": margin_type,
            "accountType": account_type,
        }
        data = await self._transport.get(
            ep.futures_margin_requirement(), params=params, headers=_FUTURES_HEADERS
        )
        return FuturesMarginRequirement(**data)

    # ── Trading Sessions ──────────────────────────────────────────────────────

    async def get_trading_sessions(self, contract_id: str, date: str) -> FuturesTradingSession:
        """Fetch trading session schedule for a contract on a given date.

        Args:
            contract_id: Contract UUID.
            date: Date in YYYY-MM-DD format.
        """
        data = await self._transport.get(
            ep.futures_trading_sessions(contract_id, date), headers=_FUTURES_HEADERS
        )
        return FuturesTradingSession(**data)

    # ── Buying Power ──────────────────────────────────────────────────────────

    async def get_buying_power(self, account_number: str) -> FuturesBuyingPower:
        """Fetch futures buying power for an account.

        Args:
            account_number: Numeric account number (not UUID).
        """
        data = await self._transport.get(ep.futures_buying_power(account_number), headers=_FUTURES_HEADERS)
        return FuturesBuyingPower(**data)

    # ── Account & Orders ──────────────────────────────────────────────────────

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

    async def place_order(
        self,
        contract_id: str,
        side: str,
        quantity: int,
        account_id: str,
        order_type: str = "LIMIT",
        limit_price: Decimal | str | None = None,
        stop_price: Decimal | str | None = None,
        time_in_force: str = "GFD",
    ) -> FuturesOrder:
        """Place a futures order.

        Args:
            contract_id: Futures contract UUID.
            side: ``"BUY"`` or ``"SELL"``.
            quantity: Number of contracts.
            account_id: Futures account UUID.
            order_type: ``"MARKET"``, ``"LIMIT"``, or ``"STOP_MARKET"``.
                Robinhood futures does not support stop-limit; use
                ``"STOP_MARKET"`` for stop orders.
            limit_price: Required for LIMIT orders.
            stop_price: Required for STOP_MARKET orders.
            time_in_force: ``"GFD"`` (good for day) or ``"GTC"``
                (good til cancelled).
        """
        order_trigger = "IMMEDIATE"
        payload_order_type = order_type

        if order_type in ("STOP_MARKET", "STOP_LIMIT"):
            order_trigger = "STOP"
            payload_order_type = "MARKET"
            if stop_price is None:
                raise ValueError("stop_price is required for stop orders")

        payload: dict = {
            "accountId": account_id,
            "quantity": str(quantity),
            "orderType": payload_order_type,
            "orderTrigger": order_trigger,
            "timeInForce": time_in_force,
            "refId": str(uuid.uuid4()),
            "legs": [
                {
                    "legId": "A",
                    "contractId": contract_id,
                    "contractType": "OUTRIGHT",
                    "ratioQuantity": 1,
                    "orderSide": side.upper(),
                }
            ],
        }
        if limit_price is not None:
            payload["limitPrice"] = str(limit_price)
        if stop_price is not None:
            payload["stopPrice"] = str(stop_price)

        data = await self._transport.post(
            ep.futures_orders(), json=payload, headers=_FUTURES_HEADERS
        )
        return FuturesOrder(**data)

    async def replace_order(
        self,
        order_id: str,
        quantity: int,
        limit_price: Decimal | str,
        account_id: str | None = None,
    ) -> FuturesOrder:
        """Replace (edit) a pending futures order.

        Robinhood futures does not support atomic replace — this
        cancels the original order and places a new one with the
        updated price/quantity.

        Args:
            order_id: The existing order UUID to replace.
            quantity: New number of contracts.
            limit_price: New limit price.
            account_id: Futures account UUID. Fetched from the existing
                order if not provided.
        """
        original = await self.get_order(order_id)
        if not account_id:
            account_id = original.account_id

        contract_id = original.contract_id
        side = original.side or "BUY"

        await self.cancel_order(order_id, account_id=account_id)

        return await self.place_order(
            contract_id=contract_id,
            side=side,
            quantity=quantity,
            account_id=account_id,
            order_type=original.order_type or "LIMIT",
            limit_price=limit_price,
            time_in_force=original.time_in_force or "GFD",
        )

    async def cancel_order(self, order_id: str, account_id: str | None = None) -> FuturesOrder:
        """Cancel a pending futures order by ID.

        Args:
            order_id: The order UUID to cancel.
            account_id: Futures account UUID. If not provided, it is
                fetched from the order itself.
        """
        if not account_id:
            order = await self.get_order(order_id)
            account_id = order.account_id
        data = await self._transport.post(
            ep.cancel_futures_order(order_id),
            json={"accountId": account_id},
            headers=_FUTURES_HEADERS,
        )
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

    # ── Settings & Positions ──────────────────────────────────────────────────

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
