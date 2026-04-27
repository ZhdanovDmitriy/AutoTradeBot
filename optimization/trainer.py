import itertools
import numpy as np
from src.backtest.engine import BacktestEngine
from src.models.mean_reversion import MeanReversionStrategy

class StrategyTrainer:
    def __init__(self, candles, initial_capital=1_000_000):
        self.candles = candles
        self.engine = BacktestEngine(initial_capital=initial_capital)

    def train(self):
        best_result = None
        best_params = None

        # Формат: (min, max, step)
        param_spaces = {
            "ma":   (3, 30, 2),          # шаг 1 для целых
            "buy":  (0.001, 0.013, 0.004),
            "sell": (0.002, 0.013, 0.004),
            "stop": (0.015, 0.025, 0.005)
        }

        # 1. Генерация сетки значений
        grids = {}
        for name, (start, stop, step) in param_spaces.items():
            if isinstance(start, float):
                # Округляем до 6 знаков, чтобы избежать багов float precision (0.0040000000001)
                grids[name] = np.round(np.arange(start, stop + step/2, step), 6)
            else:
                grids[name] = range(start, stop + 1, step)

        # (Опционально) Вывод количества комбинаций для контроля
        total = len(grids["ma"]) * len(grids["buy"]) * len(grids["sell"]) * len(grids["stop"])
        print(f"Исследуемых точек: {total}")

        # 2. Перебор сетки
        for ma, buy, sell, stop in itertools.product(grids["ma"], grids["buy"], grids["sell"], grids["stop"]):

            strategy = MeanReversionStrategy(
                ma_length=int(ma),
                buy_threshold=float(buy),
                sell_threshold=float(sell),
                stop_loss=float(stop)
            )

            result = self.engine.run(strategy, self.candles)
            profit = result['metrics']['total_return_%']

            if best_result is None or profit > best_result:
                best_result = profit
                best_params = {
                    'ma': int(ma),
                    'buy': float(buy),
                    'sell': float(sell),
                    'stop': float(stop)
                }

        return best_params, best_result