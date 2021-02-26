import os

class Configuration:

    def __init__(self):
        self.coinbase_pro = CoinbasePro()

class CoinbaseProApiKey:

    def __init__(self):
        self.key = os.environ.get('CBP_API_KEY')
        self.passphrase = os.environ.get('CBP_API_KEY_PASSPHRASE')
        self.secret = os.environ.get('CBP_API_KEY_SECRET')

class CoinbaseProTrades:

    def __init__(self):
        self.currency = os.environ.get('TRADES_CURRENCY')
        self.product_id = os.environ.get('TRADES_PRODUCT_ID')
        self.day_range_evaluate = int(os.environ.get('TRADES_DAY_RANGE_EVAL'))
        self.function = os.environ.get('TRADES_FUNCTION')
        self.type = os.environ.get('TRADES_TYPE')
        self.min_value = float(os.environ.get('TRADES_MIN_AMOUNT'))
        self.cancel_after = os.environ.get('TRADES_CANCEL_AFTER')

class CoinbasePro:

    def __init__(self):
        self.trades = CoinbaseProTrades()
        self.api_key = CoinbaseProApiKey()
