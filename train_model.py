from pathlib import Path
from src.backtest.engine import BacktestEngine
from optimization.trainer import StrategyTrainer
from datetime import datetime

def split_data(candles):
    train = []
    test = []

    for c in candles:
        t = datetime.fromisoformat(c.time.replace("Z", ""))

        if datetime(2025, 11, 1) <= t <= datetime(2026, 1, 1):
            train.append(c)
        elif t > datetime(2026, 1, 1):
            test.append(c)

    return train, test

# === CONFIG ===
DATA_PATH = Path(r"src\data\test_candles_WUSH\TCS00A105EX7\CANDLE_INTERVAL_HOUR-1745323200-1776427200.csv")
START_CAPITAL = 1_000_000

if __name__ == "__main__":
    engine = BacktestEngine(initial_capital=START_CAPITAL)
    candles = engine.load_candles(str(DATA_PATH))

    trainer = StrategyTrainer(candles, START_CAPITAL)

    best_params, best_profit = trainer.train()

    print("\n🔥 ЛУЧШИЕ ПАРАМЕТРЫ:")
    print(best_params)
    print(f"Доходность: {best_profit}%")