from Management.Trade import *


class Position:
    def __init__(self, sec):
        # price should be on base ccy
        self.id: str = sec
        self.quantity: int = 0
        self.price: float = 0.0
        self.date: str = None
        self.average_trade_price: float = 0.0
        self.margin: float = 0.0
        self.realized_pnl: float = 0.0

    def get_unrealized_pnl(self):
        sec: Security = SecurityCacheSingleton.get().get_security(self.id)
        assert sec is not None
        conversion = sec.conversion()
        return (self.price - self.average_trade_price) * self.quantity * conversion


class PositionManager:
    @staticmethod
    def initialize(config: dict, services: dict):
        name = config['name'] if config is not None and "name" in config else "PositionManager"
        value: dict = config['value']
        trade_mgr_name = value["TradeManagerName"] if "TradeManagerName" in \
                                                       value else "TradeManager"
        if trade_mgr_name in services:
            trade_mgr = services[trade_mgr_name]
        else:
            return False

        if "init_cash" in value:
            cash = float(value['init_cash'])
        else:
            return False

        services[name] = PositionManager(trade_mgr, cash,
                                         True if "isMargin" in value else False)
        return True

    def on_trade(self, trade: Trade):
        if trade.secId not in self.positions:
            self.positions[trade.secId] = Position(trade.secId)

        pos: Position = self.positions[trade.secId]
        margin = 0.0
        is_open: bool = pos.quantity * trade.quantity >= 0
        sec: Security = SecurityCacheSingleton.get().get_security(trade.secId)
        assert sec is not None
        fx_rate: float = sec.fx_rate
        conversion: float = sec.conversion()

        self.cash -= trade.trans_cost * conversion * fx_rate
        turnover = conversion * fx_rate * (trade.price * trade.quantity)

        if self.support_margin:
            if is_open:
                if sec.type == SecurityType.Future:
                    margin = abs(turnover) * sec.init_margin_ratio
                # for margin, cash will be only adjust by open trade margin here
                # and the close trade will adjust cash when calculating PNL
                self.cash -= margin
                pos.margin += margin
        else:
            # for non-margin, cash will be adjusted by trade turnover
            self.cash -= turnover

        pos.price = trade.price * fx_rate
        pos.date = trade.date
        if is_open or abs(pos.quantity) > abs(trade.quantity):
            total_amount = pos.average_trade_price * pos.quantity \
                       + pos.price * trade.quantity
            pos.quantity += trade.quantity
            pos.average_trade_price = total_amount / pos.quantity
            if self.support_margin and not is_open:
                self.adjust_margin(pos)
        else:  # cross side
            pnl: float = (pos.price - pos.average_trade_price) * pos.quantity \
                         * sec.conversion()
            pos.realized_pnl += pnl
            pos.quantity += trade.quantity
            pos.average_trade_price = pos.price
            if self.support_margin:
                self.adjust_margin(pos)
                self.cash += pnl

    def __init__(self, trade_mgr: TradeManager, init_cash: float, is_margin=True):
        self.cash: float = init_cash
        self.positions = dict()
        trade_mgr.subscribe(lambda x: self.on_trade(x))
        self.listeners = []
        self.support_margin: bool = is_margin

    def subscribe(self, f):
        self.listeners.append(f)

    def adjust_margin(self, pos: Position):
        sec: Security = SecurityCacheSingleton.get().get_security(pos.id)
        assert sec is not None
        target_margin: float = abs(pos.quantity) * pos.price * sec.conversion() * sec.call_margin_ratio
        self.cash = self.cash - target_margin + pos.margin
        pos.margin = target_margin

    def on_close_price(self, date: str, px_dict):
        for sec_id in px_dict:
            if sec_id in self.positions:
                sec: Security = SecurityCacheSingleton.get().get_security(sec_id)
                assert sec is not None
                pos: Position = self.positions[sec_id]
                pos.date = date
                pos.price = px_dict[sec_id] * sec.fx_rate
                if self.support_margin:
                    self.adjust_margin(pos)

        for l in self.listeners:
            l(self.cash, self.positions)

    def get_status(self):
        r_pnl: float = 0
        u_pnl: float = 0
        margin: float = 0
        for k in self.positions:
            sec: Security = SecurityCacheSingleton.get().get_security(k)
            assert sec is not None
            pos: Position = self.positions[k]
            r_pnl += pos.realized_pnl
            u_pnl += pos.get_unrealized_pnl()
            if self.support_margin:
                margin += pos.margin
            else:
                margin += pos.average_trade_price * pos.quantity * sec.conversion()
        return self.cash + margin + u_pnl, self.cash, r_pnl, u_pnl
