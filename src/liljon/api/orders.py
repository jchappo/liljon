"""OrdersAPI: unified place/cancel for stocks, options, crypto."""

from __future__ import annotations

import logging
import uuid

from liljon import _endpoints as ep
from liljon._http import HttpTransport
from liljon._pagination import paginate_results
from liljon.exceptions import OrderError, ValidationError
from liljon.models.orders import (
    OrderFeeResult,
    OrderResult,
    OrderSessionInfo,
)

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
        extended_hours: bool = False,
        position_effect: str = "open",
        account_url: str | None = None,
        instrument_url: str | None = None,
        ref_id: str | None = None,
    ) -> OrderResult:
        """Place a stock order.

        Args:
            symbol: Ticker symbol.
            quantity: Number of shares.
            side: 'buy' or 'sell'.
            order_type: 'market', 'limit', 'stoploss', 'stoplimit'.
            time_in_force: 'gfd' (good for day), 'gtc' (good til cancelled),
                           'ioc' (immediate or cancel), 'opg' (at the open).
            price: Limit price (required for limit/stoplimit).
            stop_price: Stop price (required for stoploss/stoplimit).
            extended_hours: If True, order is valid during extended hours.
            position_effect: 'open' or 'close'.
            account_url: Account URL (auto-resolved if not provided).
            instrument_url: Instrument URL (auto-resolved if not provided).
            ref_id: Idempotency reference ID (auto-generated if not provided).
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

        market_hours = "extended_hours" if extended_hours else "regular_hours"

        payload: dict = {
            "account": account_url,
            "instrument": instrument_url,
            "symbol": symbol.upper(),
            "quantity": str(quantity),
            "side": side,
            "type": actual_type,
            "time_in_force": time_in_force,
            "trigger": trigger,
            "market_hours": market_hours,
            "position_effect": position_effect,
            "order_form_version": 7,
            "ref_id": ref_id or str(uuid.uuid4()),
        }

        if price is not None:
            payload["price"] = f"{price:.2f}"
        if stop_price is not None:
            payload["stop_price"] = f"{stop_price:.2f}"

        data = await self._transport.post(ep.stock_orders(), json=payload)

        if "id" not in data:
            raise OrderError(f"Order placement failed: {data}", data)

        return OrderResult(**data)

    async def cancel_stock_order(
        self,
        order_id: str,
        account_number: str | None = None,
    ) -> dict:
        """Cancel a pending stock order.

        Args:
            order_id: The order UUID to cancel.
            account_number: Account number (sent in request body).
        """
        payload = {}
        if account_number:
            payload["account_number"] = account_number
        data = await self._transport.post(
            ep.cancel_stock_order(order_id),
            json=payload if payload else None,
        )
        return data

    async def get_stock_orders(
        self,
        account_numbers: list[str] | None = None,
        instrument: str | None = None,
        is_closed: bool | None = None,
    ) -> list[OrderResult]:
        """Fetch stock order history with optional filtering.

        Args:
            account_numbers: Filter by account numbers.
            instrument: Filter by instrument URL.
            is_closed: Filter by closed/open status.
        """
        params: dict[str, str] = {}
        if account_numbers:
            params["account_numbers"] = ",".join(account_numbers)
        if instrument:
            params["instrument"] = instrument
        if is_closed is not None:
            params["is_closed"] = str(is_closed).lower()
        results = await paginate_results(
            self._transport, ep.stock_orders(), params=params or None,
        )
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

    async def buy_stop_limit(
        self, symbol: str, quantity: float, price: float, stop_price: float, **kwargs,
    ) -> OrderResult:
        return await self.place_stock_order(
            symbol, quantity, "buy", "stoplimit", price=price, stop_price=stop_price, **kwargs,
        )

    async def sell_market(self, symbol: str, quantity: float, **kwargs) -> OrderResult:
        return await self.place_stock_order(symbol, quantity, "sell", "market", **kwargs)

    async def sell_limit(self, symbol: str, quantity: float, price: float, **kwargs) -> OrderResult:
        return await self.place_stock_order(symbol, quantity, "sell", "limit", price=price, **kwargs)

    async def sell_stop_loss(self, symbol: str, quantity: float, stop_price: float, **kwargs) -> OrderResult:
        return await self.place_stock_order(symbol, quantity, "sell", "stoploss", stop_price=stop_price, **kwargs)

    async def sell_stop_limit(
        self, symbol: str, quantity: float, price: float, stop_price: float, **kwargs,
    ) -> OrderResult:
        return await self.place_stock_order(
            symbol, quantity, "sell", "stoplimit", price=price, stop_price=stop_price, **kwargs,
        )

    # ── Options Orders ──────────────────────────────────────────────────

    async def get_options_orders(
        self,
        account_numbers: list[str] | None = None,
        states: str | None = None,
    ) -> list[dict]:
        """Fetch options orders with optional filtering.

        Args:
            account_numbers: Account numbers to filter by.
            states: Comma-separated order states
                    (e.g. 'queued,confirmed,partially_filled').
        """
        params: dict[str, str] = {}
        if account_numbers:
            params["account_numbers"] = ",".join(account_numbers)
        if states:
            params["states"] = states
        results = await paginate_results(
            self._transport, ep.option_orders(), params=params or None,
        )
        return results

    # ── Combo Orders ────────────────────────────────────────────────────

    async def get_combo_orders(
        self,
        account_numbers: list[str] | None = None,
        states: str | None = None,
    ) -> list[dict]:
        """Fetch combo/multi-leg orders.

        Args:
            account_numbers: Account numbers to filter by.
            states: Comma-separated order states
                    (e.g. 'queued,confirmed,partially_filled').
        """
        params: dict[str, str] = {}
        if account_numbers:
            params["account_numbers"] = ",".join(account_numbers)
        if states:
            params["states"] = states
        results = await paginate_results(
            self._transport, ep.combo_orders(), params=params or None,
        )
        return results

    # ── Fee Calculation ─────────────────────────────────────────────────

    async def calculate_fees(
        self,
        instrument_id: str,
        quantity: str,
        price: str,
        side: str,
        is_otc: bool = False,
    ) -> OrderFeeResult:
        """Calculate fees for a stock order before placing it.

        Args:
            instrument_id: Instrument UUID.
            quantity: Number of shares.
            price: Price per share.
            side: 'buy' or 'sell'.
            is_otc: Whether the instrument is OTC.
        """
        payload = {
            "instrument_id": instrument_id,
            "quantity": quantity,
            "price": price,
            "side": side,
            "is_otc": is_otc,
        }
        data = await self._transport.post(ep.orders_fees(), json=payload)
        return OrderFeeResult(**data)

    # ── Order Metadata ──────────────────────────────────────────────────

    async def calculate_expiration(self) -> str:
        """Get the GTC expiration date for orders placed now.

        Returns:
            ISO datetime string for when a GTC order would expire.
        """
        data = await self._transport.get(ep.orders_calculate_expiration())
        return data["gtc_expire_datetime"]

    async def get_order_sessions(
        self,
        date: str,
        session_type: str = "ORDER_SESSION_TYPE_SELL_SHORT",
    ) -> list[OrderSessionInfo]:
        """Get trading session hours and behaviors for a date.

        Args:
            date: Date string (YYYY-MM-DD).
            session_type: Session type filter
                          (e.g. 'ORDER_SESSION_TYPE_SELL_SHORT').
        """
        params = {"date": date, "type": session_type}
        data = await self._transport.get(ep.orders_session(), params=params)
        sessions = data.get("sessions", [])
        return [OrderSessionInfo(**s) for s in sessions]
