import os
import numpy as np
from pathlib import Path
from datetime import datetime
import shutil
import matplotlib.pyplot as plt

from t_tech.invest import Client, CandleInterval
from t_tech.invest.constants import INVEST_GRPC_API_SANDBOX

from src.instruments.figi import get_figi_by_ticker
from src.instruments.candles import draw_candles_with_trades
from src.enums.instrument_types import InstrumentType
from src.instruments.candles import download_candles, draw_candles

from src.backtest.engine import BacktestEngine
from optimization.trainer import StrategyTrainer
from optimization.nelder_mead import NelderMeadOptimizer
from src.models.mean_reversion import MeanReversionStrategy


# ================= CONFIG =================

TOKEN = os.getenv("TINKOFF_TOKEN")
ACCOUNT_ID = os.getenv("TINKOFF_ACCOUNT")

DATA_PATH = Path("data_cache")

# ==========================================


def print_header(title):
    print(f"[{title}]")


from datetime import timezone

def split_data(candles, train_start, train_end, test_start, test_end):
    train, test = [], []

    for c in candles:
        t = datetime.fromisoformat(c.time.replace("Z", "+00:00"))

        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)

        if train_start <= t <= train_end:
            train.append(c)
        elif test_start <= t <= test_end:
            test.append(c)

    return train, test


def download_data(ticker):
    print_header("ЗАГРУЗКА ДАННЫХ")

    if DATA_PATH.exists():
        shutil.rmtree(DATA_PATH)
    DATA_PATH.mkdir(parents=True, exist_ok=True)

    with Client(TOKEN, target=INVEST_GRPC_API_SANDBOX) as client:
        figi = get_figi_by_ticker(client, ticker, InstrumentType.UNSPECIFIED)

        print(f"Тикер: {ticker}")
        print(f"FIGI: {figi}")

        csv_path = download_candles(
            client,
            figi,
            days=1000,
            candle_interval_type=CandleInterval.CANDLE_INTERVAL_HOUR,
            path=str(DATA_PATH)
        )

    return csv_path


def train_model(algorithm, train_candles):
    print("\n")
    print_header("ОБУЧЕНИЕ МОДЕЛИ")

    if algorithm == "grid":
        print("Метод: ПОИСК ПО СЕТКЕ\n")

        trainer = StrategyTrainer(train_candles)
        best_params, best_profit = trainer.train()

        print("\nЛучшие параметры:")
        print(best_params)
        print(f"Доходность: {best_profit:.2f}%")

        return best_params

    elif algorithm == "nm":
        print("Метод: НЕЛДЕР–МИД\n")

        optimizer = NelderMeadOptimizer(train_candles)
        '''
        initial_simplex = [
            [5,  0.001, 0.013, 0.015],
            [8,  0.003, 0.003, 0.016],
            [5, 0.003, 0.004, 0.014],
            [12, 0.013, 0.012, 0.022],
            [13, 0.010, 0.010, 0.019],
        ]
        '''
        initial_simplex = [
            [10,  0.002, 0.002, 0.015],
            [8,  0.007, 0.007, 0.010],
            [5, 0.008, 0.004, 0.014],
            [11, 0.004, 0.012, 0.016],
            [18, 0.003, 0.002, 0.010],
        ]
        

        best_params = optimizer.optimize(initial_simplex, max_iter=50)

        print("\nЛучшие параметры:")
        sig_fig_keys = {'buy', 'sell', 'stop'}

        print({
            k: f"{v:.2g}" if k in sig_fig_keys and isinstance(v, (float, np.floating)) else v 
            for k, v in best_params.items()
        })

        return best_params

    else:
        raise ValueError("algorithm должен быть 'grid' или 'nm'")


