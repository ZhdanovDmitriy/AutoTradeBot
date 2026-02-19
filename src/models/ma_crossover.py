from typing import List
from src.models.base import BaseStrategy, Candle, TradeSignal, Signal
import numpy as np

class MovingAverageCrossover(BaseStrategy):
    def __init__(self, short_period: int = 10, long_period: int = 30):
        # ← Измените эту строку - добавляем параметры в имя
        super().__init__(f'MA_Crossover_{short_period}_{long_period}', 
                        {'short': short_period, 'long': long_period})
        self.short_period = short_period
        self.long_period = long_period
        
    def on_candle(self, candle: Candle, history: List[Candle]) -> TradeSignal:
        if len(history) < self.long_period:
            return TradeSignal(Signal.HOLD, candle.close, candle.time)
        
        closes = [c.close for c in history[-self.long_period:]]
        short_ma = np.mean(closes[-self.short_period:])
        long_ma = np.mean(closes)
        
        # Золотой крест — покупка
        if short_ma > long_ma and self.position == 0:
            self.position = 1
            return TradeSignal(Signal.BUY, candle.close, candle.time)
        # Мёртвый крест — продажа
        elif short_ma < long_ma and self.position == 1:
            self.position = 0
            return TradeSignal(Signal.SELL, candle.close, candle.time)
        
        return TradeSignal(Signal.HOLD, candle.close, candle.time)