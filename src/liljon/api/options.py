"""OptionsAPI: chains, instruments, positions, market data."""

from __future__ import annotations

from liljon import _endpoints as ep
from liljon._http import HttpTransport
from liljon._pagination import paginate_results
from liljon.models.options import OptionChain, OptionInstrument, OptionMarketData, OptionPosition


class OptionsAPI:
    """Options data: chains, instruments, positions, and greeks."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    async def get_chains(self, instrument_id: str) -> list[OptionChain]:
        """Fetch option chains for an equity instrument ID."""
        data = await self._transport.get(ep.option_chains(instrument_id))
        results = data.get("results", [])
        return [OptionChain(**r) for r in results if r is not None]

    async def get_chain_by_id(self, chain_id: str) -> OptionChain:
        """Fetch a specific option chain by its ID."""
        data = await self._transport.get(ep.option_chain_by_id(chain_id))
        return OptionChain(**data)

    async def get_instruments(
        self,
        chain_id: str,
        expiration_dates: list[str] | None = None,
        option_type: str | None = None,
        state: str = "active",
    ) -> list[OptionInstrument]:
        """Fetch option instruments (contracts) for a chain.

        Args:
            chain_id: The option chain ID.
            expiration_dates: Filter by expiration dates (YYYY-MM-DD).
            option_type: 'call' or 'put'.
            state: Instrument state filter (default: 'active').
        """
        params: dict[str, str] = {"chain_id": chain_id, "state": state}
        if expiration_dates:
            params["expiration_dates"] = ",".join(expiration_dates)
        if option_type:
            params["type"] = option_type

        results = await paginate_results(
            self._transport, ep.option_instruments(), params=params
        )
        return [OptionInstrument(**r) for r in results]

    async def get_instrument_by_id(self, option_id: str) -> OptionInstrument:
        """Fetch a specific option contract by ID."""
        data = await self._transport.get(ep.option_instrument(option_id))
        return OptionInstrument(**data)

    async def get_market_data(self, option_id: str) -> OptionMarketData:
        """Fetch real-time market data (greeks, prices) for an option contract."""
        data = await self._transport.get(ep.option_marketdata(option_id))
        return OptionMarketData(**data)

    async def get_positions(self) -> list[OptionPosition]:
        """Fetch all open option positions."""
        results = await paginate_results(self._transport, ep.option_positions())
        return [OptionPosition(**r) for r in results]

    async def get_orders(self) -> list[dict]:
        """Fetch option order history."""
        return await paginate_results(self._transport, ep.option_orders())
