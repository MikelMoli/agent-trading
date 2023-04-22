
import os

CREDENTIALS = {
    # Las credenciales de Alpaca son para paper trading y ya

    "ALPACA": {
        "API_KEY": "CKV22W69USWRL60AX8S3",
        "SECRET_KEY": "CUVJbr2pcf0FqydF8NhqEYwDpwhhHWTbhpJy3tJo"
    }
}

#  FOREX
SOURCES = {
    "FOREX": "https://www.histdata.com/download-free-forex-historical-data/?/metatrader/1-minute-bar-quotes/{}"
}

VALID_CURRENCY_PAIRS = ["EURUSD",
                        "EURCHF",
                        "EURGBP",
                        "EURJPY",
                        "EURAUD",
                        "USDCAD",
                        "USDCHF",
                        "USDJPY",
                        "USDMXN",
                        "GBPCHF",
                        "GBPJPY",
                        "GBPUSD",
                        "AUDJPY",
                        "AUDUSD",
                        "CHFJPY",
                        "NZDJPY",
                        "NZDUSD",
                        "XAUUSD",
                        "EURCAD",
                        "AUDCAD",
                        "CADJPY",
                        "EURNZD",
                        "GRXEUR",
                        "NZDCAD",
                        "SGDJPY",
                        "USDHKD",
                        "USDNOK",
                        "USDTRY",
                        "XAUAUD",
                        "AUDCHF",
                        "AUXAUD",
                        "EURHUF",
                        "EURPLN",
                        "FRXEUR",
                        "HKXHKD",
                        "NZDCHF",
                        "SPXUSD",
                        "USDHUF",
                        "USDPLN",
                        "USDZAR",
                        "XAUCHF",
                        "ZARJPY",
                        "BCOUSD",
                        "ETXEUR",
                        "CADCHF",
                        "EURDKK",
                        "EURNOK",
                        "EURTRY",
                        "GBPCAD",
                        "NSXUSD",
                        "UKXGBP",
                        "USDDKK",
                        "USDSGD",
                        "XAGUSD",
                        "XAUGBP",
                        "EURCZK",
                        "EURSEK",
                        "GBPAUD",
                        "GBPNZD",
                        "JPXJPY",
                        "UDXUSD",
                        "USDCZK",
                        "USDSEK",
                        "WTIUSD",
                        "XAUEUR",
                        "AUDNZD"
]

YEARS_TO_EXTRACT = 5

# PATHS

BASE_PATH = os.getcwd()
DATA_FOLDER_PATH = f'{BASE_PATH}/data'
