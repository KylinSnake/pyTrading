from Common import *
from Indicators.Indicator import *


class MDReplayer:
	def __init__(self, md: np.ndarray, sec_Id: str, start_index: int):
		self.sec_Id = sec_Id
		self.daily_md = md
		self.init_start = start_index
		self.daily_current = self.init_start
		self.monthly_md = np.empty(self.daily_md.shape, self.daily_md.dtype)
		self.weekly_md = np.empty(self.daily_md.shape, self.daily_md.dtype)
		self.monthly_md[0] = self.daily_md[0]
		self.weekly_md[0] = self.daily_md[0]
		self.monthly_current = 0
		self.weekly_current = 0
		self.accumulate_monthly_md(0, self.daily_current)
		self.accumulate_weekly_md(0, self.daily_current)
		self.daily_indicators = dict()

	def get_monthly_md_until_current(self):
		return self.monthly_md[:self.monthly_current + 1]

	def get_weekly_md_until_current(self):
		return self.weekly_md[:self.weekly_current + 1]
	
	def get_daily_md_until_current(self):
		return self.daily_md[:self.daily_current + 1]

	def has_next_day(self):
		return self.daily_current < self.daily_md.shape[0]

	def peak_current_date(self):
		if self.has_next_day():
			return md_date(self.daily_md[self.daily_current])
		return None
	
	def add_daily_indicator(self, config):
		assert config['SecId'] == self.sec_Id
		value = generate_indicator(self.daily_md, config['Type'], 
				config['Parameters'] if 'Parameters' in config else None)
		self.daily_indicators[str(config['Id'])] = value
	
	def get_daily_indicator_until_current_day(self, Id: str):
		def slice_data(value, end):
			if isinstance(value, np.ndarray):
				return value[0:end]
			if isinstance(value, list):
				return [slice_data(i, end) for i in value]
			if isinstance(value, dict):
				keys = value.keys()
				return dict(zip(keys, [slice_data(value[key], end) for key in keys]))
			raise ValueError('cannot slice indicators %s'%str(type(value)))
		return slice_data(self.daily_indicators[Id], self.daily_current+1)

	
	def get_current(self):
		if self.has_next_day():
			return self.daily_md[self.daily_current]
		return None
	
	def update_accumulative_md(self):
		if self.has_next_day():
			self.accumulate_weekly_md(self.daily_current, self.daily_current + 1)
			self.accumulate_monthly_md(self.daily_current, self.daily_current + 1)

	def move_next(self):
		if self.has_next_day():
			self.daily_current += 1
			self.update_accumulative_md()

	def accumulate_weekly_md(self, begin: int, end: int):
		self.weekly_current = self.calculate_duration_md_until_current(
			self.weekly_md, begin, end, self.weekly_current, is_same_week
		)

	def accumulate_monthly_md(self, begin: int, end: int):
		self.monthly_current = self.calculate_duration_md_until_current(
			self.monthly_md, begin, end, self.monthly_current, is_same_month
		)

	def calculate_duration_md_until_current(self, ret: np.ndarray, daily_begin: int,
											daily_end: int, output_begin: int, func):
		for i in range(daily_begin, daily_end):
			daily = self.daily_md[i]
			output = ret[output_begin]
			if func(md_date(daily), md_date(output)):
				set_close(output, md_close(daily))
				if md_high(daily) > md_high(output):
					set_high(output, md_high(daily))
				if md_low(daily) < md_low(output):
					set_low(output, md_low(daily))
			else:
				output_begin += 1
				ret[output_begin] = daily
		return output_begin


class MarketDataManager:
	@staticmethod
	def initialize(config: dict, services: dict):
		name = config['name'] if config is not None and 'name' in config else 'MarketDataManager'
		md = config['MarketData']
		ind = config['Indicator']
		services[name] = MarketDataManager(md, ind)
		return True

	def __init__(self, md: list, ind: list):
		self.md_map = dict()
		self.sod_listeners = []
		self.eod_listeners = []
		self.listeners = []
		configs = dict()

		for config in ind:
			sec = config['SecId']
			if not sec in configs:
				configs[sec] = list()
			configs[sec].append(config)

		for item in md:
			sec_Id = str(item["SecId"])
			file_path = item["File"]
			start = int(item["Start"]) if "Start" in item else 100
			replay = MDReplayer(load_market_data_from_file(file_path), sec_Id, start)
			if sec_Id in configs:
				for config in configs[sec_Id]:
					replay.add_daily_indicator(config)
			self.md_map[sec_Id]=replay
	
	def get_current_indicator(self, secId: str, indicator_Id: str):
		return self.md_map[secId].get_daily_indicator_until_current_day(indicator_Id)

	def subscribe(self, f):
		self.listeners.append(f)

	def subscribe_eod(self, f):
		self.sod_listeners.append(f)
	
	def subscribe_sod(self, f):
		self.eod_listeners.append(f)

	def notify(self, msg: dict):
		for f in self.sod_listeners:
			f(msg)
		for f in self.listeners:
			f(msg)
		for f in self.eod_listeners:
			f(msg)

	def run(self):
		while True:
			msg = dict()
			dates = [x.peak_current_date() for x in self.md_map.values() if x.has_next_day()]
			if len(dates) == 0:
				self.notify(msg)
				break
			min_date = min(dates)
			movable=[]
			for x in self.md_map.values():
				if x.peak_current_date() == min_date:
					msg[x.sec_Id] = x.get_current()
					movable.append(x)
			self.notify(msg)

			for x in movable:
				x.move_next()

