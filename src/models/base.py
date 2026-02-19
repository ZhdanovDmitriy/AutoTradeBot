from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class Signal(Enum):
    BUY = 1
    SELL = -1
    HOLD = 0

@dataclass
class Candle:
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: int

@dataclass
class TradeSignal:
    signal: Signal
    price: float
    timestamp: str
    meta: dict = None

class BaseStrategy(ABC):
    """Базовый класс для всех торговых стратегий"""
    
    def __init__(self, name: str, params: dict = None):
        self.name = name
        self.params = params or {}
        self.position = 0  # 0 = нет позиции, 1 = long
        
    @abstractmethod
    def on_candle(self, candle: Candle, history: List[Candle]) -> TradeSignal:
        """Вызывается для каждой свечи. Возвращает сигнал."""
        pass
    
    def reset(self):
        """Сброс состояния перед новым прогоном"""
        self.position = 0