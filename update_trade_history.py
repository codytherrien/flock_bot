import sys
from turtle import update
import alpaca_trade_api as tradeapi
from street_cred import *
import pandas as pd
import yfinance as yf
import datetime as dt
from Trade import Trade

def generate_samples(orders):
    active_orders = {}
    samples = []
    for order in orders:
        if order.symbol not in active_orders.keys() and order.side == 'sell':
            continue
        
        if order.symbol not in active_orders.keys():
            active_orders[order.symbol] = Trade(order.transaction_time.date(), int(order.qty), order.order_status, order.side, float(order.price))
        elif active_orders[order.symbol].status == 'partially_filled':
            active_orders[order.symbol].update_entry(int(order.qty), order.order_status, float(order.price))
        elif active_orders[order.symbol].close_flag:
            active_orders[order.symbol].close_position(int(order.qty), order.order_status, float(order.price))
        elif active_orders[order.symbol].close_flag and active_orders[order.symbol].exit_status == 'partially_filled':
            active_orders[order.symbol].update_close(int(order.qty), order.order_status, float(order.price))

        if active_orders[order.symbol].finish_flag == True:
            samples.append(active_orders[order.symbol].to_sample(order.symbol))
            del active_orders[order.symbol]
        
    return samples

def update_samples(df):
    samples = []

    for i, row in df.iterrows():
        start_date = row['date'] - dt.timedelta(days=7)
        start_date = start_date.strftime('%Y-%m-%d')
        end_date = row['date'].strftime('%Y-%m-%d')
        stock_df = yf.Ticker(row['symbol']).history(start=start_date, end=end_date)
        max_val = stock_df['High'].max()
        min_val = stock_df['Low'].min()
        med_val = min_val + (max_val - min_val)/2
        max_val = max_val / med_val
        min_val = min_val / med_val
        price = row['price'] / med_val
        if row['side'] == 'buy':
            side = 1
        else:
            side = 0
        samples.append([min_val, max_val, price, side, row['win']])

    return samples

def main():
    if len(sys.argv) != 2:
        print("ERROR: Wrong number of Arguments.")
        print("Include date in YYYY-MM-dd form")
        exit(-1)
    
    api = tradeapi.REST(keys, keys_to_the_vip, paper_products)
    today = dt.datetime.today().date().strftime('%Y-%m-%d')

    orders = api.get_activities('FILL', after=sys.argv[1], until=today)
    orders.reverse()

    samples = generate_samples(orders)

    columns = ['date', 'symbol', 'price', 'side', 'win']
    df = pd.DataFrame(data=samples, columns=columns)

    samples = update_samples(df)

    columns = ['week_low', 'week_high', 'price', 'side', 'win']
    final_df = pd.DataFrame(samples, columns=columns)
    final_df

    past_df = pd.read_csv("trade_history.csv")

    final_df = pd.concat([past_df, final_df])
    final_df.to_csv("trade_history.csv", index=False)

    return
    


if __name__ == "__main__":
    main()