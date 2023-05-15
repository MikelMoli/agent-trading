
import os
from datetime import datetime

CREDENTIALS = {
    # Las credenciales de Alpaca son para paper trading y ya

    "ALPACA": {
        "API_KEY": "CKV22W69USWRL60AX8S3",
        "SECRET_KEY": "CUVJbr2pcf0FqydF8NhqEYwDpwhhHWTbhpJy3tJo"
    }
}

#  FOREX
SOURCES = {
    "forex": "https://www.axiory.com/jp/assets/download/historical/mt4_standard/{}/{}.zip"
}

VALID_ASSETS = {
    "forex": ["EURUSD", "EURCHF", "EURGBP", "EURJPY", "EURAUD", "USDCAD", "USDCHF", "USDJPY", "USDMXN", "GBPCHF", "GBPJPY",
              "GBPUSD", "AUDJPY", "AUDUSD", "CHFJPY", "NZDJPY", "NZDUSD", "XAUUSD", "EURCAD", "AUDCAD", "CADJPY", "EURNZD",
              "GRXEUR", "NZDCAD", "SGDJPY", "USDHKD", "USDNOK", "USDTRY", "XAUAUD", "AUDCHF", "AUXAUD", "EURHUF", "EURPLN",
              "FRXEUR", "HKXHKD", "NZDCHF", "SPXUSD", "USDHUF", "USDPLN", "USDZAR", "XAUCHF", "ZARJPY", "BCOUSD", "ETXEUR",
              "CADCHF", "EURDKK", "EURNOK", "EURTRY", "GBPCAD", "NSXUSD", "UKXGBP", "USDDKK", "USDSGD", "XAGUSD", "XAUGBP",
              "EURCZK", "EURSEK", "GBPAUD", "GBPNZD", "JPXJPY", "UDXUSD", "USDCZK", "USDSEK", "WTIUSD", "XAUEUR", "AUDNZD"],
    "crypto": [],
    "commodity": []
}

# PATHS

BASE_PATH = os.getcwd()
DATA_FOLDER_PATH = f'{BASE_PATH}/data'

CONECTION_TIMEOUT = 10


EXTRACTION_DEFAULT_END_YEAR = datetime.now().year - 5

VALID_FILE_OUTPUT_FORMATS = ['csv', 'parquet']
