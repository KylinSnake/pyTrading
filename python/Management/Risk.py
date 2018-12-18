from abc import ABCMeta, abstractmethod
from Management.Position import *
from Management.Order import Side
from Common.Util import logger

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

	def __init__(self, pos: PositionManager, setting: dict):
		self.pos_mgr = pos
		self.capital_cap = setting["MaxCapitalPercentage"] / 100.0 if "MaxCapitalPercentage" in setting else 0.5
		self.adjust_open_quantity_functions = dict()
		self.adjust_close_quantity_functions = dict()

	@abstractmethod
	def __maximum_open_quantity__(self, sec: Security, pos: Position, asset: PositionStatus, side: Side, open_price: float):
		pass

	def get_open_quantity(self, sec_Id: str, side: Side, open_price: float):
		sec  = SecurityCacheSingleton.get().get_security(sec_Id)
		assert sec is not None
		pos: Position = self.pos_mgr.get_position(sec_Id)

		# make sure we are flat or open in the same direction
		if (pos.quantity < 0 and side.isBuy()) or (pos.quantity > 0 and side.isSell()):
			return 0
		
		asset : PositionStatus = self.pos_mgr.get_status()

		# make sure we have enough cash
		if asset.free_cash / asset.total_asset < (1 - self.capital_cap):
			return 0
		
		quantity = self.__maximum_open_quantity__(sec, pos, asset, side, open_price)

		if quantity != 0 and sec_Id in self.adjust_open_quantity_functions:
			func = self.adjust_open_quantity_functions[sec_Id]
			if func is not None:
				quantity = func(sec, pos, asset, quantity, open_price)

		if quantity != 0 and asset.free_cash < sec.to_base_ccy(sec.get_transaction_cost(quantity, open_price) + sec.get_initial_margin(quantity, open_price)):
			return 0

		return sec.round_lot(quantity)
	
	def get_close_quantity(self, sec_Id: str, close_price: float):
		sec  = SecurityCacheSingleton.get().get_security(sec_Id)
		assert sec is not None
		pos: Position = self.pos_mgr.get_position(sec_Id)
		asset : PositionStatus = self.pos_mgr.get_status()

		quantity = pos.quantity * -1
		if quantity != 0 and sec_Id in self.adjust_close_quantity_functions:
			func = self.adjust_close_quantity_functions[sec_Id]
			if func is not None:
				quantity = func(sec, pos, asset, quantity, close_price)

		return sec.round_lot(quantity)


class FixPctRiskManager(RiskManager):
	def __init__(self, pos: PositionManager, setting: dict):
		super(FixPctRiskManager, self).__init__(pos, setting)
		self.pct: float = setting["TotalRiskPercentage"] / 100.0 if "TotalRiskPercentage" in setting else 0.015
		self.risk_per_share_pct = setting['RiskPerSharePercentage'] / 100.0 if 'RiskPerSharePercentage' in setting else 0.03

	def __maximum_open_quantity__(self, sec: Security, pos: Position, asset: PositionStatus, side: Side, open_price: float):
		risk_per_share: float = sec.to_base_ccy(sec.get_trade_amount(1, open_price) * self.risk_per_share_pct)
		total_risk: float = self.pct * asset.total_asset
		qty: int = int(total_risk/risk_per_share) - abs(pos.quantity)
		if qty > 0:
			return qty if side.isBuy() else qty * -1
		return 0
		
