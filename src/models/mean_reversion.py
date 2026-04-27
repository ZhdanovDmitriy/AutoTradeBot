import numpy as np
from typing import List
from src.models.base import BaseStrategy, Candle, TradeSignal, Signal


class MeanReversionStrategy(BaseStrategy):
    def __init__(
        self,
        ma_length: int,
        buy_threshold: float,
        sell_threshold: float,
        stop_loss: float,
        trade_fraction: float = 0.1
    ):
        super().__init__(
            name=f"MeanReversion(ma={ma_length}, buy={buy_threshold}, sell={sell_threshold}, sl={stop_loss})"
        )

        self.prev_ma = None
        self.ma_length = ma_length

        # 🔥 фиксированная трендовая MA (внутри файла)
        self.trend_ma_length = 20

        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.stop_loss = stop_loss
        self.trade_fraction = trade_fraction

        self.entry_price = None
        self.entry_ma = None

    def _moving_average(self, history: List[Candle], length=None) -> float:
        if length is None:
            length = self.ma_length
        closes = [c.close for c in history[-length:]]
        return np.mean(closes)

    def on_candle(self, candle: Candle, history: List[Candle]) -> TradeSignal:
        if len(history) < max(self.ma_length, self.trend_ma_length):
            return TradeSignal(Signal.HOLD, candle.close, candle.time)

        # --- основная MA (сигнальная) ---
        ma = self._moving_average(history, self.ma_length)

        # --- трендовая MA (фильтр) ---
        trend_ma = self._moving_average(history, self.trend_ma_length)

        price = candle.close
        deviation = (price - ma) / ma

        # 🔥 фильтр тренда (УЖЕ НЕ ШУМОВОЙ)
        trend_is_up = price > trend_ma

        # BUY
        if (
            self.position == 0
            and deviation < -self.buy_threshold
            and trend_is_up
        ):
            self.position = 1
            self.entry_price = price
            self.entry_ma = ma

            return TradeSignal(Signal.BUY, price, candle.time)

        # SELL (take profit)
        if self.position == 1 and deviation > self.sell_threshold:
            self.position = 0
            self.entry_price = None
            self.entry_ma = None
            return TradeSignal(Signal.SELL, price, candle.time)

        # STOP LOSS (от MA входа)
        if self.position == 1 and price < self.entry_ma * (1 - self.stop_loss):
            self.position = 0
            self.entry_price = None
            self.entry_ma = None
            return TradeSignal(Signal.SELL, price, candle.time)

        return TradeSignal(Signal.HOLD, price, candle.time)