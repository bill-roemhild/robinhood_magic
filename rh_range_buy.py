#!/usr/bin/env python
# This isn't pretty, and needs a ton of help.
# There is currently no error checking for folder existence and other probs.
# Will update as I have time.
#
# Changelog
# v.01a Initial Upload
#
# Not responsible for any losses or gains.

import argparse
import ast
import os
import random
import pyotp
import robin_stocks.robinhood as r
import time
from argparse import RawTextHelpFormatter


def clear():
    _ = os.system('clear')


def get_cli_args():
    parser = argparse.ArgumentParser(
        description="RobinHood Up and Down Tool",
        epilog=f'Example: \n\n'
               './rh_range_buy.py -u "username" -q 100 -c ETC -b 1.50 -t 2.25 -w 30 -n 10 -s 10',
        formatter_class=RawTextHelpFormatter
    )

    parser.add_argument(
        '-u', '--username', type=str, help='Username', default=None,
    )

    parser.add_argument(
        '-p', '--password', type=str, help='Password', default=None,
    )

    parser.add_argument(
        '-q', '--quantity', type=float, help='Quantity', default=None,
    )

    parser.add_argument(
        '-c', '--coin', type=str, help='Coin Ticker', default=None,
    )

    parser.add_argument(
        '-t', '--top_price', type=float, help='Price to sell at', default=None,
    )

    parser.add_argument(
        '-b', '--bottom_price', type=float, help='Price to buy at', default=None,
    )

    parser.add_argument(
        '-w', '--timeout', type=int, help='Timeout between checks in seconds.  Defaults to 10 seconds.', default=10,
    )

    parser.add_argument(
        '-n', '--number_of_splits', type=int, help='number_of_splits - default 10', default=10,
    )

    parser.add_argument(
        '-s', '--number_of_shares_to_keep', type=int, help='number_of_shares_to_keep - default 0', default=0,
    )

    return parser.parse_args()


def login_to_robinhood(username, password):
    try:
        r.login(username, password)
        return r
    except:
        raise


def buy(r, quan, price, coin, crypto_min_order_price_increment):
    print(f'Trying to place a buy limit order with a limit price of {price}')
    try:
        round_by = len(str(crypto_min_order_price_increment).split('.')[1])
        result = r.orders.order_buy_crypto_limit(coin, quan, round(price, round_by), timeInForce='gtc')
    except:
        result = r.orders.order_buy_crypto_limit(coin, quan, round(price, 6), timeInForce='gtc')

    try:
        id = result['id']
        print('Order placed')
        return True, id
    except:
        print('Failed to place order.  Will retry.')
        print(f'Error {result}')
        time.sleep(5)
        return False, False


def sell(r, quan, price, coin, crypto_min_order_price_increment):
    print(f'Trying to place a sell limit order with a limit price of {price}')
    try:
        round_by = len(str(crypto_min_order_price_increment).split('.')[1])
        result = r.orders.order_sell_crypto_limit(coin, quan, round(price, round_by), timeInForce='gtc')
    except:
        result = r.orders.order_sell_crypto_limit(coin, quan, round(price, 6), timeInForce='gtc')

    try:
        id = result['id']
        print('Order placed')
        return True, id
    except:
        print('Failed to place order.  Will retry.')
        print(f'Error {result}')
        time.sleep(5)
        return False, False


