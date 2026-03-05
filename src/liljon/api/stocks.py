"""StocksAPI: quotes, instruments, fundamentals, historicals, news."""

from __future__ import annotations

from liljon import _endpoints as ep
from liljon._http import HttpTransport
from liljon._pagination import paginate_results
from liljon.exceptions import InvalidSymbolError
from liljon.models.stocks import Fundamentals, HistoricalBar, NewsArticle, StockInstrument, StockQuote


class StocksAPI:
    """Stock data: quotes, instruments, fundamentals, historicals, news."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    async def get_quotes(
        self,
        symbols: list[str],
        bounds: str = "regular",
        include_bbo_source: bool = False,
        include_inactive: bool = False,
    ) -> list[StockQuote]:
        """Fetch real-time quotes for one or more symbols.

        Args:
            symbols: List of ticker symbols.
            bounds: Trading session - 'trading', 'regular', 'extended', '24_5'.
            include_bbo_source: Include best bid/offer source info.
            include_inactive: Include inactive instruments.
        """
        symbols_str = ",".join(s.upper() for s in symbols)
        data = await self._transport.get(
            ep.quotes(symbols_str, bounds, include_bbo_source, include_inactive)
        )
        results = data.get("results", [])
        return [StockQuote(**r) for r in results if r is not None]

    async def get_quotes_by_ids(
        self,
        instrument_ids: list[str],
        bounds: str = "regular",
        include_bbo_source: bool = False,
        include_inactive: bool = False,
    ) -> list[StockQuote]:
        """Fetch real-time quotes by instrument IDs with extended session params.

        Args:
            instrument_ids: List of instrument UUIDs.
            bounds: Trading session - 'trading', 'regular', 'extended', '24_5'.
            include_bbo_source: Include best bid/offer source info.
            include_inactive: Include inactive instruments.
        """
        ids_str = ",".join(instrument_ids)
        data = await self._transport.get(
            ep.quotes_by_ids(ids_str, bounds, include_bbo_source, include_inactive)
        )
        results = data.get("results", [])
        return [StockQuote(**r) for r in results if r is not None]

    async def get_instruments(self, symbol: str) -> list[StockInstrument]:
        """Search for instruments matching a symbol."""
        data = await self._transport.get(ep.instruments(), params={"query": symbol.upper()})
        results = data.get("results", [])
        return [StockInstrument(**r) for r in results if r is not None]

    async def get_instrument_by_id(self, instrument_id: str) -> StockInstrument:
        """Fetch a specific instrument by its ID or full URL."""
        url = instrument_id if instrument_id.startswith("http") else ep.instrument(instrument_id)
        data = await self._transport.get(url)
        return StockInstrument(**data)

    async def get_instrument_by_symbol(self, symbol: str) -> StockInstrument:
        """Resolve a symbol to its instrument, raising InvalidSymbolError if not found."""
        instruments = await self.get_instruments(symbol)
        for inst in instruments:
            if inst.symbol.upper() == symbol.upper():
                return inst
        raise InvalidSymbolError(symbol)

    async def get_fundamentals(
        self,
        symbol: str,
        bounds: str = "regular",
        include_inactive: bool = True,
    ) -> Fundamentals:
        """Fetch fundamental data for a symbol.

        Args:
            symbol: Ticker symbol.
            bounds: Session bounds - '24_5', 'regular', 'extended', 'trading'.
            include_inactive: Include inactive instruments.
        """
        params = {"bounds": bounds, "include_inactive": str(include_inactive).lower()}
        data = await self._transport.get(ep.fundamentals(symbol.upper()), params=params)
        return Fundamentals(symbol=symbol.upper(), **data)

    async def get_historicals(
        self,
        symbols: list[str],
        interval: str = "day",
        span: str = "year",
        bounds: str = "regular",
    ) -> dict[str, list[HistoricalBar]]:
        """Fetch historical OHLCV bars for one or more symbols.

        Args:
            symbols: List of ticker symbols.
            interval: Bar interval - '5minute', '10minute', 'hour', 'day', 'week'.
            span: Time span - 'day', 'week', 'month', '3month', 'year', '5year'.
            bounds: Trading session - 'regular', 'extended', 'trading', '24_5'.
        """
        symbols_str = ",".join(s.upper() for s in symbols)
        data = await self._transport.get(ep.historicals(symbols_str, interval, span, bounds))
        out: dict[str, list[HistoricalBar]] = {}
        for result in data.get("results", []):
            if result is None:
                continue
            sym = result.get("symbol", "")
            bars = result.get("historicals", [])
            out[sym] = [HistoricalBar(**b) for b in bars if b is not None]
        return out

    async def get_news(self, symbol: str | None = None) -> list[NewsArticle]:
        """Fetch news articles for a symbol."""
        url = ep.news(symbol.upper()) if symbol else ep.news()
        results = await paginate_results(self._transport, url)
        return [NewsArticle(**r) for r in results]

    async def get_latest_price(
        self,
        symbols: list[str],
        bounds: str = "regular",
        include_bbo_source: bool = False,
        include_inactive: bool = False,
    ) -> dict[str, str | None]:
        """Fetch the latest trade price for symbols. Returns {symbol: price_string}.

        Args:
            symbols: List of ticker symbols.
            bounds: Trading session - 'trading', 'regular', 'extended', '24_5'.
            include_bbo_source: Include best bid/offer source info.
            include_inactive: Include inactive instruments.
        """
        quotes = await self.get_quotes(symbols, bounds, include_bbo_source, include_inactive)
        return {q.symbol: str(q.last_trade_price) if q.last_trade_price is not None else None for q in quotes}

    async def get_fundamentals_by_id(
        self,
        instrument_id: str,
        bounds: str = "regular",
        include_inactive: bool = False,
    ) -> Fundamentals:
        """Fetch fundamentals by instrument ID with session-aware bounds.

        Args:
            instrument_id: Instrument UUID.
            bounds: Session bounds — '24_5', 'regular', 'extended', 'trading'.
            include_inactive: Include inactive instruments.
        """
        params = {"bounds": bounds, "include_inactive": str(include_inactive).lower()}
        data = await self._transport.get(ep.fundamentals_by_id(instrument_id), params=params)
        return Fundamentals(**data)

    async def get_fundamentals_history(
        self,
        instrument_ids: list[str],
        start_date: str | None = None,
    ) -> list[dict]:
        """Fetch short fundamentals history for instruments over a date range.

        Args:
            instrument_ids: List of instrument UUIDs.
            start_date: Start date (YYYY-MM-DD). Defaults to ~3 months ago.
        """
        params: dict[str, str] = {"ids": ",".join(instrument_ids)}
        if start_date:
            params["start_date"] = start_date
        data = await self._transport.get(ep.fundamentals_short(), params=params)
        return data.get("data", [])

    async def get_historicals_by_ids(
        self,
        instrument_ids: list[str],
        interval: str = "5minute",
        span: str = "day",
        bounds: str = "regular",
    ) -> list[dict]:
        """Fetch batch historicals by instrument IDs.

        Args:
            instrument_ids: List of instrument UUIDs.
            interval: Bar interval — '5minute', '10minute', 'hour', 'day', 'week'.
            span: Time span — 'day', 'week', 'month', '3month', 'year', '5year'.
            bounds: Session bounds — '24_5', 'regular', 'extended', 'trading'.
        """
        params = {
            "ids": ",".join(instrument_ids),
            "interval": interval,
            "span": span,
            "bounds": bounds,
        }
        data = await self._transport.get(ep.historicals_by_ids(), params=params)
        return data.get("results", [])
