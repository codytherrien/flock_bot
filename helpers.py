def df_to_bars(df):
    bar_list = []
    for i, row in df.iterrows():
        new_bar = {}
        #new_bar.Time = i[1]
        new_bar['o'] = row['Open']
        new_bar['c'] = row['Close']
        new_bar['h'] = row['High']
        new_bar['l'] = row['Low']
        new_bar['v'] = row['Volume']
        bar_list.append(new_bar)
    
    return bar_list 

class StockData:
    def __init__(self, symbol):
        self.symbol = symbol
        self.min_bars = []
        self.day_bars = []
        self.ave_ratio = 0