def test_model(params, test_candles):
    print_header("ТЕСТИРОВАНИЕ МОДЕЛИ")

    strategy = MeanReversionStrategy(
        ma_length=int(params['ma']),
        buy_threshold=params['buy'],
        sell_threshold=params['sell'],
        stop_loss=params['stop']
    )

    engine = BacktestEngine(initial_capital=1_000_000)

    results = engine.run(strategy, test_candles)

    print("\nРезультаты тестирования:")
    print(results['metrics'])

    return results


def plot_results(csv_path, trades, ma_length):
    print_header("ГРАФИК СДЕЛОК")

    draw_candles_with_trades(
        csv_path,
        trades,
        ma_length=ma_length,
        title=""
    )

    plt.show()


# ================= MAIN =================

def run(
    ticker: str,
    train_start: datetime,
    train_end: datetime,
    test_start: datetime,
    test_end: datetime,
    algorithm: str = "nm"
):
    print_header("ЗАПУСК СТРАТЕГИИ")

    # 1. загрузка
    csv_path = download_data(ticker)

    # 2. загрузка в память
    engine = BacktestEngine()
    candles = engine.load_candles(csv_path)

    # 3. split
    train, test = split_data(candles, train_start, train_end, test_start, test_end)

    print(f"\nTrain candles: {len(train)}")
    print(f"Test candles: {len(test)}")

    # 4. обучение
    params = train_model(algorithm, train)

    # 5. тест
    results = test_model(params, test)

    # 6. график
    plot_results(csv_path, results['trades'], params['ma'])

    print_header("ЗАВЕРШЕНО")


# ================= ENTRY =================

if __name__ == "__main__":
    run(
        ticker="SBERP",

        train_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        train_end=datetime(2025, 1, 1, tzinfo=timezone.utc),

        test_start=datetime(2025, 1, 1, tzinfo=timezone.utc),
        test_end=datetime(2026, 1, 1, tzinfo=timezone.utc),

        algorithm="nm" #nm или grid
    )
    '''
    run(
        ticker="GLDRUB",

        train_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        train_end=datetime(2025, 1, 1, tzinfo=timezone.utc),

        test_start=datetime(2025, 1, 1, tzinfo=timezone.utc),
        test_end=datetime(2026, 1, 1, tzinfo=timezone.utc),

        algorithm="grid" #nm или grid
    )
    run(
        ticker="GLDRUB",

        train_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        train_end=datetime(2025, 1, 1, tzinfo=timezone.utc),

        test_start=datetime(2025, 1, 1, tzinfo=timezone.utc),
        test_end=datetime(2026, 1, 1, tzinfo=timezone.utc),

        algorithm="nm" #nm или grid
    )
    run(
        ticker="WUSH",

        train_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        train_end=datetime(2025, 1, 1, tzinfo=timezone.utc),

        test_start=datetime(2025, 1, 1, tzinfo=timezone.utc),
        test_end=datetime(2026, 1, 1, tzinfo=timezone.utc),

        algorithm="grid" #nm или grid
    )
    run(
        ticker="WUSH",

        train_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        train_end=datetime(2025, 1, 1, tzinfo=timezone.utc),

        test_start=datetime(2025, 1, 1, tzinfo=timezone.utc),
        test_end=datetime(2026, 1, 1, tzinfo=timezone.utc),

        algorithm="nm" #nm или grid
    )
    run(
        ticker="SBERP",

        train_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        train_end=datetime(2025, 1, 1, tzinfo=timezone.utc),

        test_start=datetime(2025, 1, 1, tzinfo=timezone.utc),
        test_end=datetime(2026, 1, 1, tzinfo=timezone.utc),

        algorithm="grid" #nm или grid
    )
    run(
        ticker="SBERP",

        train_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        train_end=datetime(2025, 1, 1, tzinfo=timezone.utc),

        test_start=datetime(2025, 1, 1, tzinfo=timezone.utc),
        test_end=datetime(2026, 1, 1, tzinfo=timezone.utc),

        algorithm="nm" #nm или grid
    )
    '''