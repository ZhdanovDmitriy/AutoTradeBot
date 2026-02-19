from t_tech.invest.caching.market_data_cache.cache import MarketDataCache
from t_tech.invest.caching.market_data_cache.cache_settings import (
    MarketDataCacheSettings,
)
from t_tech.invest.utils import now
from pathlib import Path
from datetime import timedelta
import os
import shutil
import re

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def download_candles(client, cur_figi, days, candle_interval_type, path):
    """
    Скачивает свечи и сохраняет их в CSV файл
    """
    cache_path = Path(path)
    figi_dir = cache_path / cur_figi
    
    if figi_dir.exists():
        print(f"🗑️  Очищаем старый кэш: {figi_dir}")
        shutil.rmtree(figi_dir)
    
    figi_dir.mkdir(parents=True, exist_ok=True)
    
    settings = MarketDataCacheSettings(base_cache_dir=cache_path)
    market_data_cache = MarketDataCache(settings=settings, services=client)
    
    candles_list = []
    
    print(f"📥 Загрузка свечей для FIGI: {cur_figi}...")
    print(f"📅 Период: {now() - timedelta(days=days)} → {now()}")
    
    try:
        for candle in market_data_cache.get_all_candles(
            figi=cur_figi,
            from_=now() - timedelta(days=days),
            interval=candle_interval_type,
        ):
            # 🔥 Сохраняем цены как словари, а не как строки Quotation
            candles_list.append({
                'time': candle.time,
                'open': {'units': candle.open.units, 'nano': candle.open.nano},
                'high': {'units': candle.high.units, 'nano': candle.high.nano},
                'low': {'units': candle.low.units, 'nano': candle.low.nano},
                'close': {'units': candle.close.units, 'nano': candle.close.nano},
                'volume': candle.volume,
                'is_complete': candle.is_complete,
                'candle_source': candle.candle_source
            })
    except FileNotFoundError as e:
        print(f"⚠️  Ошибка кэша: {e}")
        if cache_path.exists():
            shutil.rmtree(cache_path)
            cache_path.mkdir(parents=True, exist_ok=True)
        market_data_cache = MarketDataCache(settings=settings, services=client)
        for candle in market_data_cache.get_all_candles(
            figi=cur_figi,
            from_=now() - timedelta(days=days),
            interval=candle_interval_type,
        ):
            candles_list.append({
                'time': candle.time,
                'open': {'units': candle.open.units, 'nano': candle.open.nano},
                'high': {'units': candle.high.units, 'nano': candle.high.nano},
                'low': {'units': candle.low.units, 'nano': candle.low.nano},
                'close': {'units': candle.close.units, 'nano': candle.close.nano},
                'volume': candle.volume,
                'is_complete': candle.is_complete,
                'candle_source': candle.candle_source
            })
    
    if not candles_list:
        print("⚠️  Свечи не найдены!")
        return None
    
    df = pd.DataFrame(candles_list)
    
    start_ts = int(df['time'].min().timestamp())
    end_ts = int(df['time'].max().timestamp())
    
    filename = f"CANDLE_INTERVAL_HOUR-{start_ts}-{end_ts}.csv"
    filepath = figi_dir / filename
    
    # 🔥 Сохраняем словари как JSON-строки
    df.to_csv(filepath, index=False, encoding='utf-8')
    
    print(f"\n✅ Свечи сохранены в: {filepath}")
    print(f"📊 Всего свечей: {len(df)}")
    print(f"📈 Диапазон: {df['time'].min()} → {df['time'].max()}")
    
    return str(filepath)


