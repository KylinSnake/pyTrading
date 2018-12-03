from abc import ABCMeta, abstractmethod
from Management.Position import *


class RiskManager:
	__metaclass__ = ABCMeta

	@staticmethod
	def initialize(config: dict, services: dict):
		name = config['name'] if config is not None and 'name' in config else 'RiskManager'
		value: dict = config['value']
		type_name = config['type']
		pos_name = value["PositionManagerName"] if 'PositionManagerName' in \
												   value else 'PositionManager'
		if pos_name in services:
			pos = services[pos_name]
		else:
			return False
		if type_name == "FixPctRiskManager":
			services[name] = FixPctRiskManager(pos, value)
			return True
		return False

	def __init__(self, pos: PositionManager):
		self.pos_mgr = pos

	@abstractmethod
	def get_open_quantity(self, sec_id: str, is_buy: bool, open_price: float, stop_price: float):
		pass


class FixPctRiskManager(RiskManager):
	def __init__(self, pos: PositionManager, setting: dict):
		super(FixPctRiskManager, self).__init__(pos)
		self.pct: float = setting["RiskPercentage"] / 100.0 if "RiskPercentage" in setting else 0.015
		self.capital_cap = setting["MaxCapitalPercentage"] / 100.0 if "MaxCapitalPercentage" in setting else 0.5

	def get_open_quantity(self, sec_id: str, is_buy: bool, open_price: float, stop_price: float):
		sec: Future = SecurityCacheSingleton.get().get_security(sec_id)
		assert sec is not None
		risk_per_share: float = abs(open_price - stop_price) * sec.fx_rate * sec.conversion()
		open_qty: int = 0
		factor: int = 1 if is_buy else -1
		if sec_id in self.pos_mgr.positions:
			pos: Position = self.pos_mgr.positions[sec_id]
			open_qty = pos.quantity
			if open_qty * factor < 0:
				return 0
		status = self.pos_mgr.get_status()
		if status.free_cash / status.total_asset < (1 - self.capital_cap):
			return 0
		total_risk: float = self.pct * status.total_asset
		qty: int = int(total_risk/risk_per_share)
		qty = abs(qty) - abs(open_qty)
		if qty <= 0:
			return 0
		
		if status.free_cash < sec.to_base_ccy(sec.get_transaction_cost(qty, open_price) + sec.get_initial_margin(qty, open_price)):
			return 0
		return factor * qty
