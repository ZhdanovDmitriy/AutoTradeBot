from decimal import Decimal
from t_tech.invest import MoneyValue
from t_tech.invest.utils import decimal_to_quotation, quotation_to_decimal

def get_balance(client, account_id) -> str | None:
    balance = float(quotation_to_decimal(
                    client.operations.get_positions(account_id=account_id).money[0]
                )
            )
    if balance:
        return balance
    return None


def add_money_sandbox(client, account_id, money, currency="rub"):
    money = decimal_to_quotation(Decimal(money))
    return client.sandbox.sandbox_pay_in(
        account_id=account_id,
        amount=MoneyValue(units=money.units, nano=money.nano, currency=currency),
    )