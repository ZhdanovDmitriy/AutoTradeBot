from typing import List
import random
from src.models.base import BaseStrategy, Candle, TradeSignal, Signal

class RandomStrategy(BaseStrategy):
    """
    Стратегия, которая открывает и закрывает сделки случайным образом.
    Полезно для проверки корректности бэктест-движка.
    """
    
    def __init__(self, buy_probability: float = 0.1, sell_probability: float = 0.1, seed: int = None):
        """
        Args:
            buy_probability: Вероятность покупки на каждой свече (0.0 - 1.0)
            sell_probability: Вероятность продажи на каждой свече (0.0 - 1.0)
            seed: Seed для воспроизводимости результатов (None = случайный)
        """
        name = f'Random_B{buy_probability}_S{sell_probability}'
        if seed is not None:
            name += f'_seed{seed}'
        
        super().__init__(name, {
            'buy_prob': buy_probability,
            'sell_prob': sell_probability,
            'seed': seed
        })
        
        self.buy_probability = buy_probability
        self.sell_probability = sell_probability
        
        # Инициализируем random с seed для воспроизводимости
        if seed is not None:
            random.seed(seed)
        
    def on_candle(self, candle: Candle, history: List[Candle]) -> TradeSignal:
        # Если уже есть позиция — пробуем закрыть
        if self.position == 1:
            if random.random() < self.sell_probability:
                self.position = 0
                return TradeSignal(Signal.SELL, candle.close, candle.time)
            return TradeSignal(Signal.HOLD, candle.close, candle.time)
        
        # Если нет позиции — пробуем открыть
        else:
            if random.random() < self.buy_probability:
                self.position = 1
                return TradeSignal(Signal.BUY, candle.close, candle.time)
            return TradeSignal(Signal.HOLD, candle.close, candle.time)
    
    def reset(self):
        """Сброс состояния + перезапуск random с тем же seed"""
        super().reset()
        if self.params.get('seed') is not None:
            random.seed(self.params['seed'])