from enum import Enum, unique


@unique
class SecurityType(Enum):
	Unknown = 0
	Future = 1
	Option = 2
	Stock = 3
	Index = 4


class Security:
	def __init__(self):
		self.Id: str = None
		self.type: SecurityType = SecurityType.Unknown
		self.lot_size: int = 0
		self.currency: str = None
		self.fx_rate: float = 1.0
		self.trans_cost_multiplier: float = 0.0
		self.trans_cost_fix_amount: float = 0.0
		self.exchange: str = None

	def init_from_token(self, token):
		self.Id = token[1]
		self.lot_size = int(token[2])
		self.currency = token[3]
		self.fx_rate = float(token[4])
		self.trans_cost_multiplier = float(token[5])
		self.trans_cost_fix_amount = float(token[6])
		self.exchange = token[7]

	def conversion(self):
		return 1.0
	
	def round_lot(self, num):
		return int(float(num)/self.lot_size) * self.lot_size
	
	def get_trade_amount(self, quantity: int, price: float):
		return quantity * price * self. conversion()

	def get_transaction_cost(self, quantity: int, price: float):
		return abs(self.get_trade_amount(quantity, price)) * self.trans_cost_multiplier + self.trans_cost_fix_amount
	
	def to_base_ccy(self, amount: float):
		return self.fx_rate * amount
	
	def to_local_ccy(self, amount: float):
		return amount / self.fx_rate

	def get_initial_margin(self, quantity: int, price: float):
		return abs(self.get_trade_amount(quantity, price))

	def get_trading_margin(self, quantity: int, price: float):
		return abs(self.get_trade_amount(quantity, price))
	
	def get_average_price(self, quantity:int, amount: float, amount_is_base_ccy = True, amount_contains_conversion_ratio = True):
		if amount_is_base_ccy:
			amount = self.to_local_ccy(amount)
		if amount_contains_conversion_ratio:
			amount = amount / self.conversion()
		return amount / quantity;

class Future(Security):
	def __init__(self):
		super(Future, self).__init__()
		self.type = SecurityType.Future
		self.conversion_ratio: float = 0.0
		self.init_margin_ratio: float = 0.0
		self.call_margin_ratio: float = 0.0

	def init_from_token(self, token):
		super(Future, self).init_from_token(token)
		self.conversion_ratio = float(token[8])
		self.init_margin_ratio = float(token[9])
		self.call_margin_ratio = float(token[10])

	def conversion(self):
		return self.conversion_ratio

	def get_initial_margin(self, quantity: int, price: float):
		return abs(self.get_trade_amount(quantity, price) * self.init_margin_ratio)

	def get_trading_margin(self, quantity: int, price: float):
		return abs(self.get_trade_amount(quantity, price) * self.call_margin_ratio)

class SecurityCache:
	def __init__(self):
		self.map = dict()

	def get_security(self, sec_Id):
		if sec_Id in self.map:
			return self.map[sec_Id]
		return None

	def insert_security(self, security):
		sec_Id = security.Id
		if sec_Id in self.map:
			return False, self.map[sec_Id]
		self.map[sec_Id] = security
		return True, security

	def create_security(self, token):
		if token[0] == "F":
			future = Future()
			future.init_from_token(token)
			self.insert_security(future)

	def load_securities_from_file(self, filename):
		with open(filename, 'r') as f:
			for line in f.readlines():
				if line.startswith("#"):
					continue
				self.create_security(line.strip().split(','))
		return len(self.map) > 0


class SecurityCacheSingleton:
	__instance__: SecurityCache = SecurityCache()

	@staticmethod
	def initialize(file: str, services: dict):
		return SecurityCacheSingleton.get().load_securities_from_file(file)

	@staticmethod
	def get():
		return SecurityCacheSingleton.__instance__

