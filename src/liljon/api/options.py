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

    async def get_aggregate_positions(
        self,
        account_numbers: list[str] | None = None,
        nonzero: bool = True,
    ) -> list[dict]:
        """Fetch aggregated option positions grouped by strategy.

        Args:
            account_numbers: Account numbers to filter by.
            nonzero: Only return non-zero positions.
        """
        params: dict[str, str] = {"nonzero": str(nonzero)}
        if account_numbers:
            params["account_numbers"] = ",".join(account_numbers)
        results = await paginate_results(self._transport, ep.option_aggregate_positions(), params=params)
        return results

    async def get_strategies(self, strategy_codes: list[str]) -> list[dict]:
        """Fetch option strategy definitions/pricing.

        Args:
            strategy_codes: Strategy codes (e.g. '{option_id}_L1').
        """
        params = {"strategy_codes": ",".join(strategy_codes)}
        data = await self._transport.get(ep.option_strategies(), params=params)
        return data.get("results", [])

    async def get_chain_collateral(self, chain_id: str, account_number: str | None = None) -> dict:
        """Fetch collateral requirements for an option chain.

        Args:
            chain_id: Option chain ID.
            account_number: Account to check collateral for.
        """
        params = {}
        if account_number:
            params["account_number"] = account_number
        return await self._transport.get(ep.option_chain_collateral(chain_id), params=params)

    async def get_events(
        self,
        account_numbers: list[str] | None = None,
        chain_ids: list[str] | None = None,
    ) -> list[dict]:
        """Fetch option events (expirations, assignments, exercises).

        Args:
            account_numbers: Account numbers to filter by.
            chain_ids: Chain IDs to filter by.
        """
        params: dict[str, str] = {}
        if account_numbers:
            params["account_numbers"] = ",".join(account_numbers)
        if chain_ids:
            params["chain_ids"] = ",".join(chain_ids)
        results = await paginate_results(self._transport, ep.option_events(), params=params)
        return results

    async def get_market_data_batch(self, option_ids: list[str]) -> list[OptionMarketData]:
        """Fetch batch option market data (greeks, prices) for multiple contracts.

        Args:
            option_ids: List of option instrument IDs.
        """
        params = {"ids": ",".join(option_ids)}
        data = await self._transport.get(ep.option_marketdata_batch(), params=params)
        results = data.get("results", [])
        return [OptionMarketData(**r) for r in results if r is not None]

    async def get_strategy_quotes(
        self,
        ids: list[str],
        ratios: list[str] | None = None,
        types: list[str] | None = None,
    ) -> dict:
        """Fetch strategy-level quotes with greeks.

        Args:
            ids: Option instrument IDs.
            ratios: Ratio quantities for each leg.
            types: Position types ('long', 'short') for each leg.
        """
        params: dict[str, str] = {"ids": ",".join(ids)}
        if ratios:
            params["ratios"] = ",".join(ratios)
        if types:
            params["types"] = ",".join(types)
        return await self._transport.get(ep.option_strategy_quotes(), params=params)

    async def get_pnl_chart(
        self,
        legs: str,
        order_price: str,
        quantity: str,
        underlying_price: str | None = None,
    ) -> dict:
        """Fetch options profit-and-loss chart data.

        Args:
            legs: Leg definitions (URL-encoded strategy legs).
            order_price: Order price.
            quantity: Number of contracts.
            underlying_price: Current underlying price.
        """
        params: dict[str, str] = {
            "legs": legs,
            "order_price": order_price,
            "quantity": quantity,
        }
        if underlying_price:
            params["underlying_price"] = underlying_price
        return await self._transport.get(ep.option_pnl_chart(), params=params)

    async def get_breakevens(self, strategy_code: str, average_cost: str) -> dict:
        """Fetch breakeven price calculations for an option position.

        Args:
            strategy_code: Strategy code (e.g. '{option_id}_L1').
            average_cost: Average cost of the position.
        """
        params = {"strategy_code": strategy_code, "average_cost": average_cost}
        return await self._transport.get(ep.option_breakevens(), params=params)
