#!/usr/bin/env python3
# This isn't pretty, and needs a ton of help.
# There is currently no error checking for probs.
# Will update as I have time.
#
# Changelog
# v.01a Initial Upload
#
# Not responsible for any losses or gains.

import ast
import glob
import os
import operator

os.chdir("/tmp")
total_coins = 0
total_profit = 0
all_sales = []
data = {}

os.chdir("/tmp")
for file in glob.glob("range_buy_*.txt"):
    filename = f'/tmp/{file}'
    f = open(filename, "r")
    temp = f.read()
    data = ast.literal_eval(temp)
    f.close()
    for count, value in enumerate(data):
        bottom_price = round(data[count]['bottom_price'], 8)
        top_price = round(data[count]['top_price'], 6)
        runs = data[count]['completed_runs']
        quantity_buy = data[count]['quantity_buy']
        quantity_sell = data[count]['quantity_sell']
        profit_per_share = round(top_price - bottom_price,6)
        purchase_total_price = bottom_price * quantity_buy
        sell_total_price = top_price * quantity_sell
        coins_collected = (quantity_buy - quantity_sell) * runs
        profits_collected = ((quantity_sell * top_price) - (quantity_buy * bottom_price)) * runs
        if runs > 0:
            price_per_coin = (profits_collected / (quantity_buy - quantity_sell)) / runs
        try:
            percentage_win = '.' + f'{round(((top_price / bottom_price) - 1) * 100, 4)}'.split(".")[1] + '%'
        except:
            percentage_win = '0%'

        if runs > 0:
            total_coins += coins_collected
            total_profit += profits_collected
            all_sales.append([runs, round(data[count]['bottom_price'], 6), round(data[count]['top_price'], 6),
                              coins_collected, profit_per_share, profits_collected,
                              percentage_win, abs(price_per_coin)])

print(f'Total coins collected: {total_coins} at and average of {abs(total_profit / total_coins)}')
print(f'Total profit collected: ${total_profit}')

sorted_list = sorted(all_sales, key=operator.itemgetter(7))
for item in sorted_list:
    print(f"Runs: {item[0]} Bottom: {item[1]:<10} Top: {item[2]:<10} Coins Collected: {item[3]:<5} Profit Per Share: {item[4]:<10} Profits Collected: {round(item[5], 5):<10} Percetage Increase per run: {item[6]}  Price per Coin: {round(item[7], 6)}")

