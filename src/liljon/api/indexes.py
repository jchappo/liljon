"""IndexesAPI: instruments, quotes, options chain resolution."""

from __future__ import annotations

from liljon import _endpoints as ep
from liljon._http import HttpTransport
from liljon.exceptions import InvalidSymbolError
from liljon.models.indexes import IndexClose, IndexFundamentals, IndexInstrument, IndexQuote
from liljon.models.options import OptionChain


class IndexesAPI:
    """Index data: instruments, quotes, and option chain resolution."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    async def get_instrument(self, symbol: str) -> IndexInstrument:
        """Fetch an index instrument by symbol (SPX, NDX, VIX, RUT, XSP)."""
        data = await self._transport.get(ep.index_by_symbol(symbol.upper()))
        results = data.get("results", [])
        if not results:
            raise InvalidSymbolError(symbol)
        return IndexInstrument(**results[0])

    async def get_instrument_by_id(self, index_id: str) -> IndexInstrument:
        """Fetch an index instrument by its UUID."""
        data = await self._transport.get(ep.index_by_id(index_id))
        return IndexInstrument(**data)

    async def get_quote(self, index_id: str) -> IndexQuote:
        """Fetch the current value for an index by its instrument ID."""
        resp = await self._transport.get(ep.index_quote(index_id))
        # API wraps the payload: {"status": ..., "data": {"status": ..., "data": {actual fields}}}
        data = resp.get("data", resp)
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        return IndexQuote(**data)

    async def get_quote_by_symbol(self, symbol: str) -> IndexQuote:
        """Fetch the current value for an index by symbol."""
        instrument = await self.get_instrument(symbol)
        quote = await self.get_quote(instrument.id)
        quote.symbol = symbol.upper()
        return quote

    async def get_fundamentals(self, index_ids: list[str]) -> list[IndexFundamentals]:
        """Fetch fundamentals (high/low, 52-week range) for indexes by instrument IDs."""
        ids_str = ",".join(index_ids)
        resp = await self._transport.get(ep.index_fundamentals(ids_str))
        return [IndexFundamentals(**item["data"]) for item in resp.get("data", []) if item.get("data")]

    async def get_fundamentals_by_symbol(self, symbol: str) -> IndexFundamentals:
        """Fetch fundamentals for an index by symbol."""
        instrument = await self.get_instrument(symbol)
        results = await self.get_fundamentals([instrument.id])
        if not results:
            raise InvalidSymbolError(symbol)
        return results[0]

    async def get_closes(self, index_ids: list[str]) -> list[IndexClose]:
        """Fetch previous close values for indexes by instrument IDs."""
        ids_str = ",".join(index_ids)
        resp = await self._transport.get(ep.index_closes(ids_str))
        return [IndexClose(**item["data"]) for item in resp.get("data", []) if item.get("data")]

    async def get_close_by_symbol(self, symbol: str) -> IndexClose:
        """Fetch the previous close for an index by symbol."""
        instrument = await self.get_instrument(symbol)
        results = await self.get_closes([instrument.id])
        if not results:
            raise InvalidSymbolError(symbol)
        return results[0]

    async def get_option_chains(self, symbol: str) -> list[OptionChain]:
        """Resolve an index symbol to its tradable option chains.

        Indexes use `tradable_chain_ids` (plural array) instead of the singular
        `tradable_chain_id` that stocks use.
        """
        instrument = await self.get_instrument(symbol)
        return await self._fetch_chains(instrument)

    async def get_option_chains_by_id(self, index_id: str) -> list[OptionChain]:
        """Resolve an index UUID to its tradable option chains."""
        instrument = await self.get_instrument_by_id(index_id)
        return await self._fetch_chains(instrument)

    async def _fetch_chains(self, instrument: IndexInstrument) -> list[OptionChain]:
        chains: list[OptionChain] = []
        for chain_id in instrument.tradable_chain_ids:
            data = await self._transport.get(ep.option_chain_by_id(chain_id))
            chains.append(OptionChain(**data))
        return chains
