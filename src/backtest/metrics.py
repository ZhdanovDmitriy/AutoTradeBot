def calculate_metrics(equity_curve: list, trades: list, initial_capital: float) -> dict:
    if not equity_curve:
        return {}
    
    equities = [e['equity'] for e in equity_curve]
    final_equity = equities[-1]
    
    # Доходность
    total_return = (final_equity - initial_capital) / initial_capital * 100
    
    # Максимальная просадка
    peak = equities[0]
    max_drawdown = 0
    for equity in equities:
        if equity > peak:
            peak = equity
        drawdown = (peak - equity) / peak * 100
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    # Количество сделок
    num_trades = len([t for t in trades if t['type'] == 'SELL'])
    
    # Win rate
    buys = [t for t in trades if t['type'] == 'BUY']
    sells = [t for t in trades if t['type'] == 'SELL']
    winning_trades = 0
    for i, sell in enumerate(sells):
        if i < len(buys):
            if sell['price'] > buys[i]['price']:
                winning_trades += 1
    win_rate = (winning_trades / len(sells) * 100) if sells else 0
    
    return {
        'total_return_%': round(total_return, 2),
        'final_equity': round(final_equity, 2),
        'max_drawdown_%': round(max_drawdown, 2),
        'num_trades': num_trades,
        'win_rate_%': round(win_rate, 2)
    }