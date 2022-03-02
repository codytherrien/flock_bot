class Trade:
    def __init__(self, date, qty, status, side, price):
        self.date = date
        self.qty = qty 
        self.status = status
        self.side = side
        self.entry_price = price
        self.finish_flag = False
        if status == 'filled':
            self.close_flag = True
        else:
            self.close_flag = False

    def update_entry(self, qty, status, price):
        self.status = status
        prev_total = self.qty*self.entry_price
        new_total = qty*price
        self.qty = self.qty + qty
        self.entry_price = (new_total + prev_total) / self.qty
        if status == 'filled':
            self.close_flag = True

    def close_position(self, qty, status, price):
        self.exit_price = price
        self.exit_qty = qty
        self.exit_status = status
        if status == 'filled':
            self._check_win()
            self.finish_flag = True
    
    def update_close(self, qty, status, price):
        self.exit_status = status
        prev_total = self.exit_qty*self.exit_price
        new_total = qty*price
        self.exit_qty = self.exit_qty + qty
        self.exit_price (new_total + prev_total) / self.exit_qty
        if status == 'filled':
            self._check_win()
            self.finish_flag = True

    def _check_win(self):
        if self.side == 'sell_short':
            if self.entry_price > self.exit_price:
                self.win = 1
            else:
                self.win = 0
        else:
            if self.entry_price < self.exit_price:
                self.win = 1
            else:
                self.win = 0
    
    def to_sample(self, symbol):
        sample = []
        sample.append(self.date)
        sample.append(symbol)
        sample.append(self.entry_price)
        sample.append(self.side)
        sample.append(self.win)

        return sample