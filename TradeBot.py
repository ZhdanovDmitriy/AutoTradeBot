# TradeBot.py
import os
import matplotlib.pyplot as plt
from pathlib import Path
import shutil

from t_tech.invest import Client
from t_tech.invest.constants import INVEST_GRPC_API_SANDBOX

from src.enums.instrument_types import InstrumentType
from src.instruments.figi import get_figi_by_ticker
from src.instruments.balance import get_balance, add_money_sandbox
from src.instruments.candles import download_candles, draw_candles
from t_tech.invest import CandleInterval

TOKEN = os.getenv("TINKOFF_TOKEN")
ACCOUNT_ID = os.getenv("TINKOFF_ACCOUNT")

DATA_PATH = R"C:\Users\dzhda\OneDrive\Рабочий стол\автотрейдинг\TradeBot\src\data\test_candles_WUSH"

if os.path.exists(DATA_PATH):
    print(f"Очищаем старый кэш: {DATA_PATH}")
    shutil.rmtree(DATA_PATH)

Path(DATA_PATH).mkdir(parents=True, exist_ok=True)

with Client(TOKEN, target=INVEST_GRPC_API_SANDBOX) as client:
    print(client.users.get_accounts())
    print(get_balance(client, ACCOUNT_ID))
    
    figi = get_figi_by_ticker(client, "WUSH", InstrumentType.SHARE)
    print("FIGI:", figi)
    
    #print(add_money_sandbox(client, ACCOUNT_ID, 10000))

    csv_filepath = download_candles(
        client, 
        figi, 
        days=30, 
        candle_interval_type=CandleInterval.CANDLE_INTERVAL_HOUR, 
        path=DATA_PATH
    )
    
    if csv_filepath:
        draw_candles(
            csv_filepath,
            title=f"WUSH ({figi})",
            show_volume=False
        )
        plt.show()
    else:
        print("Не удалось создать график - нет данных")
