#!/usr/bin/env python3
# This isn't pretty, and needs a ton of help.
# There is currently no error checking for probs.
# Will update as I have time.
#
# Changelog
# v.01a Initial Upload
#
# Not responsible for any losses or gains.


import robin_stocks.robinhood as r
import time
import argparse
from argparse import RawTextHelpFormatter


def get_cli_args():
    parser = argparse.ArgumentParser(
        description="RobinHood Stop Loss Tool.",
        epilog=f'Example: \n\n'
               './rh_stop_loss.py -u user@gmail.com -p "my_password" -q 1 -t DOGE -s 10 -l .01',
        formatter_class=RawTextHelpFormatter
    )

    parser.add_argument(
        '-u', '--username', nargs='?', help='Username', default = None,
    )

    parser.add_argument(
        '-p', '--password', nargs='?', help='Password', default = None,
    )

    parser.add_argument(
        '-q', '--quantity', nargs='?', help='Quantity', default = None,
    )

    parser.add_argument(
        '-t', '--ticker', nargs='?', help='Ticker', default = None,
    )

    parser.add_argument(
        '-s', '--stop_price', nargs='?', help='Stop Price - When stock mark price hits this value an order will be placed to sell', default = None,
    )

    parser.add_argument(
        '-l', '--limit_price', nargs='?', help='Limit Price - Limit price when an order to sell is placed', default = None,
    )

    return parser.parse_args()


def login_to_robinhood(username, password):
    try:
        r.login(username, password)
        return r
    except Exception as ex:
        print(f'Failed to login to Robinhood: {ex}')
        exit()


def sell(r, quan, limit_price, ticker):
    print(f'Trying to enter a limit order for {str(quan)} shares at {str(limit_price)}')
    try:
        result = r.orders.order_sell_crypto_limit(ticker, quan, limit_price, timeInForce='gtc')
        if 'id' in result.keys():
            print(f'Successfully entered order.  Exiting.')
            return True
        else:
            print(f'Failed to place order error: {result}')
            return False
    except:
        print(f'Failed to enter limit order.')
        return False


def let_the_magic_run(r, quan, ticker, stop_price, limit_price):
    try:
        quote = r.crypto.get_crypto_quote(ticker)
        mark_price = float(quote['mark_price'])
    except:
        print('Failed to gather quote from Robinhood.  Will retry.')

    if mark_price < stop_price:
        print(f'Current mark price: {str(mark_price)} is lower than stop price.  Placing sell order.')
        result = sell(r, quan, limit_price, ticker)
        if result:
            exit()
    else:
        print(f'Current mark price: {str(mark_price)} is higher than stop price: {str(stop_price)}')


def main():
    try:
        cli_args = get_cli_args()
        username = cli_args.username
        password = cli_args.password
        quantity = cli_args.quantity
        ticker = cli_args.ticker
        stop_price = float(cli_args.stop_price)
        limit_price = float(cli_args.limit_price)

    except:
        print('Missing command line argument or bad argument.  Exiting.')
        exit()

    if username is None or password is None or quantity is None or ticker is None:
        print('Missing command line argument.  Exiting.')
        exit()

    r = login_to_robinhood(username, password)

    print('Logged into Robinhood')

    while True:
        let_the_magic_run(r, quantity, ticker, stop_price, limit_price)
        time.sleep(15)


if __name__ == "__main__":
    main()

