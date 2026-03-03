"""DiscoveryAPI: analyst ratings, hedge fund activity, insider trading, similar instruments."""

from __future__ import annotations

from liljon import _endpoints as ep
from liljon._http import HttpTransport
from liljon.models.discovery import (
    AnalystRating,
    ChartBounds,
    Earnings,
    EquitySummary,
    EtpDetails,
    HedgeFundSummary,
    HedgeFundTransactions,
    InsiderSummary,
    InsiderTransactions,
    MarketIndex,
    NbboSummary,
    ShortInterest,
    SimilarInstruments,
)


class DiscoveryAPI:
    """Discovery data: analyst ratings, hedge funds, insiders, short interest, and more."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    # ── Analyst Ratings ──────────────────────────────────────────────────

    async def get_ratings(self, instrument_id: str) -> AnalystRating:
        """Fetch analyst ratings (buy/hold/sell, price targets) for an instrument."""
        data = await self._transport.get(ep.ratings(instrument_id))
        return AnalystRating(**data)

    async def get_ratings_batch(self, instrument_ids: list[str]) -> list[AnalystRating]:
        """Fetch analyst ratings for multiple instruments."""
        ids_str = ",".join(instrument_ids)
        data = await self._transport.get(ep.ratings_batch(), params={"ids": ids_str})
        results = data.get("results", [data]) if "results" in data else [data]
        return [AnalystRating(**r) for r in results if r is not None]

    # ── Hedge Fund Activity ──────────────────────────────────────────────

    async def get_hedgefund_summary(self, instrument_id: str) -> HedgeFundSummary:
        """Fetch hedge fund activity summary (sentiment, quarterly aggregates)."""
        data = await self._transport.get(ep.hedgefunds_summary(instrument_id))
        return HedgeFundSummary(**data)

    async def get_hedgefund_transactions(self, instrument_id: str) -> HedgeFundTransactions:
        """Fetch detailed hedge fund transactions (individual manager trades)."""
        data = await self._transport.get(ep.hedgefunds_transactions(instrument_id))
        return HedgeFundTransactions(**data)

    # ── Insider Trading ──────────────────────────────────────────────────

    async def get_insider_summary(self, instrument_id: str) -> InsiderSummary:
        """Fetch insider trading summary (sentiment, monthly aggregates)."""
        data = await self._transport.get(ep.insiders_summary(instrument_id))
        return InsiderSummary(**data)

    async def get_insider_transactions(self, instrument_id: str) -> InsiderTransactions:
        """Fetch detailed insider transactions (individual trades by officers)."""
        data = await self._transport.get(ep.insiders_transactions(instrument_id))
        return InsiderTransactions(**data)

    # ── Short Interest ───────────────────────────────────────────────────

    async def get_short_interest(self, instrument_id: str) -> ShortInterest:
        """Fetch short interest data (fee, inventory, daily fee) for an instrument."""
        data = await self._transport.get(ep.shorting(instrument_id))
        return ShortInterest(**data)

    # ── Equity Summary ───────────────────────────────────────────────────

    async def get_equity_summary(self, instrument_id: str) -> EquitySummary:
        """Fetch equity summary — daily net buy/sell transaction flow."""
        data = await self._transport.get(ep.equity_summary(instrument_id))
        return EquitySummary(**data)

    # ── Earnings ─────────────────────────────────────────────────────────

    async def get_earnings(self, instrument_id: str) -> Earnings:
        """Fetch earnings data for an instrument."""
        instrument_url = f"https://api.robinhood.com/instruments/{instrument_id}/"
        data = await self._transport.get(ep.earnings(), params={"instrument": instrument_url})
        return Earnings(**data)

    # ── Similar Instruments ──────────────────────────────────────────────

    async def get_similar(self, instrument_id: str) -> SimilarInstruments:
        """Fetch similar instrument recommendations."""
        data = await self._transport.get(ep.similar_instruments(instrument_id))
        return SimilarInstruments(**data)

    # ── Market Indices ───────────────────────────────────────────────────

    async def get_market_indices(self, symbols: list[str] | None = None) -> list[MarketIndex]:
        """Fetch market index summaries (S&P 500, Nasdaq, etc.).

        Args:
            symbols: Index symbols to fetch (e.g. ['SPX', 'NDX', 'DJX', 'VIX', 'RUT']).
                     If None, fetches all active indices.
        """
        # 1. List index instruments and filter to active ones
        listing = await self._transport.get(ep.indexes())
        instruments = listing.get("results", [])
        active = [i for i in instruments if i.get("state") == "active"]
        if symbols:
            upper = {s.upper() for s in symbols}
            active = [i for i in active if i.get("symbol", "").upper() in upper]
        if not active:
            return []

        ids = [i["id"] for i in active]
        ids_str = ",".join(ids)

        # 2. Fetch current values and previous closes in parallel-safe sequence
        values_resp = await self._transport.get(ep.index_values(ids_str))
        closes_resp = await self._transport.get(ep.index_closes(ids_str))

        # Build lookup maps: instrument_id -> data
        val_map: dict[str, dict] = {}
        for item in values_resp.get("data", []):
            d = item.get("data", {})
            if d:
                val_map[d.get("instrument_id") or d.get("id", "")] = d

        close_map: dict[str, dict] = {}
        for item in closes_resp.get("data", []):
            d = item.get("data", {})
            if d:
                close_map[d.get("id", "")] = d

        # 3. Assemble MarketIndex objects
        from decimal import Decimal

        results: list[MarketIndex] = []
        for inst in active:
            iid = inst["id"]
            val_data = val_map.get(iid, {})
            close_data = close_map.get(iid, {})

            current = Decimal(val_data["value"]) if val_data.get("value") else None
            prev = Decimal(close_data["close_value"]) if close_data.get("close_value") else None
            pct = None
            if current is not None and prev is not None and prev != 0:
                pct = ((current - prev) / prev * 100).quantize(Decimal("0.01"))

            results.append(
                MarketIndex(
                    key=inst.get("symbol", ""),
                    name=inst.get("simple_name"),
                    value=current,
                    previous_close=prev,
                    percent_change=pct,
                )
            )
        return results

    # ── Chart Bounds ─────────────────────────────────────────────────────

    async def get_chart_bounds(self) -> ChartBounds:
        """Fetch chart time bounds based on current market hours."""
        data = await self._transport.get(ep.bonfire_chart_bounds())
        return ChartBounds(**data)

    # ── ETP Details ──────────────────────────────────────────────────────

    async def get_etp_details(self, instrument_id: str) -> EtpDetails:
        """Fetch ETP (ETF/ETN) details — AUM, expense ratio, holdings, performance."""
        data = await self._transport.get(ep.bonfire_etp_details(instrument_id))
        return EtpDetails(**data)

    # ── NBBO Summary ─────────────────────────────────────────────────────

    async def get_nbbo_summary(self, instrument_id: str) -> NbboSummary:
        """Fetch NBBO (National Best Bid/Offer) summary for an instrument."""
        data = await self._transport.get(ep.bonfire_nbbo_summary(instrument_id))
        return NbboSummary(**data)

    # ── Search ───────────────────────────────────────────────────────────

    async def search(self, query: str) -> list[dict]:
        """Unified search for stocks, crypto, lists, futures.

        Returns raw result sections (each with content nested under 'content' key).
        """
        params = {
            "query": query,
            "content_types": "instruments,currency_pairs,active_futures,market_indexes",
            "exclude_sports": "true",
            "query_context": "default",
            "user_origin": "US",
        }
        data = await self._transport.get(ep.bonfire_search(), params=params)
        return data.get("results", [])
