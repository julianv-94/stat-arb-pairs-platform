from __future__ import annotations


import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .data import fetch_bars_polygon, stream_bars_polygon
from .live import LivePairTrader

app = FastAPI(title="Stat-Arb Pairs Trader")


@app.get("/backtest")  # type: ignore[misc]
def backtest(symbol_a: str, symbol_b: str, start: str, end: str) -> dict[str, object]:
    df_a = fetch_bars_polygon(symbol_a, start, end)
    df_b = fetch_bars_polygon(symbol_b, start, end)
    df = df_a.join(df_b, lsuffix="_a", rsuffix="_b", how="inner")
    spread = np.log(df["close_a"]) - np.log(df["close_b"])
    z = (spread - spread.mean()) / spread.std()
    position = np.where(z > 1, -1, np.where(z < -1, 1, 0))
    equity = np.cumsum(position * np.diff(np.concatenate([[0.0], spread])))
    return {
        "z": z.tolist(),
        "equity": equity.tolist(),
    }


@app.websocket("/ws/live")  # type: ignore[misc]
async def ws_live(websocket: WebSocket, symbol_a: str, symbol_b: str) -> None:
    await websocket.accept()
    trader = LivePairTrader(symbol_a, symbol_b)
    try:
        async for bar in stream_bars_polygon([symbol_a, symbol_b]):
            data = trader.on_bar(bar)
            if data is not None:
                await websocket.send_json(data)
    except WebSocketDisconnect:
        return
    except Exception:
        await websocket.close()
        raise
