import itertools
from src.backtest.engine import BacktestEngine
from src.models.mean_reversion import MeanReversionStrategy


class StrategyTrainer:
    def __init__(self, candles, initial_capital=1_000_000):
        self.candles = candles
        self.engine = BacktestEngine(initial_capital=initial_capital)

    def train(self):
        best_result = None
        best_params = None

        ma_range = range(3, 100)  # можно расширить до 100
        buy_range = [0.004, 0.006, 0.0002]
        sell_range = [0.004, 0.006, 0.0002]
        stop_range = [0.008, 0.02, 0.0001]

        for ma, buy, sell, stop in itertools.product(
            ma_range, buy_range, sell_range, stop_range
        ):
            if buy >= sell:
                continue

            strategy = MeanReversionStrategy(
                ma_length=ma,
                buy_threshold=buy,
                sell_threshold=sell,
                stop_loss=stop
            )

            result = self.engine.run(strategy, self.candles)
            profit = result['metrics']['total_return_%']

            if best_result is None or profit > best_result:
                best_result = profit
                best_params = {
                    'ma': ma,
                    'buy': buy,
                    'sell': sell,
                    'stop': stop
                }

        return best_params, best_result