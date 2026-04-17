from pathlib import Path
from src.backtest.engine import BacktestEngine
from src.models.mean_reversion import MeanReversionStrategy

DATA_PATH = Path(r"src\data\test_candles_GOLD\BBG000VJ5YR4\CANDLE_INTERVAL_HOUR-1745326800-1776430800.csv")

BEST_PARAMS = {
    'ma': 5,
    'buy': 0.005497702598571777,
    'sell': 0.010497702598571777,
    'stop': 0.012424846649169926
}

if __name__ == "__main__":
    engine = BacktestEngine(initial_capital=1_000_000)
    candles = engine.load_candles(str(DATA_PATH))

    strategy = MeanReversionStrategy(
        ma_length=BEST_PARAMS['ma'],
        buy_threshold=BEST_PARAMS['buy'],
        sell_threshold=BEST_PARAMS['sell'],
        stop_loss=BEST_PARAMS['stop']
    )

    results = engine.run(strategy, candles)

    print(results['metrics'])