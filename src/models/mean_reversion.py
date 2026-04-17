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
        
        self.ma_length = ma_length
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.stop_loss = stop_loss
        self.trade_fraction = trade_fraction
        
        self.entry_price = None

    def _moving_average(self, history: List[Candle]) -> float:
        closes = [c.close for c in history[-self.ma_length:]]
        return np.mean(closes)

    def on_candle(self, candle: Candle, history: List[Candle]) -> TradeSignal:
        if len(history) < self.ma_length:
            return TradeSignal(Signal.HOLD, candle.close, candle.time)

        ma = self._moving_average(history)

        price = candle.close
        deviation = (price - ma) / ma  # относительное отклонение

        # BUY
        if self.position == 0 and deviation < -self.buy_threshold:
            self.position = 1
            self.entry_price = price
            return TradeSignal(Signal.BUY, price, candle.time)

        # SELL (take profit)
        if self.position == 1 and deviation > self.sell_threshold:
            self.position = 0
            return TradeSignal(Signal.SELL, price, candle.time)

        # STOP LOSS
        if self.position == 1 and price < self.entry_price * (1 - self.stop_loss):
            self.position = 0
            return TradeSignal(Signal.SELL, price, candle.time)

        return TradeSignal(Signal.HOLD, price, candle.time)