def parse_price(price_value):
    """
    Парсит цену из различных форматов в float:
    - Словарь: {'units': 92, 'nano': 260000000}
    - Строка-словарь: "{'units': 92, 'nano': 260000000}"
    - Строка-Quotation: "Quotation(units=103, nano=900000000)"
    """
    if pd.isna(price_value) or price_value is None or price_value == '':
        return None
    
    try:
        # Если уже словарь
        if isinstance(price_value, dict):
            units = price_value.get('units', 0)
            nano = price_value.get('nano', 0)
            return float(units) + float(nano) / 1_000_000_000
        
        # Если строка
        price_str = str(price_value).strip()
        
        # 🔥 Формат: Quotation(units=103, nano=900000000)
        quotation_match = re.match(r'Quotation\(units=(-?\d+),\s*nano=(-?\d+)\)', price_str)
        if quotation_match:
            units = int(quotation_match.group(1))
            nano = int(quotation_match.group(2))
            return float(units) + float(nano) / 1_000_000_000
        
        # 🔥 Формат: {'units': 92, 'nano': 260000000}
        if price_str.startswith('{') and price_str.endswith('}'):
            # Удаляем кавычки если есть
            price_str = price_str.strip('"').strip("'")
            import ast
            price_dict = ast.literal_eval(price_str)
            units = price_dict.get('units', 0)
            nano = price_dict.get('nano', 0)
            return float(units) + float(nano) / 1_000_000_000
        
        print(f"⚠️  Неизвестный формат цены: {price_str}")
        return None
        
    except Exception as e:
        print(f"⚠️  Ошибка парсинга цены: {price_value}, {e}")
        return None


def load_candle_data(filepath):
    """
    Загружает данные свечей из CSV файла
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Файл не найден: {filepath}")
    
    df = pd.read_csv(filepath)
    df['time'] = pd.to_datetime(df['time'])
    
    # Парсим цены
    price_columns = ['open', 'high', 'low', 'close']
    for col in price_columns:
        df[col] = df[col].apply(parse_price)
    
    # Парсим volume
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    
    # Парсим is_complete
    df['is_complete'] = df['is_complete'].apply(lambda x: True if str(x) == 'True' else False)
    
    # Парсим candle_source
    df['candle_source'] = pd.to_numeric(df['candle_source'], errors='coerce')
    
    # 🔥 Удаляем строки с None ценами
    df = df.dropna(subset=['open', 'high', 'low', 'close'])
    
    if len(df) == 0:
        # 🔥 Показываем отладочную информацию
        print(f"⚠️  Файл: {filepath}")
        print(f"📊 Строк всего: {len(pd.read_csv(filepath))}")
        raise ValueError("Нет валидных данных для отображения после парсинга!")
    
    print(f"✅ Загружено {len(df)} валидных свечей")
    print(f"💰 Диапазон цен: {df['close'].min():.2f} - {df['close'].max():.2f}")
    
    return df


def draw_candles(filepath, title="Candlestick Chart", figsize=(14, 8), 
                 show_volume=True, save_path=None):
    """
    Рисует свечной график из CSV файла
    """
    df = load_candle_data(filepath)
    
    if show_volume:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, 
                                        gridspec_kw={'height_ratios': [3, 1]},
                                        sharex=True)
    else:
        fig, ax1 = plt.subplots(figsize=figsize)
        ax2 = None
    
    color_up = '#26a69a'
    color_down = '#ef5350'
    
    for idx, row in df.iterrows():
        x = row['time']
        open_price = row['open']
        close_price = row['close']
        high_price = row['high']
        low_price = row['low']
        
        if any(p is None for p in [open_price, close_price, high_price, low_price]):
            continue
        
        if close_price >= open_price:
            color = color_up
            body_bottom = open_price
            body_height = close_price - open_price
        else:
            color = color_down
            body_bottom = close_price
            body_height = open_price - close_price
        
        ax1.add_patch(plt.Rectangle(
            (mdates.date2num(x) - 0.003, body_bottom),
            0.006,
            body_height,
            facecolor=color,
            edgecolor=color,
            linewidth=0.5
        ))
        
        ax1.plot([mdates.date2num(x), mdates.date2num(x)], 
                 [low_price, high_price], 
                 color=color, linewidth=0.5)
    
    ax1.set_ylabel('Цена', fontsize=12)
    ax1.set_title(title, fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_axisbelow(True)
    
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    if show_volume and ax2 is not None:
        colors = []
        for idx in range(len(df)):
            close_val = df.iloc[idx]['close']
            open_val = df.iloc[idx]['open']
            if close_val is not None and open_val is not None:
                colors.append(color_up if close_val >= open_val else color_down)
            else:
                colors.append(color_down)
        
        ax2.bar(df['time'], df['volume'], color=colors, width=0.008, alpha=0.7)
        ax2.set_ylabel('Объем', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.set_axisbelow(True)
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"📁 График сохранен в: {save_path}")
    
    return fig, ax1