def main():
    slowly_end = False
    cli_args = get_cli_args()
    try:
        username = cli_args.username
        password = cli_args.password
        quantity = cli_args.quantity
        coin = cli_args.coin
        top_price = cli_args.top_price
        bottom_price = cli_args.bottom_price
        timeout = cli_args.timeout
        number_of_splits = cli_args.number_of_splits
        number_of_shares_to_keep = cli_args.number_of_shares_to_keep
    except:
        print('Missing command line argument or bad argument.  Exiting.')
        exit()

    if username is None:
        username = getpass.getpass(prompt='Username? ')

    if password is None:
        password = getpass.getpass(prompt='Password? ')


    if coin is None:
        coin = input('Coin? ')

    try:
        coin = coin.upper()
    except:
        print('Unable to convert coin to upper case.  Exiting.')
        exit()

    if top_price is None:
        top_price = input('Top Price? ')

    try:
        top_price = float(top_price)
    except:
        print('Unable to convert top_price to float.  Exiting.')
        exit()

    if bottom_price is None:
        bottom_price = input('Bottom Price? ')

    try:
        bottom_price = float(bottom_price)
    except:
        print('Unable to convert bottom_price to float.  Exiting.')
        exit()

    if top_price <= bottom_price:
        print('top_price higher or equal to lower_price.  Exiting.')
        exit()

    print(f'coin: {coin}')
    print(f'top_price: {top_price}')
    print(f'bottom_price: {bottom_price}')
    print(f'timeout: {timeout}')
    print(f'number_of_splits: {number_of_splits}')

    print('========================================================================================================')
    print('\nWelcome to the RobinHood Distance Script\n')
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
        exit()

    # PRE CHECKS
    if quantity > crypto_max_order_size:
        print('Quantity is too large.  Exiting.')
        exit()

    if quantity < crypo_min_order_size:
        print('Quantity is too small.  Exiting.')
        exit()

    filename = f'/tmp/range_buy_{coin}_{top_price}_{bottom_price}_{number_of_splits}.txt'

    try:
        f = open(filename, "r")
        temp = f.read()
        data = ast.literal_eval(temp)
        f.close()
        for count, value in enumerate(data):
            data[count]['quantity_buy'] = quantity
            data[count]['quantity_sell'] = quantity - number_of_shares_to_keep
    except:
        data = {}
        counter = 0
        range_of_split = (top_price - bottom_price) / number_of_splits
        top_price = bottom_price + range_of_split
        while counter < number_of_splits:
            bottom_of_range = bottom_price
            top_of_range = bottom_price + range_of_split
            print(f'bottom: {bottom_of_range}')
            print(f'top: {top_of_range}')
            print('------------------')
            bottom_price += range_of_split
            top_price += range_of_split
            data[counter] = {'bottom_price': bottom_price,
                             'top_price': top_price,
                             'status': 'new',
                             'order_id': 'N/A',
                             'completed_runs': 0,
                             'quantity_buy': quantity,
                             'quantity_sell': quantity - number_of_shares_to_keep,
                             'order_state': ''}
            counter += 1

    test_me = input('Continue? ')
    if test_me.upper() != 'Y':
        exit()

    quote = r.crypto.get_crypto_quote(coin)
    mark_price = float(quote['mark_price'])

    print('========================================================================================================')
    print(f'coin: {coin}')
    print(f'crypto_name: {crypto_name}')
    print(f'Quantity to Buy/Sell: {quantity}')
    print(f'Price to Buy: {bottom_price}')
    print(f'Price to Sell: {top_price}')
    print(f'Timeout: {timeout}')
    print(f'Current Price on Robinhood: {mark_price}')
    print(f'crypto_max_order_size: {crypto_max_order_size}')
    print(f'crypo_min_order_size: {crypo_min_order_size}')
    print(f'crypto_min_order_price_increment: {crypto_min_order_price_increment}')
    print(f'crypto_min_order_quantity_increment: {crypto_min_order_quantity_increment}')

    # Start the Loop
    while True:
        quote = r.crypto.get_crypto_quote(coin)
        mark_price = float(quote['mark_price'])
        for count, value in enumerate(data):
            if data[count]['status'] == 'new':
                if data[count]['top_price'] < mark_price:
                    data[count]['status'] = 'buy'
                else:
                    data[count]['status'] = 'sell'

            if data[count]['status'] == 'buy':
                result, data[count]['order_id'] = buy(r, data[count]['quantity_buy'], data[count]['bottom_price'], coin, crypto_min_order_price_increment)
                if result:
                    data[count]['status'] = 'check_for_buy'
            elif data[count]['status'] == 'check_for_buy':
                try:
                    data[count]['order_state'] = r.get_crypto_order_info(data[count]['order_id'])['state']
                    if slowly_end:
                        if data[count]['order_state'] != 'canceled':
                            print(f'Trying to cancel {data[count]["order_id"]}')
                            r.cancel_crypto_order(data[count]["order_id"])
                    else:
                        if data[count]['order_state'] == 'filled':
                            data[count]['status'] = 'sell'
                            data[count]['order_state'] = ''
                except:
                    print('Failed request to get info from RobinHood.  Will retry.')
                    time.sleep(5)
            elif data[count]['status'] == 'sell':
                result, data[count]['order_id'] = sell(r, data[count]['quantity_sell'], data[count]['top_price'], coin, crypto_min_order_price_increment)
                if result:
                    data[count]['status'] = 'check_for_sell'
            elif data[count]['status'] == 'check_for_sell':
                try:
                    data[count]['order_state'] = r.orders.get_crypto_order_info(data[count]['order_id'])['state']
                    if data[count]['order_state'] == 'filled':
                        data[count]['completed_runs'] += 1
                        if slowly_end:
                            data[count]['status'] = 'exit'
                        else:
                            data[count]['status'] = 'buy'
                        data[count]['order_state'] = ''
                except:
                    print('Failed request to get info from RobinHood.  Will retry.')
                    time.sleep(5)
        clear()
        print(f'Coin: {coin} - Shares to Keep: {number_of_shares_to_keep} Data File: {filename} \n')

        if mark_price <= data[0]['bottom_price']:
            print(f'-----------  MARK PRICE: {mark_price} ------------')

        for count, value in enumerate(data):
            if data[count]['bottom_price'] < mark_price < data[count]['top_price']:
                print(f'-----------  MARK PRICE: {mark_price} ------------')
            if data[count]['completed_runs'] > 0:
                profits_collected = (data[count]['quantity_sell'] * data[count]['top_price']) - (data[count]['quantity_buy'] * data[count]['bottom_price'])
                price_per_coin = round(abs(profits_collected / (data[count]['quantity_buy'] - data[count]['quantity_sell'])), 6)
                print(
                    f"Bottom: {round(data[count]['bottom_price'], 6):<8}({quantity}) Top: {round(data[count]['top_price'], 6):<8}({quantity - number_of_shares_to_keep}) Status: {data[count]['status']:<14} State: {data[count]['order_state']} Runs: {data[count]['completed_runs']} Coins Collected: {number_of_shares_to_keep * data[count]['completed_runs']} at {price_per_coin}")
            else:
                print(
                    f"Bottom: {round(data[count]['bottom_price'], 6):<8}({quantity}) Top: {round(data[count]['top_price'], 6):<8}({quantity - number_of_shares_to_keep}) Status: {data[count]['status']:<14} State: {data[count]['order_state']} Runs: {data[count]['completed_runs']}")

        if mark_price >= data[len(data) - 1]['top_price']:
            print(f'-----------  MARK PRICE: {mark_price} ------------')

        f = open(filename, "w")
        f.write(str(data))
        f.close()

        number_still_running = 0
        for count, value in enumerate(data):
            if data[count]['order_state'] != 'canceled':
                number_still_running += 1
        if number_still_running == 0:
            os.rename(filename, '/opt/old_logs/' + filename.split('/')[2].replace('.txt', '') + '__' + str(random.randint(0, 1000)) + '.txt')
            exit()
        try:
            time.sleep(timeout)
        except:
            slowly_end = input('Do you want to slowly exit? (y/n)')
            if slowly_end.upper() == 'Y':
                slowly_end = True
            else:
                delete_existing = input('Do you want to delete existing orders? (y/n)')
                if delete_existing.upper() == 'Y':
                    delete_buy = input('Do you want to delete existing buy orders? (y/n)')
                    delete_sell = input('Do you want to delete existing sell orders? (y/n)')

                    for count, value in enumerate(data):
                        counter = 0
                        exit_loop = False
                        try:
                            state_result = r.get_crypto_order_info(data[count]['order_id'])['state']
                        except:
                            print(f'===========> Failed to gather state for order: {data[count]["order_id"]}')
                            continue
                        if (data[count]['status'] == 'check_for_sell' and delete_sell.upper() == 'Y') or (data[count]['status'] == 'check_for_buy' and delete_buy.upper() == 'Y'):
                            while state_result != 'canceled' and not exit_loop:
                                print(f'Cancelling {data[count]["order_id"]}')
                                print(f'State {state_result}')
                                r.cancel_crypto_order(data[count]["order_id"])
                                state_result = r.get_crypto_order_info(data[count]['order_id'])['state']
                                counter += 1
                                if counter > 20:
                                    print(f'===========> Failed to cancel order: {data[count]["order_id"]}')
                                    exit_loop = True
                                time.sleep(5)

                    os.rename(filename, '/opt/old_logs/' + filename.split('/')[2].replace('.txt', '') + '__' + str(random.randint(0, 1000)) + '.txt')
                exit()


if __name__ == "__main__":
    main()
