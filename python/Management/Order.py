from Common import *
from enum import Enum, unique
from Management.Trade import Trade

@unique
class OrderType(Enum):
	Unknown = 0
	Market = 1
	Limit = 2
	Stop = 3
	StopLimit = 4

@unique
class Side(Enum):
	Unknown = 0
	Buy = 1
	Sell = 2
	ShortSell = 3

	def isBuy(self):
		return self == Side.Buy
	
	def isLongSell(self):
		return self == Side.Sell
	
	def isShortSell(self):
		return self == Side.ShortSell
	
	def isSell(self):
		return self.isLongSell() or self.isShortSell()

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

		self.new_order_callbacks = list()
		self.execution_callbacks = list()
	
	def set_callback(self, on_new_order, on_execution):
		if on_new_order is not None:
			self.new_order_callbacks.append(on_new_order)
		if on_execution is not None:
			self.execution_callbacks.append(on_execution)
	
	def on_new_order(self):
		for l in self.new_order_callbacks:
			l(self)
	
	def on_execution(self, trade: Trade):
		for l in self.execution_callbacks:
			l(self, trade)

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
		services['MarketDataManager'].subscribe_sod(self.handle_sod_md)
		services['MarketDataManager'].subscribe_eod(self.handle_eod_md)
		self.order_queue = list()
		self.eod_orders = list()
	
	def queue_order(self, order: Order, is_eod = False):
		if is_eod:
			self.eod_orders.append(order)
		else:
			self.order_queue.append(order)
	
	def on_action(self, order:Order, md: np.ndarray):
		pass
	
	def process(self, msg : dict, orders: list, is_eod: bool):
		unhandled = list()
		for order in orders:
			secId = order.secId
			if secId in msg:
				if self.on_action(order, msg[secId]) or is_eod:
					continue
				order.valid_days -= 1
				if order.valid_days == 0:
					continue
			unhandled.append(order)
		return unhandled
	
	def handle_sod_md(self, msg: dict):
		self.order_queue = self.process(msg, self.order_queue, False)
	
	def handle_eod_md(self, msg: dict):
		self.process(msg, self.eod_orders, True)
		self.eod_orders.clear()

class OrderSimulator(OrderManager):
	def __init__(self, config: dict, services: dict):
		super().__init__(services)
		self.trade_mgr = services['TradeManager']
	
	def on_action(self, order:Order, md: np.ndarray):
		def derivate_price_from_stop(stop_price: float, quantity: int, md: np.ndarray):
			high = md_high(md)
			low = md_low(md)
			if (stop_price - high)*(stop_price - low) < 0:
				return stop_price
			if (quantity > 0 and low > stop_price) or (quantity < 0 and high < stop_price):
				return md_open(md)
			return 0.0
		price = 0
		if order.order_type == OrderType.Market:
			price = md_open(md)
		elif order.order_type == OrderType.Limit:
			price = order.limit_price
		elif order.order_type == OrderType.Stop:
			price = derivate_price_from_stop(order.stop_price, order.quantity, md)
		elif order.order_type == OrderType.StopLimit:
			price = order.limit_price
			if (price - md_high(md)) * (price - md_low(md)) > 0:
				price = derivate_price_from_stop(order.stop_price, order.quantity, md)

		if price == 0 or (price - md_high(md)) * (price - md_low(md)) > 0:
			return False

		order.on_new_order()
		t = self.trade_mgr.add_trade(md_date(md), order.secId, order.quantity, price)
		order.on_execution(t)
		return True
