from Signals.SignalCore import *
import numpy as np


class FixDaysExitSignal(ExitSignal):
    def __init__(self, mkt_data, open_signal, open_price, duration):
        super(FixDaysExitSignal, self).__init__(mkt_data, open_signal, open_price)
        self.duration = duration
        self.count_day = -1

    def start(self, today):
        super(FixDaysExitSignal, self).start(today)
        self.count_day = 0

    def stop(self):
        self.count_day = -1
        super(FixDaysExitSignal, self).stop()

    def get_stop(self, price):
        if self.open_signal == SignalType.BuyOpen:
            return float('-inf')
        return float('inf')

    def signal(self):
        if self.count_day % self.duration == 0:
            return SignalType.Stop
        return SignalType.NoAction

    def update_data(self):
        super(FixDaysExitSignal, self).update_data()
        if self.signal() != SignalType.NoAction:
            self.count_day = 0


class AmountExitSignal(ExitSignal):
    def __init__(self, mkt_data, open_signal, open_price, amount):
        super(AmountExitSignal, self).__init__(mkt_data, open_signal, open_price)
        self.amount = amount
        if type(amount) != np.ndarray:
            assert amount >= 0.0
        else:
            assert len(amount) == len(mkt_data)

    def get_stop(self, price):
        amount = self.amount
        if type(amount) == np.ndarray:
            amount = amount[self.current_day]
        if self.open_signal == SignalType.BuyOpen:
            return price - amount
        return price + amount


class StopExitSignal(ExitSignal):
    def __init__(self, mkt_data, open_signal, open_price, stop_price):
        super(StopExitSignal, self).__init__(mkt_data, open_signal, open_price)
        self.stop_price = stop_price
        if type(stop_price) != np.ndarray:
            assert stop_price >= 0.0
        else:
            assert len(stop_price) == len(mkt_data)

    def get_stop(self, price):
        amount = self.stop_price
        if type(amount) == np.ndarray:
            amount = amount[self.current_day]
        return amount


class FixPercentageExitSignal(ExitSignal):
    def __init__(self, mkt_data, open_signal, open_price, pct):
        super(FixPercentageExitSignal, self).__init__(mkt_data, open_signal, open_price)
        if type(pct) != np.ndarray:
            assert 0.0 <= pct <= 1.0
        else:
            assert len(pct) == len(mkt_data)
        self.percentage = pct

    def get_stop(self, price):
        pct = self.percentage
        if type(pct) == np.ndarray:
            pct = pct[self.current_day]
            assert 0.0 <= pct <= 1.0
        if self.open_signal == SignalType.BuyOpen:
            return price * (1 - pct)
        return price * (1 + pct)
