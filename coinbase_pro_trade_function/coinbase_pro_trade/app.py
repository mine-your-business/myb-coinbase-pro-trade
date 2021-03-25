import os, datetime

from .configuration import Configuration
from coinbase_pro import CoinbaseProApi

def lambda_handler(event, context):
    """Lambda function reacting to EventBridge events

    Parameters
    ----------
    event: dict, required
        Event Bridge Scheduled Events Format

        Event doc: https://docs.aws.amazon.com/eventbridge/latest/userguide/event-types.html#schedule-event-type

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    """

    dry_run = os.environ.get('RUN_MODE') == 'test'
    print(f'Running in {"dry run" if dry_run else "production"} mode')

    config = Configuration()
        
    coinbase_pro_api = CoinbaseProApi(
        api_key=config.coinbase_pro.api_key.key,
        api_secret_key=config.coinbase_pro.api_key.secret,
        api_key_passphrase=config.coinbase_pro.api_key.passphrase
    )

    past_day_stats = coinbase_pro_api.get_24_hr_stats(config.coinbase_pro.trades.product_id)
    past_day_high = float(past_day_stats['high'])
    latest_trade_price = float(past_day_stats['last'])
    print(f'Max latest trade price for {config.coinbase_pro.trades.product_id} was: {latest_trade_price}')
    print(f'24-hour high trade price for {config.coinbase_pro.trades.product_id} was: {past_day_high}')

    range_start = (
        datetime.datetime.today() - 
        datetime.timedelta(days=config.coinbase_pro.trades.day_range_evaluate)
    ).isoformat()
    range_end = datetime.datetime.utcnow().isoformat()

    historic_rates = coinbase_pro_api.get_historic_rates(
        config.coinbase_pro.trades.product_id,
        start=range_start,
        end=range_end,
        # Day granularity
        granularity=86400
    )

    trade_price = None
    if config.coinbase_pro.trades.function == 'average':
        average_high = sum(day[2] for day in historic_rates) / len(historic_rates)
        print(f'Average daily high for the past {config.coinbase_pro.trades.day_range_evaluate} days was: {average_high}')

        if average_high > latest_trade_price:
            # Place the trade at the average price
            print(f'Using average trading price')
            trade_price = average_high
        else:
            # Place the trade at the latest trade price
            print(f'Using latest trading price')
            trade_price = latest_trade_price
    elif config.coinbase_pro.trades.function == 'max':
        max_high = max(day[2] for day in historic_rates)
        print(f'Max daily high for the past {config.coinbase_pro.trades.day_range_evaluate} days was: {max_high}')

        if max_high > latest_trade_price:
            # Place the trade at the max recent price
            print(f'Using max trading price')
            trade_price = max_high
        else:
            # Place the trade at the latest trade price
            print(f'Using latest trading price')
            trade_price = latest_trade_price
    else:
        print(f'Trade evaluation function {config.coinbase_pro.trades.function} not currently supported')

    if trade_price:  
        account = coinbase_pro_api.get_account(config.coinbase_pro.trades.currency)
        if not account['trading_enabled']:
            print(f'{config.coinbase_pro.trades.currency} account does not have trading enabled')
            return

        account_balance = float(account['available'])
        balance_value = account_balance * trade_price
        if balance_value >= config.coinbase_pro.trades.min_value:
            print(
                f"{config.coinbase_pro.trades.currency} account balance {account['balance']} value {balance_value} meets " + 
                f'minimum trade value of {config.coinbase_pro.trades.min_value}'
            )
        else:
            print(
                f"{config.coinbase_pro.trades.currency} account balance {account['balance']} value {balance_value} does " + 
                f'not meet minimum trade value of {config.coinbase_pro.trades.min_value}'
            )
            return

        if dry_run:
            print(
                f'Would have placed a {config.coinbase_pro.trades.type} sell trade of {account_balance} ' + 
                f'{config.coinbase_pro.trades.currency} at a price of {trade_price} for a total value of {balance_value}'
            )
        else:
            print(
                f'Placing a {config.coinbase_pro.trades.type} sell trade of {account_balance} ' + 
                f'{config.coinbase_pro.trades.currency} at a price of {trade_price} for a total value of {balance_value}'
            )
            if config.coinbase_pro.trades.type == 'limit':
                coinbase_pro_api.place_limit_order(
                    config.coinbase_pro.trades.product_id,
                    'sell',
                    trade_price,
                    account_balance,
                    cancel_after=config.coinbase_pro.trades.cancel_after
                )
    
    # We got here successfully!
    return True
