#!/usr/bin/env python
# This isn't pretty, and needs a ton of help.
# There is currently no error checking for probs.
# Will update as I have time.
#
# Changelog
# v.01a Initial Upload
#
# Not responsible for any losses or gains.

import argparse
import datetime
import math
import pyotp
import robin_stocks.robinhood as r
import sys
import time
from argparse import RawTextHelpFormatter
from decimal import *

counter = 0

def get_cli_args():
    parser = argparse.ArgumentParser(
        description="RobinHood Stop Loss Tool.",
        epilog=f'Example: \n\n'
               './rh_trailing_stop_loss.py -u "username" -p "password" -c ETC -v .01 -m 50 -l .50 -q .01 -t 60',
        formatter_class=RawTextHelpFormatter
    )

    parser.add_argument(
        '-u', '--username', type=str, help='Username', default=None,
    )

    parser.add_argument(
        '-p', '--password', type=str, help='Password', default=None,
    )

    parser.add_argument(
        '-q', '--quantity', nargs='?', help='Quantity can be number or ALL.  ALL will be gathered from Robinhood.',
        default=None,
    )

    parser.add_argument(
        '-c', '--coin', type=str, help='Coin Ticker', default=None,
    )

    parser.add_argument(
        '-m', '--minimum_price', type=float, help='Minimum Price - Do not place order if price is lower than this',
        default=None,
    )

    parser.add_argument(
        '-v', '--trailing_value', type=float, help='Trailing Value - How much to trail', default=None,
    )

    parser.add_argument(
        '-l', '--limit_value', type=float, help='Limit Value - Amount below trailing stop price to set limit order',
        default=None,
    )

    parser.add_argument(
        '-t', '--timeout', type=int, help='Timeout between checks in seconds.  Defaults to 10 seconds.', default=10,
    )

    return parser.parse_args()


def login_to_robinhood(username, password):
    try:
        r.login(username, password)
        return r
    except:
        raise


def sell(r, quan, price, coin, crypto_min_order_price_increment):
    global counter
    if counter < 4:
        print('Counter is less that 4.  Adding 1 to counter.')
        counter += 1
        return False
    print(f'Trying to place a sell limit order for {quan} shares with a limit price of {price}')
    try:
        round_by = len(str(crypto_min_order_price_increment).split('.')[1])
        result = r.orders.order_sell_crypto_limit(coin, quan, round(price, round_by), timeInForce='gtc')
    except:
        result = r.orders.order_sell_crypto_limit(coin, quan, price, timeInForce='gtc')
    try:
        id = result['id']
        print('Order placed')
        print(f'Order ID: {id}')
        print(f'Order created at: {result["created_at"]}')
        return True
    except:
        print('Failed to place order.  Will retry.')
        print(f'Error {result}')
        return False


def run_me(r, highest_seen, lowest_seen, coin, quantity, trailing_value, minimum_price, limit_value,
           crypto_min_order_price_increment, times_above_stop_limit, times_below_stop_limit,
           initial_start_time):
    print('========================================================================================================')
    print(f'Coin: {coin}')
    print(f'Quantity to sell: {quantity}')
    print(f'Minimum price before sale: {minimum_price}')
    print(f'Trailing value: {trailing_value}')
    print(f'Price below stop price to set limit order below: {limit_value}')
    print(f'Time running: {datetime.datetime.now() - initial_start_time}')
    try:
        quote = r.crypto.get_crypto_quote(coin)
        mark_price = float(quote['mark_price'])
    except Exception as ex:
        print('Crash while gathering crypto quote')
        return False

    if lowest_seen == 0:
        lowest_seen = mark_price

    if mark_price > highest_seen:
        print('''    __  ______________  ____________     __  ______________  __
   / / / /  _/ ____/ / / / ____/ __ \   / / / /  _/ ____/ / / /
  / /_/ // // / __/ /_/ / __/ / /_/ /  / /_/ // // / __/ /_/ / 
 / __  // // /_/ / __  / /___/ _, _/  / __  // // /_/ / __  /  
/_/ /_/___/\____/_/ /_/_____/_/ |_|  /_/ /_/___/\____/_/ /_/
''')
        print(f'Found new highest price: {mark_price}')
        print(f'Raising stop price: {abs(round(highest_seen - mark_price, 6))}')

        highest_seen = mark_price

    if mark_price < lowest_seen:
        lowest_seen = mark_price

    stop_price = highest_seen - trailing_value

    print(f'Market Price: {mark_price} Highest Price Seen: {highest_seen} Lowest Price Seen: {lowest_seen}')
    print(f'Stop Price: {stop_price}')
    print(f'Distance between Stop Price and Current Price: {mark_price - stop_price}')
    try:
        print(f'Percentage of time above stop limit: {round((times_above_stop_limit / (times_above_stop_limit + times_below_stop_limit) * 100), 2)}')
    except:
        pass
    print(f'Limit Price if sell order placed: {stop_price - limit_value}')

    if mark_price < stop_price:
        times_below_stop_limit += 1
        if stop_price - limit_value > minimum_price:
            result = sell(r, quantity, stop_price - limit_value, coin, crypto_min_order_price_increment)
            if result:
                exit()
        else:
            print(f'Price not above minimum price of {minimum_price}.  Cannot create sell order.')
    else:
        times_above_stop_limit += 1
    print('========================================================================================================')

    return highest_seen, lowest_seen, times_above_stop_limit, times_below_stop_limit


