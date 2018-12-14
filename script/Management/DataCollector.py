from Management import *
from Common.Util import logger
import numpy as np
import datetime
import os

class DataCollector:
	def __init__(self, services, base_dir, with_date_time_sub_dir):
		self.md_svc = services['MarketDataManager']
		services['TradeManager'].subscribe(self.handle_trade)
		services['PositionManager'].subscribe(self.handle_pos)
		self.trade_files = dict()
		self.pos_files = dict()
		self.base_path = base_dir
		if with_date_time_sub_dir:
			directory = self.base_path + '/%s'%(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
			if not os.path.exists(directory):
				os.makedirs(directory)
			self.base_path = directory
		self.asset_file=open(self.base_path + '/asset.txt', 'w')
		self.output_md()
	
	def __del__(self):
		def clean_up(files):
			for i in files:
				files[i].close()
		clean_up(self.trade_files)
		clean_up(self.pos_files)
		self.asset_file.close()
	
	
	def output_md(self):
		for Id in self.md_svc.md_map:
			md_data = self.md_svc.md_map[Id].daily_md
			np.savetxt(self.base_path + '/%s_md.csv'%Id, md_data, delimiter=',', fmt='%s,%.4f,%.4f,%.4f,%.4f,%.4f')

			indicators = self.md_svc.get_all_indicators(Id)
			date = md_date(md_data)
			for ind_name in indicators:
				name = self.base_path + '/%s_indicator_%s.csv'%(Id, ind_name)
				value = date
				ind = indicators[ind_name]
				ind_fmt = '%s'
				if isinstance(ind, np.ndarray):
					value = np.vstack([date.astype(str), ind.astype(str)])
				elif isinstance(ind, tuple):
					value = np.vstack([date.astype(str)] + [x.astype(str) for x in list(ind)])
				elif isinstance(ind, list):
					value = np.vstack([date.astype(str)] + [x.astype(str) for x in ind])
				elif isinstance(ind, dict):
					value = np.vstack([date.astype(str)] + [x.astype(str) for x in ind.values()])
				value = np.transpose(value)
				ind_fmt +=',%s'*(value.shape[1] - 1)
				np.savetxt(name, value, delimiter=',', fmt=ind_fmt)

	def handle_trade(self, trade:Trade):
		if trade.secId not in self.trade_files:
			self.trade_files[trade.secId] = open(self.base_path + '/%s_trade.csv'%trade.secId, 'w')
		self.trade_files[trade.secId].write("%s\n"%trade.to_csv())
	
	def handle_pos(self, pos_mgr:PositionManager, date: str):
		asset: PositionStatus = pos_mgr.get_status()
		self.asset_file.write('%s,%s\n'%(date, asset.to_csv()))
		for secId in pos_mgr.positions:
			pos = pos_mgr.positions[secId]
			if secId not in self.pos_files:
				self.pos_files[secId] = open(self.base_path + '/%s_pos.csv'%secId, 'w')
			self.pos_files[secId].write('%s\n'%pos.to_csv())
	

	@staticmethod
	def initialize(config: dict, services:dict):
		name = config['name'] if config is not None and 'name' in config else 'DataCollector'
		if 'base_dir' not in config:
			return False
		with_date_time = bool(config['path_with_datetime']) if 'path_with_datetime' in config else True
		services[name] = DataCollector(services, config['base_dir'], with_date_time)
		return True

