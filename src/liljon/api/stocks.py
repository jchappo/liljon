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

    async def get_quotes(self, symbols: list[str]) -> list[StockQuote]:
        """Fetch real-time quotes for one or more symbols."""
        symbols_str = ",".join(s.upper() for s in symbols)
        data = await self._transport.get(ep.quotes(symbols_str))
        results = data.get("results", [])
        return [StockQuote(**r) for r in results if r is not None]

    async def get_quotes_by_ids(
        self,
        instrument_ids: list[str],
        bounds: str = "trading",
        include_bbo_source: bool = True,
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

    async def get_quote(self, symbol: str) -> StockQuote:
        """Fetch a single stock quote."""
        data = await self._transport.get(ep.quote(symbol.upper()))
        return StockQuote(**data)

    async def get_instruments(self, symbol: str) -> list[StockInstrument]:
        """Search for instruments matching a symbol."""
        data = await self._transport.get(ep.instruments(), params={"query": symbol.upper()})
        results = data.get("results", [])
        return [StockInstrument(**r) for r in results if r is not None]

    async def get_instrument_by_id(self, instrument_id: str) -> StockInstrument:
        """Fetch a specific instrument by its ID."""
        data = await self._transport.get(ep.instrument(instrument_id))
        return StockInstrument(**data)

    async def get_instrument_by_url(self, url: str) -> StockInstrument:
        """Fetch an instrument from its full URL."""
        data = await self._transport.get(url)
        return StockInstrument(**data)

    async def get_instrument_by_symbol(self, symbol: str) -> StockInstrument:
        """Resolve a symbol to its instrument, raising InvalidSymbolError if not found."""
        instruments = await self.get_instruments(symbol)
        for inst in instruments:
            if inst.symbol.upper() == symbol.upper():
                return inst
        raise InvalidSymbolError(symbol)

    async def get_fundamentals(self, symbol: str) -> Fundamentals:
        """Fetch fundamental data for a symbol."""
        data = await self._transport.get(ep.fundamentals(symbol.upper()))
        return Fundamentals(symbol=symbol.upper(), **data)

    async def get_historicals(
        self,
        symbol: str,
        interval: str = "day",
        span: str = "year",
        bounds: str = "regular",
    ) -> list[HistoricalBar]:
        """Fetch historical OHLCV bars for a symbol.

        Args:
            symbol: Ticker symbol.
            interval: Bar interval - '5minute', '10minute', 'hour', 'day', 'week'.
            span: Time span - 'day', 'week', 'month', '3month', 'year', '5year'.
            bounds: Trading session - 'regular', 'extended', 'trading'.
        """
        data = await self._transport.get(ep.historicals(symbol.upper(), interval, span, bounds))
        results = data.get("historicals", [])
        return [HistoricalBar(**r) for r in results if r is not None]

    async def get_news(self, symbol: str) -> list[NewsArticle]:
        """Fetch news articles for a symbol."""
        results = await paginate_results(self._transport, ep.news(symbol.upper()))
        return [NewsArticle(**r) for r in results]

    async def get_latest_price(self, symbols: list[str]) -> dict[str, str | None]:
        """Fetch the latest trade price for symbols. Returns {symbol: price_string}."""
        quotes = await self.get_quotes(symbols)
        return {q.symbol: str(q.last_trade_price) if q.last_trade_price is not None else None for q in quotes}