def main():
    cli_args = get_cli_args()
    try:
        username = cli_args.username
        password = cli_args.password
        quantity = cli_args.quantity
        coin = cli_args.coin.upper()
        trailing_value = cli_args.trailing_value
        minimum_price = cli_args.minimum_price
        limit_value = cli_args.limit_value
        timeout = cli_args.timeout
    except:
        raise
        print('Missing command line argument or bad argument.  Exiting.')
        exit()

    if username is None or \
            password is None or \
            quantity is None or \
            coin is None or \
            trailing_value is None or \
            minimum_price is None or \
            limit_value is None:
        print('Missing command line argument.  Exiting.')
        exit()
    print('========================================================================================================')
    print('\nWelcome to the RobinHood trailing stop limit tool\n')
    print('========================================================================================================')
    print('Attempting to log into RobinHood')
    r = login_to_robinhood(username, password)
    print('Logged into RobinHood')

    try:
        current_cypto_info = r.crypto.get_crypto_info(coin)
        crypto_name = current_cypto_info['asset_currency']['name']
        crypto_max_order_size = float(current_cypto_info['max_order_size'])
        crypto_min_order_price_increment = float(current_cypto_info['min_order_price_increment'])
        crypto_min_order_quantity_increment = float(current_cypto_info['min_order_quantity_increment'])
        crypo_min_order_size = float(current_cypto_info['min_order_size'])
    except:
        print(f'Failed to gather info about {coin}.  Exiting.')

    # PRE CHECKS
    positions = r.crypto.get_crypto_positions()
    rh_quantity = float(0)
    for item in positions:
        if item['currency']['code'] == coin:
            rh_quantity = float(item['quantity'])

    if quantity.upper() == 'ALL':
        quantity = rh_quantity
    else:
        quantity = float(quantity)

    if quantity > rh_quantity:
        print('Quantity specified is greater that quantity owned.  Exiting.')
        exit()

    if quantity > crypto_max_order_size:
        print('Quantity is too large.  Exiting.')
        exit()

    if quantity < crypo_min_order_size:
        print('Quantity is too small.  Exiting.')
        exit()

    if not (quantity / crypto_min_order_quantity_increment).is_integer():
        print('Quantity is not divisible by crypto_min_order_quantity_increment.  Exiting.')
        exit()

    quote = r.crypto.get_crypto_quote(coin)
    mark_price = float(quote['mark_price'])
    highest_seen = mark_price
    lowest_seen = mark_price

    print('========================================================================================================')
    print(f'username: {username}')
    print(f'Timeout: {timeout}')
    print(f'coin: {coin}')
    print(f'RobinHood Quantity: {rh_quantity}')
    print(f'Current Price on Robinhood: {mark_price}')
    print(f'Quantity to Sell: {quantity}')
    print(f'Minimum Price to Sell: {minimum_price}')
    print(f'trailing_value: {trailing_value}')
    print(f'limit_value: {limit_value}')
    print(f'crypto_name: {crypto_name}')
    print(f'crypto_max_order_size: {crypto_max_order_size}')
    print(f'crypo_min_order_size: {crypo_min_order_size}')
    print(f'crypto_min_order_price_increment: {crypto_min_order_price_increment}')
    print(f'crypto_min_order_quantity_increment: {crypto_min_order_quantity_increment}')

    times_above_stop_limit = 0
    times_below_stop_limit = 0
    initial_start_time = datetime.datetime.now()
    # Start the Loop
    while True:
        highest_seen, lowest_seen, times_above_stop_limit, times_below_stop_limit = run_me(r, highest_seen, lowest_seen,
                                                                                           coin, quantity,
                                                                                           trailing_value,
                                                                                           minimum_price,
                                                                                           limit_value,
                                                                                           crypto_min_order_price_increment,
                                                                                           times_above_stop_limit,
                                                                                           times_below_stop_limit,
                                                                                           initial_start_time)
        time.sleep(timeout)


if __name__ == "__main__":
    main()
