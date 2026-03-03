"""CryptoAPI: pairs, quotes, holdings, historicals."""

from __future__ import annotations

from liljon import _endpoints as ep
from liljon._http import HttpTransport
from liljon._pagination import paginate_results
from liljon.models.crypto import CryptoHistoricalBar, CryptoHolding, CryptoPair, CryptoQuote


class CryptoAPI:
    """Crypto data: pairs, quotes, holdings, and historicals."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    async def get_pairs(self) -> list[CryptoPair]:
        """Fetch all available cryptocurrency pairs."""
        results = await paginate_results(self._transport, ep.crypto_pairs())
        return [CryptoPair(**r) for r in results]

    async def get_pair(self, pair_id: str) -> CryptoPair:
        """Fetch a specific crypto pair by ID."""
        data = await self._transport.get(ep.crypto_pair(pair_id))
        return CryptoPair(**data)

    async def get_pair_by_symbol(self, symbol: str) -> CryptoPair | None:
        """Find a crypto pair by its symbol (e.g. 'BTC')."""
        pairs = await self.get_pairs()
        symbol_upper = symbol.upper()
        for pair in pairs:
            asset_code = (pair.asset_currency or {}).get("code", "")
            if (
                pair.symbol.upper() == symbol_upper
                or (pair.code and pair.code.upper() == symbol_upper)
                or asset_code.upper() == symbol_upper
            ):
                return pair
        return None

    async def get_quote(self, pair_id: str) -> CryptoQuote:
        """Fetch a real-time quote for a crypto pair."""
        data = await self._transport.get(ep.crypto_quotes(pair_id))
        return CryptoQuote(**data)

    async def get_holdings(self) -> list[CryptoHolding]:
        """Fetch all crypto holdings in the user's account."""
        results = await paginate_results(self._transport, ep.crypto_holdings())
        return [CryptoHolding(**r) for r in results]

    async def get_historicals(
        self,
        pair_id: str,
        interval: str = "day",  
        span: str = "year",
        bounds: str = "24_7",
    ) -> list[CryptoHistoricalBar]:
        """Fetch historical OHLCV bars for a crypto pair.

        Args:
            pair_id: The crypto pair ID.
            interval: Bar interval - '1minute', '5minute', '10minute', 'hour', 'day', 'week'.
            span: Time span - 'hour', 'day', 'week', 'month', '3month', 'year', '5year'.
            bounds: Trading session - '24_7', 'regular', 'extended'.
        """
        data = await self._transport.get(ep.crypto_historicals(pair_id, interval, span, bounds))
        results = data.get("data_points", data.get("historicals", []))
        return [CryptoHistoricalBar(**r) for r in results if r is not None]
