import numpy as np
from src.models.mean_reversion import MeanReversionStrategy
from src.backtest.engine import BacktestEngine


class NelderMeadOptimizer:
    def __init__(self, candles, initial_capital=1_000_000):
        self.candles = candles
        self.engine = BacktestEngine(initial_capital=initial_capital)

        # границы параметров
        self.bounds = {
            "ma": (3, 100),
            "buy": (0.003, 0.02),
            "sell": (0.003, 0.02),
            "stop": (0.005, 0.05)
        }

    # --- целевая функция ---
    def objective(self, x):
        ma, buy, sell, stop = x

        # ограничения
        ma = int(round(ma))
        ma = np.clip(ma, *self.bounds["ma"])

        buy = np.clip(buy, *self.bounds["buy"])
        sell = np.clip(sell, *self.bounds["sell"])
        stop = np.clip(stop, *self.bounds["stop"])

        if buy >= sell:
            return 1e6  # штраф

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
        max_iter=50
    ):
        simplex = np.array(initial_simplex)

        for iteration in range(max_iter):
            # сортировка
            simplex = sorted(simplex, key=lambda x: self.objective(x))
            simplex = np.array(simplex)

            best = simplex[0]
            worst = simplex[-1]

            # центр тяжести
            centroid = np.mean(simplex[:-1], axis=0)

            # отражение
            xr = centroid + alpha * (centroid - worst)
            fr = self.objective(xr)

            f_best = self.objective(best)
            f_second = self.objective(simplex[-2])
            f_worst = self.objective(worst)

            # --- логика ---
            if f_best <= fr < f_second:
                simplex[-1] = xr
                continue

            if fr < f_best:
                # растяжение
                xe = centroid + gamma * (xr - centroid)
                if self.objective(xe) < fr:
                    simplex[-1] = xe
                else:
                    simplex[-1] = xr
                continue

            # сжатие
            xc = centroid + beta * (worst - centroid)
            if self.objective(xc) < f_worst:
                simplex[-1] = xc
                continue

            # редукция
            best = simplex[0]
            simplex = np.array([
                best + sigma * (x - best)
                for x in simplex
            ])

            print(f"Итерация {iteration}: лучший результат = {-self.objective(best):.2f}%")

        best = min(simplex, key=lambda x: self.objective(x))

        return {
            "ma": int(round(best[0])),
            "buy": best[1],
            "sell": best[2],
            "stop": best[3],
            "profit": -self.objective(best)
        }