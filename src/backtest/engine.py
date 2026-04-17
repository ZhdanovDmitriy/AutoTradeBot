import pandas as pd
import ast
from typing import List
from src.models.base import BaseStrategy, Candle, Signal
from src.backtest.portfolio import Portfolio
from src.backtest.metrics import calculate_metrics

class BacktestEngine:
    def __init__(self, initial_capital: float = 100000, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        
    def _parse_price(self, value) -> float:
        """Парсинг цены из формата {'units': X, 'nano': Y}"""
        if isinstance(value, str):
            data = ast.literal_eval(value)
            return data['units'] + data['nano'] / 1_000_000_000
        return float(value)
    
    def load_candles(self, csv_path: str) -> List[Candle]:
        df = pd.read_csv(csv_path)
        candles = []
        for _, row in df.iterrows():
            candles.append(Candle(
                time=row['time'],
                open=self._parse_price(row['open']),
                high=self._parse_price(row['high']),
                low=self._parse_price(row['low']),
                close=self._parse_price(row['close']),
                volume=int(row['volume'])
            ))
        return candles
    
    def run(self, strategy: BaseStrategy, candles: List[Candle]) -> dict:
        portfolio = Portfolio(self.initial_capital, self.commission)
        equity_curve = []
        history = []
        
        for candle in candles:
            signal = strategy.on_candle(candle, history)
            
            if signal.signal == Signal.BUY and portfolio.position == 0:
                portfolio.buy(signal.price, candle.time,fraction=0.1)
            elif signal.signal == Signal.SELL and portfolio.position > 0:
                portfolio.sell(signal.price, candle.time)
            
            equity_curve.append({
                'time': candle.time,
                'equity': portfolio.get_equity(candle.close),
                'position': portfolio.position
            })
            
            history.append(candle)
        
        metrics = calculate_metrics(equity_curve, portfolio.trades, self.initial_capital)
        
        return {
            'strategy': strategy.name,
            'metrics': metrics,
            'trades': portfolio.trades,
            'equity_curve': equity_curve
        }