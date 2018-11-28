from Management.Security import *
import copy


class Trade:
    def __init__(self):
        self.secId: str = None
        self.quantity: int = 0
        self.price: float = 0.0
        self.date: str = None
        self.trans_cost: float = 0.0

    def set(self, date: str, sec: str, qty: int, px: float, trans_cost: float):
        self.secId = sec
        self.date = date
        self.quantity = qty
        self.trans_cost = trans_cost
        self.price = px


class TradeManager:
    @staticmethod
    def initialize(config: dict, services: dict):
        name = config['name'] if config is not None and 'name' in config else 'TradeManager'
        services[name] = TradeManager()
        return True

    def __init__(self):
        self.trades = dict()
        self.listeners = []

    def add_trade(self, date, sec, qty, px):
        trade = Trade()
        trans_cost = 0.0
        security = SecurityCacheSingleton.get().get_security(sec)
        if security is not None:
            trans_cost = abs(security.trans_cost_multiplier * qty * px + security.trans_cost_fix_amount)
        trade.set(date, sec, qty, px, trans_cost)
        assert (trade.secId is not None and trade.secId != "")
        if trade.secId not in self.trades:
            self.trades[trade.secId] = []
        self.trades[trade.secId].append(trade)
        t = copy.copy(trade)
        for l in self.listeners:
            l(t)

        return t

    def subscribe(self, func):
        self.listeners.append(func)

