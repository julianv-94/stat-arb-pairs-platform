from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Deque, cast

import numpy as np


@dataclass
class TradeEvent:
    timestamp: datetime
    position: int


@dataclass
class LivePairTrader:
    symbol_a: str
    symbol_b: str
    window: int = 60
    threshold: float = 1.0
    prices_a: Deque[float] = field(default_factory=lambda: deque(maxlen=60))
    prices_b: Deque[float] = field(default_factory=lambda: deque(maxlen=60))
    position: int = 0
    trades: list[TradeEvent] = field(default_factory=list)

    def on_bar(self, bar: dict[str, object]) -> dict[str, object] | None:
        symbol = str(bar.get("sym"))
        price = float(cast(float, bar.get("c", 0)))
        ts_value = cast(float, bar.get("s") or bar.get("t") or 0)
        ts = datetime.fromtimestamp(ts_value / 1000)

        if symbol == self.symbol_a:
            self.prices_a.append(price)
        elif symbol == self.symbol_b:
            self.prices_b.append(price)
        else:
            return None

        if len(self.prices_a) < self.window or len(self.prices_b) < self.window:
            return None

        spread_series = np.log(np.array(self.prices_a)) - np.log(np.array(self.prices_b))
        z = float((spread_series[-1] - spread_series.mean()) / spread_series.std())

        old_position = self.position
        if self.position == 0:
            if z > self.threshold:
                self.position = -1
            elif z < -self.threshold:
                self.position = 1
        elif abs(z) < 0.2:
            self.position = 0

        if old_position != self.position:
            self.trades.append(TradeEvent(timestamp=ts, position=self.position))

        return {
            "ts": ts.isoformat(),
            "price_a": self.prices_a[-1],
            "price_b": self.prices_b[-1],
            "z": float(z),
            "position": self.position,
        }
