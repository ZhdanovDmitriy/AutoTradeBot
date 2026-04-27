import os
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
import shutil
import matplotlib.pyplot as plt

from t_tech.invest import Client, CandleInterval
from t_tech.invest.constants import INVEST_GRPC_API_SANDBOX

from src.instruments.figi import get_figi_by_ticker
from src.instruments.candles import download_candles, draw_candles_with_trades
from src.enums.instrument_types import InstrumentType

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
    print(f"\n[{title}]")


# ---------- DATA SPLIT ----------

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


# ---------- DOWNLOAD ----------

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


# ---------- TRAIN ----------

def train_model(algorithm, train_candles):
    print_header(f"ОБУЧЕНИЕ: {algorithm}")

    if algorithm == "grid":
        trainer = StrategyTrainer(train_candles)
        best_params, best_profit = trainer.train()

    elif algorithm == "nm":
        optimizer = NelderMeadOptimizer(train_candles)

        initial_simplex = [
            [5,  0.001, 0.013, 0.015],
            [8,  0.001, 0.003, 0.016],
            [10, 0.008, 0.002, 0.014],
            [12, 0.013, 0.012, 0.022],
            [18, 0.003, 0.013, 0.019],
        ]

        best_params = optimizer.optimize(initial_simplex, max_iter=50)

    else:
        raise ValueError("algorithm должен быть 'grid' или 'nm'")

    if isinstance(best_params, (list, np.ndarray)):
        best_params = {
            "ma": best_params[0], "buy": best_params[1],
            "sell": best_params[2], "stop": best_params[3]
        }

    return {
        "ma": int(round(best_params.get("ma", 0))),
        "buy": float(best_params.get("buy", 0)),
        "sell": float(best_params.get("sell", 0)),
        "stop": float(best_params.get("stop", 0))
    }

# ---------- TEST ----------

def test_model(params, candles):
    strategy = MeanReversionStrategy(
        ma_length=int(params['ma']),
        buy_threshold=params['buy'],
        sell_threshold=params['sell'],
        stop_loss=params['stop']
    )

    engine = BacktestEngine(initial_capital=1_000_000)
    results = engine.run(strategy, candles)

    return results


# ---------- METRICS ----------

def calculate_metrics(results):
    trades = results.get("trades", [])
    metrics = results.get("metrics", {})

    # 🔑 Прямое извлечение по точным ключам из вашего лога
    profit_pct = metrics.get('total_return_%', 0.0)
    max_dd = metrics.get('max_drawdown_%', 0.0)
    
    # Берём количество сделок из метрик движка (надёжнее, чем len(trades))
    total_trades = metrics.get('num_trades', len(trades))
    
    # Win rate уже в процентах, как показывает ваш вывод
    success_rate = metrics.get('win_rate_%', 0.0)

    # 🛡 Fallback: если метрики вдруг пустые, считаем вручную
    if total_trades == 0 and len(trades) > 0:
        total_trades = len(trades)
        def get_pnl(t):
            return t.get("profit", t.get("pnl", 0)) if isinstance(t, dict) else getattr(t, "profit", 0)
        success_rate = sum(1 for t in trades if get_pnl(t) > 0) / total_trades * 100

    return {
        "profit_pct": profit_pct,
        "max_dd": max_dd,
        "trades": total_trades,
        "success_rate": success_rate
    }


# ---------- EVALUATION ----------

def evaluate(train, test, algorithm):
    params = train_model(algorithm, train)

    train_results = test_model(params, train)
    test_results = test_model(params, test)

    return {
        "method": algorithm,
        "params": params,
        "train": calculate_metrics(train_results),
        "test": calculate_metrics(test_results),
    }


# ---------- MAIN RUN ----------

def run(
    ticker: str,
    train_start: datetime,
    train_end: datetime,
    test_start: datetime,
    test_end: datetime,
):
    print_header("ЗАПУСК СТРАТЕГИИ")

    csv_path = download_data(ticker)

    engine = BacktestEngine()
    candles = engine.load_candles(csv_path)

    train, test = split_data(candles, train_start, train_end, test_start, test_end)

    print(f"Train candles: {len(train)}")
    print(f"Test candles: {len(test)}")

    results = []

    for algo in ["grid", "nm"]:
        results.append(evaluate(train, test, algo))

    rows = []

    for r in results:
        p = r["params"]

        rows.append({
            "Тикер": ticker,
            "Метод": r["method"],
            "MA": p["ma"],
            "Buy": p["buy"],
            "Sell": p["sell"],
            "Stop": p["stop"],

            "Прибыль обучения %": round(r["train"]["profit_pct"], 2),
            "Прибыль тест %": round(r["test"]["profit_pct"], 2),

            "Просадка макс. %": round(r["test"]["max_dd"], 2),
            "Количество сделок тест": r["test"]["trades"],
            "Успешные сделки тест%": round(r["test"]["success_rate"], 2),
        })

    df = pd.DataFrame(rows)

    print("\n================ СРАВНЕНИЕ МЕТОДОВ ================\n")
    print(df.to_string(index=False))

    return df

if __name__ == "__main__":
    run(
        ticker="WUSH",

        train_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        train_end=datetime(2025, 1, 1, tzinfo=timezone.utc),

        test_start=datetime(2025, 1, 1, tzinfo=timezone.utc),
        test_end=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )