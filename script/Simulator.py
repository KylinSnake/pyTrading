from Signals.SignalCore import *
import numpy as np


class SimulationResult:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.trades = []
        self.entry_signals = None
        self.stops = []

    def profit(self):
        mat = np.array(self.trades)
        return -1 * np.inner(mat[:, 0], mat[:, 1])


class Simulator:
    def __init__(self):
        self.market_data = None
        self.indicators = dict()
        self.simulation_results = []
        self.entry_signal_generator = None
        self.exit_signal_generator = None

    def load_market_data(self, filename):
        self.market_data = np.loadtxt(filename,
                                      dtype={'names': ('date', 'open', 'high', 'low', 'close', 'volume'),
                                             'formats': ('S10', 'f4', 'f4', 'f4', 'f4', 'f4')},
                                      delimiter=',', skiprows=1)

    def add_indicator(self, name, data):
        self.indicators[name] = data

    def append_simulation_range(self, start, end):
        self.simulation_results.append(SimulationResult(start, end))

    def generate_entry_signal(self):
        return self.entry_signal_generator(self.market_data, self.indicators)

    def generate_exit_signal(self, signal, price, entry_signal):
        return self.exit_signal_generator(self.market_data, self.indicators, signal, price, entry_signal)

    def get_open_position(self):
        return 1.0

    def open_trade(self, current_day, signal):
        #price = self.market_data[current_day + 1]['open']
        price = self.market_data[current_day]['close']
        position = self.get_open_position()
        if signal == SignalType.SellOpen:
            position *= -1
        return price, position, current_day

    def run(self):
        assert self.market_data is not None
        assert self.entry_signal_generator is not None
        assert self.exit_signal_generator is not None
        for result in self.simulation_results:
            entry_signal = self.generate_entry_signal()
            signal = SignalType.NoAction
            exit_signal = None
            average_price = 0.0
            total_position = 0.0
            for i in range(result.start, result.end):
                if not entry_signal.started():
                    entry_signal.start(i)
                    continue
                entry_signal.next()
                if signal != SignalType.NoAction:
                    assert exit_signal is not None
                    exit_signal.next()
                    if i == result.end - 1 or exit_signal.signal() == SignalType.Stop:
                        price = exit_signal.current_stop
                        position = -1 * total_position
                        result.trades.append((price, position, i))
                        exit_signal.stop()
                        result.stops.append(exit_signal.stops)
                        exit_signal = None
                        average_price = 0.0
                        total_position = 0.0
                        signal = SignalType.NoAction
                        entry_signal.reset_signal()
                    else:
                        exit_signal.update()

                if signal == SignalType.NoAction:
                    signal = entry_signal.signal()
                    if signal != SignalType.NoAction:
                        (price, position, day) = self.open_trade(i, signal)
                        result.trades.append((price, position, day))
                        exit_signal = self.generate_exit_signal(signal, price, entry_signal)
                        exit_signal.start(i)
                        entry_signal.acknowledge_signal()
                        average_price = (average_price * total_position
                                         + price * position) / (total_position + position)
                        total_position += position
                entry_signal.update()
            entry_signal.stop()
            result.entry_signals = entry_signal.signals






