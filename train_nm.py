from pathlib import Path
from src.backtest.engine import BacktestEngine
from optimization.nelder_mead import NelderMeadOptimizer

DATA_PATH = Path(r"src\data\test_candles_GOLD\BBG000VJ5YR4\CANDLE_INTERVAL_HOUR-1745326800-1776430800.csv")

if __name__ == "__main__":
    engine = BacktestEngine(initial_capital=1_000_000)
    candles = engine.load_candles(str(DATA_PATH))

    # --- начальный симплекс ---
    initial_simplex = [
        [5, 0.005, 0.01, 0.012],
        [8, 0.007, 0.012, 0.014],
        [10, 0.006, 0.011, 0.014],
        [12, 0.008, 0.013, 0.015],
        [18, 0.009, 0.014, 0.018],
    ]

    optimizer = NelderMeadOptimizer(candles)

    best_params = optimizer.optimize(initial_simplex, max_iter=50)

    print("\n🔥 ЛУЧШИЕ ПАРАМЕТРЫ (Nelder-Mead):")
    print(best_params)