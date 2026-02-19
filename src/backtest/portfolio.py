class Portfolio:
    def __init__(self, initial_capital: float, commission: float = 0.001):
        self.cash = initial_capital
        self.initial_capital = initial_capital
        self.commission = commission
        self.position = 0  # количество акций
        self.entry_price = 0
        self.trades = []
        
    def buy(self, price: float, timestamp: str):
        """Покупка на 95% капитала"""
        shares = int(self.cash * 0.95 / price)
        if shares > 0:
            cost = shares * price * (1 + self.commission)
            self.cash -= cost
            self.position = shares
            self.entry_price = price
            self.trades.append({'type': 'BUY', 'price': price, 'time': timestamp, 'shares': shares})
            
    def sell(self, price: float, timestamp: str):
        """Продажа всей позиции"""
        if self.position > 0:
            revenue = self.position * price * (1 - self.commission)
            self.cash += revenue
            self.trades.append({'type': 'SELL', 'price': price, 'time': timestamp, 'shares': self.position})
            self.position = 0
            self.entry_price = 0
            
    def get_equity(self, current_price: float) -> float:
        return self.cash + (self.position * current_price)