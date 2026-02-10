from enum import Enum

class InstrumentType(Enum):
    UNSPECIFIED = 0
    BOND = 1
    SHARE = 2
    CURRENCY = 3
    ETF = 4
    FUTURES = 5
    SP = 6
    OPTION = 7
    CLEARING_CERTIFICATE = 8
    INDEX = 9
    COMMODITY = 10