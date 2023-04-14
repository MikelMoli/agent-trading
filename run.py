import alpaca_trade_api as api
import config


def tiro_alpaca():
    alpaca = api.REST(config.CREDENTIALS['ALPACA']['API_KEY'], config.CREDENTIALS['ALPACA']['SECRET_KEY'])

