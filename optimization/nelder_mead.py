import numpy as np
from src.models.mean_reversion import MeanReversionStrategy
from src.backtest.engine import BacktestEngine


class NelderMeadOptimizer:
    def __init__(self, candles, initial_capital=1_000_000):
        self.candles = candles
        self.engine = BacktestEngine(initial_capital=initial_capital)

        self.bounds = {
            "ma":   (3, 30),
            "buy":  (0.000, 0.0135),
            "sell": (0.000, 0.0135),
            "stop": (0.015, 0.025)
        }

    # --- вспомогательный метод для проекции в границы ---
    def _clip_to_bounds(self, x):
        """Гарантирует, что точка лежит внутри self.bounds"""
        return np.array([
            np.clip(x[0], self.bounds["ma"][0], self.bounds["ma"][1]),
            np.clip(x[1], self.bounds["buy"][0], self.bounds["buy"][1]),
            np.clip(x[2], self.bounds["sell"][0], self.bounds["sell"][1]),
            np.clip(x[3], self.bounds["stop"][0], self.bounds["stop"][1])
        ])

    # --- целевая функция ---
    def objective(self, x):
        ma, buy, sell, stop = x

        # ma хранится как float в симплексе, округляем только здесь
        ma = int(round(ma))
        ma = np.clip(ma, *self.bounds["ma"])
        
        buy = np.clip(buy, *self.bounds["buy"])
        sell = np.clip(sell, *self.bounds["sell"])
        stop = np.clip(stop, *self.bounds["stop"])

        strategy = MeanReversionStrategy(
            ma_length=ma,
            buy_threshold=buy,
            sell_threshold=sell,
            stop_loss=stop
        )

        result = self.engine.run(strategy, self.candles)
        profit = result['metrics']['total_return_%']
        return -profit  # МИНИМИЗАЦИЯ

    # --- основной алгоритм ---
    def optimize(
        self,
        initial_simplex,
        alpha=1.0,
        gamma=2.0,
        beta=0.5,
        sigma=0.5,
        max_iter=30
    ):
        # 1. Обрезаем начальный симплекс (на случай, если он задан криво)
        simplex = np.array([self._clip_to_bounds(x) for x in initial_simplex])

        for iteration in range(max_iter):
            # Сортировка симплекса по возрастанию целевой функции
            # Примечание: sorted возвращает список, конвертируем обратно в array
            simplex = np.array(sorted(simplex, key=lambda x: self.objective(x)))

            best = simplex[0]
            worst = simplex[-1]
            centroid = np.mean(simplex[:-1], axis=0)

            # Предвычисляем значения, чтобы не запускать backtest повторно
            f_best = self.objective(best)
            f_second = self.objective(simplex[-2])
            f_worst = self.objective(worst)

            # 1. Отражение
            xr = self._clip_to_bounds(centroid + alpha * (centroid - worst))
            fr = self.objective(xr)

            if f_best <= fr < f_second:
                simplex[-1] = xr
                continue

            # 2. Растяжение
            if fr < f_best:
                xe = self._clip_to_bounds(centroid + gamma * (xr - centroid))
                fe = self.objective(xe)
                simplex[-1] = xe if fe < fr else xr
                continue

            # 3. Сжатие
            xc = self._clip_to_bounds(centroid + beta * (worst - centroid))
            fc = self.objective(xc)
            if fc < f_worst:
                simplex[-1] = xc
                continue

            # 4. Редукция (сжатие к лучшему)
            simplex = np.array([self._clip_to_bounds(best + sigma * (x - best)) for x in simplex])

            print(f"Итерация {iteration}: лучший результат = {-f_best:.2f}%")

        best = min(simplex, key=lambda x: self.objective(x))

        return {
            "ma": int(round(best[0])),
            "buy": best[1],
            "sell": best[2],
            "stop": best[3],
            "profit": -self.objective(best)
        }