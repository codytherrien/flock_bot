from calendar import c
import sys
import time
import datetime
from street_cred import *
from Account import Account
import alpaca_trade_api as tradeapi
from websocket import create_connection
import ast
from helpers import *
import yfinance as yf

NUM_STOCKS = 50
PERIOD = 5
STOCKS_HELD = 5
THRESHOLD = 0

def sleeping_stage(api):
        market_close_flag = True
        while datetime.datetime.now().hour < 4:
            time.sleep(7200) # Sleeps for 2 hours
        while datetime.datetime.now().hour < 13: # set to 5 for local machine 13 for cloud
            time.sleep(1200) # sleeps for 20 minutes
        while market_close_flag:
            time.sleep(60)
            try:
                clock = api.get_clock()
                if clock.is_open:
                    market_close_flag = False
            except:
                api = tradeapi.REST(keys, keys_to_the_vip, paper_products)

def get_hold_stocks(high_volume_stocks):
    for s1 in high_volume_stocks.keys():
        bars1 = high_volume_stocks[s1].day_bars
        prices1 = [x['c'] for x in bars1]
        ave_price1 = sum(prices1) / len(prices1)
        norm_price1 = [x / ave_price1 for x in prices1]
        sum_ratios = 0
            
        for s2 in high_volume_stocks.keys():
            if s1 != s2:
                bars2 = high_volume_stocks[s2].day_bars
                prices2 = [x['c'] for x in bars2]
                ave_price2 = sum(prices2) / len(prices2)
                norm_price2 = [x/ave_price2 for x in prices2]
                diffs = [x-y for x, y in zip(norm_price1, norm_price2)]
                diff_range = max(diffs) - min(diffs)
                curr_diff = norm_price1[-1] - norm_price2[-1]
                if diff_range != 0:
                    sum_ratios += (curr_diff / diff_range)
                        
        high_volume_stocks[s1].ave_ratio = sum_ratios / (len(high_volume_stocks) - 1)
            
    return sorted(high_volume_stocks.values(), key=lambda x: abs(x.ave_ratio), reverse=True)[:5]

def submit_trade(trade_account, stock, kept_positions):
    trade_account.reconnect()
    qty = 0

    if stock.symbol not in kept_positions.keys():
        if stock.ave_ratio < -THRESHOLD:
            side = 'buy'
        else:
            side = 'sell'
        qty = float(trade_account.account.equity) // (STOCKS_HELD*stock.min_bars[-1]['c'])
    elif stock.ave_ratio < -THRESHOLD and kept_positions[stock.symbol] <= 0:
        side = 'buy'
        qty = float(trade_account.account.equity) // (STOCKS_HELD*stock.min_bars[-1]['c']) + abs(kept_positions[stock])
    elif stock.ave_ratio > THRESHOLD and kept_positions[stock.symbol] >= 0:
        side = 'sell'
        qty = float(trade_account.account.equity) // (STOCKS_HELD*stock.min_bars[-1]['c']) + abs(kept_positions[stock])

    if qty != 0:
        try:
            trade_account.api.submit_order(
                symbol = stock.symbol,
                qty = int(qty),
                side = side,
                type='market',
                time_in_force='gtc'
            )
            return True
        except:
            print("Order Failed")
    
    return False

def make_trades(trade_account, stocks_to_hold):
    positions = trade_account.api.list_positions()
    held_symbols = [x.symbol for x in stocks_to_hold]
    kept_positions = {}
    for p in positions:
        if p.symbol not in held_symbols:
            side = 'sell'
            if int(p.qty) < 0:
                p.qty = abs(int(p.qty))
                side = 'buy'
            trade_account.api.submit_order(
                    symbol = p.symbol,
                    qty = p.qty,
                    side = side,
                    type = 'market',
                    time_in_force = 'day'
                )
        else:
            kept_positions[p.symbol] = int(p.qty)

    for stock in stocks_to_hold:
        submit_trade(trade_account, stock, kept_positions)

def trade_stage(high_volume_stocks):
    trade_account = Account(list(high_volume_stocks.keys()))

    while trade_account.market_open_flag:
        try:
            minute_bars = trade_account.ws.recv()
        except:
            trade_account.stream_connect()
            trade_account.reconnect()
            minute_bars = trade_account.ws.recv()

        minute_bars = ast.literal_eval(minute_bars)
        for last_bar in minute_bars:
            high_volume_stocks[last_bar['S']].min_bars.append(last_bar)
            if len(high_volume_stocks[last_bar['S']].min_bars) > PERIOD * 390:
                    high_volume_stocks[last_bar['S']].min_bars.pop(0)

        if datetime.datetime.now().hour == 21: # set hour to 13 for local machine 21 for cloud
            trade_account.market_open_flag = False
            #if trade submit trade

        if datetime.datetime.today().day == trade_account.last_time.day:
            continue
        trade_account.last_time = datetime.datetime.today()
            
        stocks_to_hold = get_hold_stocks(high_volume_stocks)
        
        make_trades(trade_account, stocks_to_hold)
        
    return trade_account


def Group(bars, bin_width):
    out_bars = []
    for start in range(0, len(bars), bin_width):
        if start+bin_width < len(bars):
            group = bars[start: start+bin_width]
        else:
            group = bars[start:]
        new_bar = {}
        #new_bar.Time = group[0].Time
        new_bar['o'] = group[0]['o']
        new_bar['c'] = group[-1]['c']
        new_bar['h'] = max(x['h'] for x in group)
        new_bar['l'] = min(x['l'] for x in group)
        new_bar['v'] =  sum(x['v'] for x in group)
        out_bars.append(new_bar)
    
    return out_bars

def main():
    if len(sys.argv) != 2:
        print("ERROR: Wrong number of arguments!")
        exit(-1)
    
    with open(sys.argv[1]) as file:
        lines = file.readlines()
        lines = [line.rstrip() for line in lines]

    api = tradeapi.REST(keys, keys_to_the_vip, paper_products)
    high_volume_stocks = {}
    first_day = datetime.datetime.today() - datetime.timedelta(days=6)
    for line in lines:
        stock_data = StockData(line)
        stock_data.min_bars = df_to_bars(yf.Ticker(line).history(start=first_day.strftime('%Y-%m-%d'), interval='1m'))
        stock_data.day_bars = df_to_bars(yf.Ticker(line).history(start=first_day.strftime('%Y-%m-%d'), interval='1d'))
        high_volume_stocks[line] = stock_data
    
    while datetime.datetime.today().weekday() != 5:
        api = tradeapi.REST(keys, keys_to_the_vip, paper_products)
        sleeping_stage(api)
    
        trade_stage(high_volume_stocks)

        for stock in high_volume_stocks.keys():
            high_volume_stocks[stock].day_bars = Group(high_volume_stocks[stock].min_bars, 390)

        time.sleep(21600) # Sleep for 6 hours
    

if __name__ == "__main__":
    main()
