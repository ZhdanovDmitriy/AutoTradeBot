from pathlib import Path
from src.backtest.engine import BacktestEngine
from src.models.ma_crossover import MovingAverageCrossover

def run_strategy_test(strategy, data_path: str):
    engine = BacktestEngine(initial_capital=100000, commission=0.001)
    candles = engine.load_candles(data_path)
    results = engine.run(strategy, candles)
    
    print(f"\n{'='*60}")
    print(f"Стратегия: {results['strategy']}")
    print(f"{'='*60}")
    for key, value in results['metrics'].items():
        print(f"{key}: {value}")
    print(f"{'='*60}\n")
    
    return results

if __name__ == '__main__':
    data_dir = Path(r"C:\Users\dzhda\OneDrive\Рабочий стол\автотрейдинг\TradeBot\src\data\test_candles_WUSH\TCS00A105EX7")
    csv_file = list(data_dir.glob('CANDLE_INTERVAL_HOUR-*.csv'))[0]
    
    print(f"📊 Запуск бэктеста на файле: {csv_file.name}")
    
    # ← Теперь стратегии будут иметь разные имена
    strategies = [
        MovingAverageCrossover(short_period=10, long_period=30),
        MovingAverageCrossover(short_period=5, long_period=20),
    ]
    
    all_results = []
    for strategy in strategies:
        results = run_strategy_test(strategy, str(csv_file))
        all_results.append(results)
    
    # Сравнение
    print("\n📈 Сравнение стратегий:")
    print(f"{'Стратегия':<25} {'Доходность':<15} {'Просадка':<15} {'Сделки'}")
    print("-" * 65)
    for r in all_results:
        m = r['metrics']
        print(f"{r['strategy']:<25} {m['total_return_%']:>10}%    {m['max_drawdown_%']:>10}%    {m['num_trades']:>5}")