from Signals.SignalCore import *
import numpy as np


class FixDaysEntrySignal(EntrySignal):
    def __init__(self, mkt_data, duration):
        super(FixDaysEntrySignal, self).__init__(mkt_data)
        self.duration = duration
        self.count_day = -1

    def start(self, today):
        super(FixDaysEntrySignal, self).start(today)
        self.count_day = 0

    def stop(self):
        self.count_day = -1
        super(FixDaysEntrySignal, self).stop()

    def reset_signal(self):
        super(FixDaysEntrySignal, self).reset_signal()
        self.count_day = 0

    def acknowledge_signal(self):
        super(FixDaysEntrySignal, self).acknowledge_signal(False, False)

    def entry_signal(self):
        if self.count_day % self.duration == 0:
            today_data = self.market_data[self.current_day]
            if today_data['close'] > today_data['open']:
                return SignalType.BuyOpen
            else:
                return SignalType.SellOpen
        return SignalType.NoAction

    def update_data(self):
        self.count_day += 1


class RandomProbabilityEntrySignal(EntrySignal):
    def __init__(self, mkt_data, prob_func, prob_percentage):
        super(RandomProbabilityEntrySignal, self).__init__(mkt_data)
        self.func = prob_func
        self.pct_value = prob_percentage

    def entry_signal(self):
        if self.func() <= self.pct_value:
            today_data = self.market_data[self.current_day]
            if today_data['close'] > today_data['open']:
                return SignalType.BuyOpen
            else:
                return SignalType.SellOpen
        return SignalType.NoAction


class NoDirectionPointBreakEntry(EntrySignal):
    def __init__(self, mkt_data, benchmark, points, direction_func = None):
        super(NoDirectionPointBreakEntry, self).__init__(mkt_data)
        assert len(benchmark) == len(points)
        assert len(points) == len(mkt_data)
        self.benchmark = benchmark
        self.points = points
        self.func = direction_func
        if self.func is None:
            self.func = lambda x, t: SignalType.BuyOpen if x[t]['close'] > x[t]['open'] else SignalType.SellOpen

    def entry_signal(self):
        if np.isnan(self.points[self.current_day]) or np.isnan(self.benchmark[self.current_day]):
            return SignalType.NoAction
        if self.points[self.current_day] <= self.benchmark[self.current_day]:
            return SignalType.NoAction
        return self.func(self.market_data, self.current_day)


class DirectionPointBreakEntry(EntrySignal):
    def __init__(self, mkt_data, high_benchmark, high_points, low_benchmark, low_points):
        super(DirectionPointBreakEntry, self).__init__(mkt_data)
        assert len(high_benchmark) == len(high_points)
        assert len(low_benchmark) == len(low_points)
        assert len(high_benchmark) == len(low_benchmark)
        assert len(high_benchmark) == len(mkt_data)
        self.high_benchmark = high_benchmark
        self.low_benchmark = low_benchmark
        self.high_points = high_points
        self.low_points = low_points

    def entry_signal(self):
        t = self.current_day
        if not (np.isnan(self.high_benchmark[t]) or np.isnan(self.high_points[t])):
            if self.high_points[t] > self.high_benchmark[t]:
                return SignalType.BuyOpen
        if not (np.isnan(self.low_benchmark[t]) or np.isnan(self.low_points[t])):
            if self.low_points[t] < self.low_benchmark[t]:
                return SignalType.SellOpen
        return SignalType.NoAction

