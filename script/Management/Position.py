from Management.Trade import *


class Position:
	def __init__(self, sec):
		self.sec: Security = sec
		self.quantity: int = 0
		self.current_price: float = 0.0
		self.last_update_date: str = None
		#following are base ccy
		self.total_amount: float = 0.0
		self.margin: float = 0.0
		self.realized_pnl: float = 0.0
	
	def get_realized_pnl(self):
		return self.realized_pnl

	def update_margin_from_open_trade(self, trade: Trade, mgr):
		margin = self.sec.to_base_ccy(self.sec.get_initial_margin(trade.quantity, trade.price))
		self.margin += margin
		mgr.cash -= margin

	def adjust_margin(self, mgr):
		u_pnl = self.get_unrealized_pnl()
		if self.quantity == 0:
			margin = 0.0
		elif u_pnl + self.margin <= 0:
			margin = u_pnl * -1
		else:
			avg_px = self.sec.get_average_price(self.quantity, self.total_amount)
			margin = self.sec.to_base_ccy(self.sec.get_trading_margin(self.quantity, avg_px))
		mgr.cash = mgr.cash - margin + self.margin
		self.margin = margin 

	def get_unrealized_pnl(self):
		return self.sec.to_base_ccy(self.sec.get_trade_amount(self.quantity, self.current_price)) - self.total_amount
	
	def update_by_trade(self, trade: Trade, mgr):
		sec = self.sec
		is_open: bool = self.quantity * trade.quantity >= 0
		self.last_update_date = trade.date
		self.current_price = trade.price
		mgr.cash -= sec.to_base_ccy(trade.trans_cost)

		if is_open:
			self.quantity += trade.quantity
			self.total_amount += sec.to_base_ccy(sec.get_trade_amount(trade.quantity, trade.price))
		elif abs(self.quantity) <= abs(trade.quantity): #cross
			pnl: float = sec.to_base_ccy(sec.get_trade_amount(self.quantity, trade.price)) - self.total_amount
			self.realized_pnl += pnl
			mgr.cash += pnl
			self.quantity += trade.quantity
			self.total_amount = sec.to_base_ccy(sec.get_trade_amount(self.quantity, self.current_price))
		else: # partial cover
			covered_amount = self.total_amount * abs(trade.quantity) / abs(self.quantity)
			pnl: float = sec.to_base_ccy(sec.get_trade_amount(trade.quantity * -1, trade.price)) - covered_amount
			self.realized_pnl += pnl
			mgr.cash += pnl
			self.quantity += trade.quantity
			self.total_amount -= covered_amount

		if is_open:
			self.update_margin_from_open_trade(trade, mgr)
		else:
			self.adjust_margin(mgr)

class PositionStatus:
	def __init__(self, total_asset: float, free_cash: float, realized_pnl: float, unrealized_pnl: float):
		self.total_asset = total_asset
		self.free_cash = free_cash
		self.realized_pnl = realized_pnl
		self.unrealized_pnl = unrealized_pnl
	
	def __eq__(self, other):
		return  self.total_asset == other.total_asset \
			and self.free_cash == other.free_cash \
			and self.realized_pnl == other.realized_pnl \
			and self.unrealized_pnl == other.unrealized_pnl

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

		services[name] = PositionManager(trade_mgr, cash)
		return True
	
	
	def on_trade(self, trade: Trade):
		sec: Security = SecurityCacheSingleton.get().get_security(trade.secId)
		assert sec is not None

		if trade.secId not in self.positions:
			self.positions[trade.secId] = Position(sec)

		self.positions[trade.secId].update_by_trade(trade, self)

	def __init__(self, trade_mgr: TradeManager, init_cash: float):
		self.init_cash: float = init_cash
		self.cash: float  = init_cash
		self.positions = dict()
		trade_mgr.subscribe(lambda x: self.on_trade(x))
		self.listeners = []

	def subscribe(self, f):
		self.listeners.append(f)

	def on_close_price(self, date: str, px_dict):
		for sec_id in px_dict:
			if sec_id in self.positions:
				pos: Position = self.positions[sec_id]
				pos.last_update_date = date
				pos.current_price = px_dict[sec_id] 
				pos.adjust_margin(self)

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
			r_pnl += pos.get_realized_pnl()
			u_pnl += pos.get_unrealized_pnl()
			margin += pos.margin
		return PositionStatus(self.cash + margin + u_pnl, self.cash, r_pnl, u_pnl)
