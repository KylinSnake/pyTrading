from Management import *

class StrategyManager:
	def __init__(self, order_mgr:OrderManager, mkt_mgr: MarketDataManager, pos_mgr: PositionManager):
		self.order_mgr = order_mgr
		self.entry_signal = dict()
		self.exit_signal = dict()
		self.local_data = dict()
		self.mkt_mgr = mkt_mgr
		self.mkt_mgr.subscribe(self.handle_md)
		self.pos_mgr = pos_mgr
		self.pos_mgr.subscribe(self.handle_position)
		self._cur_sec_ = None
	
	def market_data_manager(self):
		return self.mkt_mgr
	
	def order_manager(self):
		return self.order_mgr
	
	def position_manager(self):
		return self.pos_mgr
	
	def trade_manager(self):
		return get_app_service('TradeManager')
	
	def risk_manager(self):
		return get_app_service('RiskManager')
	
	def security(self):
		return self._cur_sec_
	
	def daily_md_until_current_day(self):
		return self.mkt_mgr.md_map[self.security().Id].get_daily_md_until_current()
	
	def weekly_md_until_current_day(self):
		return self.mkt_mgr.md_map[self.security().Id].get_weekly_md_until_current()

	def monthly_md_until_current_day(self):
		return self.mkt_mgr.md_map[self.security().Id].get_monthly_md_until_current()
	
	def indicator(self, indicator_id: str):
		return self.mkt_mgr.get_current_indicator(self.security().Id, indicator_id)

	def trades(self):
		trades_map = self.trade_manager().trades
		secId = self.security().Id
		return trades_map[secId] if secId in trades_map else list()
	
	def position(self):
		secId = self.security().Id
		return self.pos_mgr.get_position(secId)
	
	def get_local_data(self):
		secId = self.security().Id
		if not secId in self.local_data:
			self.local_data[secId] = dict()
		return self.local_data[secId]
	
	def handle_md(self, mkt: dict()):
		for secId in mkt:
			sec = SecurityCacheSingleton.get().get_security(secId)
			if sec is not None and secId in self.entry_signal:
				self._cur_sec_ = sec
				order = self.entry_signal[secId](self, mkt[secId])
				if order is not None:
					self.order_manager().queue_order(order)
	
	def handle_position(self, pos_manager: PositionManager):
		for secId in pos_manager.positions:
			sec = SecurityCacheSingleton.get().get_security(secId)
			pos = pos_manager.get_position(secId)
			if sec is not None and secId in self.exit_signal:
				self._cur_sec_ = sec
				order = self.exit_signal[secId](self, pos)
				if order is not None:
					self.order_manager().queue_order(order, True)
	
	def set_signal(self, secId, entry_f, exit_f):
		assert entry_f is not None and exit_f is not None
		(v, w) = (None, None)
		if secId in self.entry_signal:
			v = self.entry_signal[secId]
		self.entry_signal[secId] = entry_f
		if secId in self.exit_signal:
			w = self.exit_signal[secId]
		self.exit_signal[secId] = exit_f
		self.local_data[secId] = dict()
		return (v, w)

	@staticmethod
	def initialize(config: dict, services: dict):
		name = config['name'] if config is not None and 'name' in config else 'StrategyManager'
		services[name] = StrategyManager(services['OrderManager'], services['MarketDataManager'], services['PositionManager'])
		return True

