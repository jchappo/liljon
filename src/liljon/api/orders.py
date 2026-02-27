"""OrdersAPI: unified place/cancel for stocks, options, crypto."""

from __future__ import annotations

import logging

from liljon import _endpoints as ep
from liljon._http import HttpTransport
from liljon._pagination import paginate_results
from liljon.exceptions import OrderError, ValidationError
from liljon.models.orders import OrderResult

logger = logging.getLogger(__name__)


class OrdersAPI:
    """Unified order placement and management for stocks, options, and crypto."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    # ── Stock Orders ────────────────────────────────────────────────────

    async def place_stock_order(
        self,
        symbol: str,
        quantity: float,
        side: str,
        order_type: str = "market",
        time_in_force: str = "gfd",
        price: float | None = None,
        stop_price: float | None = None,
        account_url: str | None = None,
        instrument_url: str | None = None,
    ) -> OrderResult:
        """Place a stock order.

        Args:
            symbol: Ticker symbol.
            quantity: Number of shares.
            side: 'buy' or 'sell'.
            order_type: 'market', 'limit', 'stoploss', 'stoplimit'.
            time_in_force: 'gfd' (good for day), 'gtc' (good til cancelled), 'ioc', 'opg'.
            price: Limit price (required for limit/stoplimit).
            stop_price: Stop price (required for stoploss/stoplimit).
            account_url: Account URL (auto-resolved if not provided).
            instrument_url: Instrument URL (auto-resolved if not provided).
        """
        if order_type in ("limit", "stoplimit") and price is None:
            raise ValidationError("price is required for limit/stoplimit orders")
        if order_type in ("stoploss", "stoplimit") and stop_price is None:
            raise ValidationError("stop_price is required for stoploss/stoplimit orders")
        if quantity <= 0:
            raise ValidationError(f"quantity must be positive, got {quantity}")

        # Resolve instrument URL if not provided
        if not instrument_url:
            from liljon.api.stocks import StocksAPI
            stocks_api = StocksAPI(self._transport)
            instrument = await stocks_api.get_instrument_by_symbol(symbol)
            instrument_url = instrument.url

        # Resolve account URL if not provided
        if not account_url:
            from liljon.api.account import AccountAPI
            accounts = await AccountAPI(self._transport).get_accounts()
            if not accounts:
                raise OrderError("No accounts found")
            account_url = accounts[0].url

        trigger = "immediate"
        if order_type in ("stoploss", "stoplimit"):
            trigger = "stop"

        actual_type = order_type
        if order_type == "stoploss":
            actual_type = "market"
        elif order_type == "stoplimit":
            actual_type = "limit"

        payload: dict = {
            "account": account_url,
            "instrument": instrument_url,
            "symbol": symbol.upper(),
            "quantity": str(quantity),
            "side": side,
            "type": actual_type,
            "time_in_force": time_in_force,
            "trigger": trigger,
        }

        if price is not None:
            payload["price"] = f"{price:.2f}"
        if stop_price is not None:
            payload["stop_price"] = f"{stop_price:.2f}"

        data = await self._transport.post(ep.stock_orders(), json=payload)

        if "id" not in data:
            raise OrderError(f"Order placement failed: {data}", data)

        return OrderResult(**data)

    async def cancel_stock_order(self, order_id: str) -> dict:
        """Cancel a pending stock order."""
        data = await self._transport.post(ep.cancel_stock_order(order_id))
        return data

    async def get_stock_orders(self) -> list[OrderResult]:
        """Fetch stock order history."""
        results = await paginate_results(self._transport, ep.stock_orders())
        return [OrderResult(**r) for r in results]

    async def get_stock_order(self, order_id: str) -> OrderResult:
        """Fetch a specific stock order by ID."""
        data = await self._transport.get(ep.stock_order(order_id))
        return OrderResult(**data)

    # ── Convenience wrappers ────────────────────────────────────────────

    async def buy_market(self, symbol: str, quantity: float, **kwargs) -> OrderResult:
        return await self.place_stock_order(symbol, quantity, "buy", "market", **kwargs)

    async def buy_limit(self, symbol: str, quantity: float, price: float, **kwargs) -> OrderResult:
        return await self.place_stock_order(symbol, quantity, "buy", "limit", price=price, **kwargs)

    async def buy_stop_loss(self, symbol: str, quantity: float, stop_price: float, **kwargs) -> OrderResult:
        return await self.place_stock_order(symbol, quantity, "buy", "stoploss", stop_price=stop_price, **kwargs)

    async def sell_market(self, symbol: str, quantity: float, **kwargs) -> OrderResult:
        return await self.place_stock_order(symbol, quantity, "sell", "market", **kwargs)

    async def sell_limit(self, symbol: str, quantity: float, price: float, **kwargs) -> OrderResult:
        return await self.place_stock_order(symbol, quantity, "sell", "limit", price=price, **kwargs)

    async def sell_stop_loss(self, symbol: str, quantity: float, stop_price: float, **kwargs) -> OrderResult:
        return await self.place_stock_order(symbol, quantity, "sell", "stoploss", stop_price=stop_price, **kwargs)
