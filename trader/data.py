from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from typing import AsyncIterator, Iterable

import pandas as pd
import websockets
import yfinance as yf
from polygon import RESTClient

API_KEY = os.getenv("POLYGON_API_KEY")
_client = RESTClient(API_KEY) if API_KEY else None


def fetch_bars_polygon(symbol: str, start: str, end: str, timeframe: str = "day") -> pd.DataFrame:
    """Fetch historical bars from Polygon or fall back to yfinance."""
    if _client is None:
        df = yf.download(symbol, start=start, end=end, interval="1d" if timeframe == "day" else "1m")
        df.index.name = "timestamp"
        return df

    timespan = "day" if timeframe == "day" else "minute"
    aggs = _client.get_aggs(symbol, 1, timespan, start, end)
    records = [
        {
            "timestamp": datetime.fromtimestamp(a.timestamp / 1000),
            "open": a.open,
            "high": a.high,
            "low": a.low,
            "close": a.close,
            "volume": a.volume,
        }
        for a in aggs
    ]
    df = pd.DataFrame(records).set_index("timestamp")
    return df


async def stream_bars_polygon(symbols: Iterable[str]) -> AsyncIterator[dict[str, object]]:
    """Yield live minute bars from the Polygon WebSocket."""
    if API_KEY is None:
        raise RuntimeError("POLYGON_API_KEY required for live streaming")

    uri = "wss://socket.polygon.io/stocks"
    params = ",".join(f"A.{s}" for s in symbols)
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"action": "auth", "params": API_KEY}))
        await ws.send(json.dumps({"action": "subscribe", "params": params}))
        async for message in ws:
            data = json.loads(message)
            for bar in data:
                if bar.get("ev") == "AM":
                    yield bar
            await asyncio.sleep(0)  # allow cancellation
