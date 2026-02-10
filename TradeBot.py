import os

from t_tech.invest import Client
from t_tech.invest.constants import INVEST_GRPC_API_SANDBOX

from src.enums.instrument_types import InstrumentType
from src.instruments.figi import get_figi_by_ticker
from src.instruments.balance import get_balance, add_money_sandbox

TOKEN = os.getenv("TINKOFF_TOKEN")
ACCOUNT_ID = os.getenv("TINKOFF_ACCOUNT")

with Client(TOKEN, target=INVEST_GRPC_API_SANDBOX) as client:
    print(client.users.get_accounts())
    print(get_balance(client, ACCOUNT_ID))
    print(add_money_sandbox(client, ACCOUNT_ID, 10000))
    print(get_balance(client, ACCOUNT_ID))
    figi = get_figi_by_ticker(client, "WUSH", InstrumentType.SHARE)
    print("FIGI:", figi)