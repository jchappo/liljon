"""Test bounds parameter on stocks API methods."""
import asyncio
import json
from liljon.client import RobinhoodClient

BOUNDS_VALUES = ["regular", "extended", "trading", "24_5"]
SYMBOL = "AAPL"


async def main():
    async with RobinhoodClient() as client:
        await client.try_restore_session()

        # Get instrument ID for later tests
        inst = await client.stocks.get_instrument_by_symbol(SYMBOL)
        iid = inst.id
        print(f"{SYMBOL} instrument_id: {iid}\n")

        # --- get_quotes ---
        print("=" * 60)
        print("get_quotes")
        print("=" * 60)
        for bounds in BOUNDS_VALUES:
            try:
                quotes = await client.stocks.get_quotes([SYMBOL], bounds=bounds)
                q = quotes[0]
                print(f"  bounds={bounds:10s}  last_trade={q.last_trade_price}  extended={q.last_extended_hours_trade_price}")
            except Exception as e:
                print(f"  bounds={bounds:10s}  ERROR: {e}")

        # --- get_quotes_by_ids ---
        print("\n" + "=" * 60)
        print("get_quotes_by_ids")
        print("=" * 60)
        for bounds in BOUNDS_VALUES:
            try:
                quotes = await client.stocks.get_quotes_by_ids([iid], bounds=bounds)
                q = quotes[0]
                print(f"  bounds={bounds:10s}  last_trade={q.last_trade_price}  extended={q.last_extended_hours_trade_price}")
            except Exception as e:
                print(f"  bounds={bounds:10s}  ERROR: {e}")

        # --- get_fundamentals ---
        print("\n" + "=" * 60)
        print("get_fundamentals")
        print("=" * 60)
        for bounds in BOUNDS_VALUES:
            try:
                f = await client.stocks.get_fundamentals(SYMBOL, bounds=bounds)
                print(f"  bounds={bounds:10s}  market_cap={f.market_cap}  pe_ratio={f.pe_ratio}")
            except Exception as e:
                print(f"  bounds={bounds:10s}  ERROR: {e}")

        # --- get_fundamentals_by_id ---
        print("\n" + "=" * 60)
        print("get_fundamentals_by_id")
        print("=" * 60)
        for bounds in BOUNDS_VALUES:
            try:
                f = await client.stocks.get_fundamentals_by_id(iid, bounds=bounds)
                print(f"  bounds={bounds:10s}  market_cap={f.market_cap}  pe_ratio={f.pe_ratio}")
            except Exception as e:
                print(f"  bounds={bounds:10s}  ERROR: {e}")

        # --- get_fundamentals_history ---
        print("\n" + "=" * 60)
        print("get_fundamentals_history")
        print("=" * 60)
        for bounds in BOUNDS_VALUES:
            try:
                data = await client.stocks.get_fundamentals_history([iid], bounds=bounds)
                count = len(data)
                sample = data[0] if data else {}
                print(f"  bounds={bounds:10s}  records={count}  sample_keys={list(sample.keys())[:5]}")
            except Exception as e:
                print(f"  bounds={bounds:10s}  ERROR: {e}")

        # --- get_latest_price ---
        print("\n" + "=" * 60)
        print("get_latest_price")
        print("=" * 60)
        for bounds in BOUNDS_VALUES:
            try:
                prices = await client.stocks.get_latest_price([SYMBOL], bounds=bounds)
                print(f"  bounds={bounds:10s}  price={prices.get(SYMBOL)}")
            except Exception as e:
                print(f"  bounds={bounds:10s}  ERROR: {e}")

        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
