from src.enums.instrument_types import InstrumentType

def get_figi_by_ticker(client, ticker: str, instrument_type: InstrumentType) -> str | None:
    response = client.instruments.find_instrument(
        query=ticker,
        instrument_kind=instrument_type,
        api_trade_available_flag=True
    )

    if response.instruments:
        return response.instruments[0].figi
    return None
