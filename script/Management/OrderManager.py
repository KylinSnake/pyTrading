from Common import *
from enum import Enum, unique

@unique
class OrderType(Enum):
	Unknown = 0
	Market = 1
	Limit = 2
	Stop = 3
	StopLimit = 4

class Order:
	def __init__(self, secId: str, order_type: OrderType, quantity: int, limit_price: float = 0.0, stop_price: float = 0.0, valid_days = 1):
		self.secId = secId
		self.order_type = order_type
		self.quantity = quantity
		if self.order_type == OrderType.Limit or self.order_type == OrderType.StopLimit:
			self.limit_price = limit_price
			assert self.limit_price > 0.0
		if self.order_type == OrderType.Stop or self.order_type == OrderType.StopLimit:
			self.stop_price = stop_price
			assert self.stop_price > 0.0
			if self.order_type == OrderType.StopLimit:
				assert (self.quantity > 0 and self.stop_price < self.limit_price) \
					or (self.quantity < 0 and self.stop_price > self.limit_price)

		self.valid_days = valid_days

class OrderManager:
	@staticmethod
	def initialize(config: dict, services: dict):
		name = config['name'] if config is not None and 'name' in config else 'OrderManager'
		type_name = config['type']

		if type_name == 'Simulator':
			services[name] = OrderSimulator(config, services)
			return True

		return False
	
	def __init__(self, services: dict):
		services['MarketDataManager'].subscribe(self.handle_md_msg)
		self.order_queue = list()
	
	def queue_order(self, order: Order):
		self.order_queue.append(order)
	
	def on_action(self, order:Order, md: np.ndarray):
		pass
	
	def handle_md_msg(self, msg : dict):
		unhandled = list()
		for order in self.order_queue:
			secId = order.secId
			if secId in msg:
				if self.on_action(order, msg[secId]):
					continue
				order.valid_days -= 1
				if order.valid_days == 0:
					continue
			unhandled.append(order)
		self.order_queue = unhandled

class OrderSimulator(OrderManager):
	def __init__(self, config: dict, services: dict):
		super().__init__(services)
		self.trade_mgr = services['TradeManager']
	
	def on_action(self, order:Order, md: np.ndarray):
		price = 0
		if order.order_type == OrderType.Market:
			price = md_open(md)
		elif order.order_type == OrderType.Limit:
			price = order.limit_price
		elif order.order_type == OrderType.Stop:
			price = order.stop_price
		elif order.order_type == OrderType.StopLimit:
			price = order.limit_price
			if (price - md_high(md)) * (price - md_low(md)) > 0:
				price = order.stop_price

		if price == 0 or (price - md_high(md)) * (price - md_low(md)) > 0:
			return False
			
		self.trade_mgr.add_trade(md_date(md), order.secId, order.quantity, price)
		return True
