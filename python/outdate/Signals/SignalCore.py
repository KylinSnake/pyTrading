from enum import Enum, unique
from abc import ABCMeta, abstractmethod


class Signal:
    __metaclass__ = ABCMeta

    def __init__(self, mkt_data):
        self.current_day = -1
        self.market_data = mkt_data

    def start(self, today):
        self.current_day = today

    def stop(self):
        self.current_day = -1

    def started(self):
        return self.current_day != -1

    def next(self):
        if self.current_day != -1:
            self.current_day += 1
            return True
        return False

    @abstractmethod
    def signal(self):
        pass

    def update(self):
        pass


@unique
class SignalType(Enum):
    NoAction = 0
    BuyOpen = 1
    SellOpen = 2
    Stop = 3
    ReOpen = 4


class EntrySignal(Signal):
    def __init__(self, mkt_data):
        super(EntrySignal, self).__init__(mkt_data)
        self.signals = []
        self.current_signal_type = SignalType.NoAction
        self.signal_enable = False
        self.update_enable = False

    def enable_signal(self, *args):
        if len(args) == 0:
            return self.signal_enable
        self.signal_enable = args[0]

    def enable_update(self, *args):
        if len(args) == 0:
            return self.update_enable
        self.update_enable = args[0]

    def start(self, today):
        super(EntrySignal, self).start(today)
        self.signal_enable = True
        self.update_enable = True

    def stop(self):
        self.update_enable = False
        self.signal_enable = False
        super(EntrySignal, self).stop()

    @abstractmethod
    def entry_signal(self):
        pass

    def signal(self):
        if self.signal_enable:
            return self.entry_signal()
        return SignalType.NoAction

    def acknowledge_signal(self, enable_signal=False, enable_update=True):
        self.current_signal_type = self.signal()
        self.signals.append((self.current_day, self.current_signal_type))
        self.enable_signal(enable_signal)
        self.enable_update(enable_update)

    def reset_signal(self):
        self.enable_signal(True)
        self.enable_update(True)

    def update_data(self):
        pass

    def pre_update(self):
        pass

    def post_update(self):
        pass

    def update(self):
        if self.enable_update():
            self.pre_update()
            self.update_data()
            self.post_update()


class ExitSignal(Signal):
    def __init__(self, mkt_data, open_signal, open_price):
        super(ExitSignal, self).__init__(mkt_data)
        self.open_signal = open_signal
        self.price = open_price
        self.init_stop = None
        self.current_stop = None
        self.stops = []

    @abstractmethod
    def get_stop(self, price):
        return float('inf')

    def get_init_stop(self) -> float:
        return self.get_stop(self.price)

    def get_current_stop(self) -> float:
        return self.get_stop(self.market_data[self.current_day]['close'])

    def start(self, today):
        super(ExitSignal, self).start(today)
        self.init_stop = self.get_init_stop()
        self.current_stop = self.init_stop
        self.stops.append((today, self.current_stop))

    def stop(self):
        if self.stops[-1][0] < self.current_day:
            self.update()
        super(ExitSignal, self).stop()

    def update_data(self):
        px = self.get_current_stop()
        if self.open_signal == SignalType.BuyOpen and px > self.current_stop:
            self.current_stop = px
        elif self.open_signal == SignalType.SellOpen and px < self.current_stop:
            self.current_stop = px

    def pre_update(self):
        pass

    def post_update(self):
        self.stops.append((self.current_day, self.current_stop))

    def update(self):
        self.pre_update()
        self.update_data()
        self.post_update()

    def signal(self):
        data = self.market_data[self.current_day]
        if self.open_signal == SignalType.BuyOpen and data['low'] < self.current_stop:
            return SignalType.Stop
        elif self.open_signal == SignalType.SellOpen and data['high'] > self.current_stop:
            return SignalType.Stop
        return SignalType.NoAction
