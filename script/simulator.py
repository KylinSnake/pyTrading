from Management import *
from Indicators import *
import os

class DataOutputTest:
	def __init__(self, services):
		self.md_svc = services['MarketDataManager']
		self.md_svc.subscribe(self.handle)
		self.files = dict()
	
	def name(self):
		return 'DataOutputTest'
	
	def handle(self, msg: dict):
		if len(msg) == 0:
			[f.close() for f in self.files.values()]
		for Id in msg:
			m = msg[Id]
			if Id not in self.files:
				self.files[Id] = open('../output/%s.txt'%Id, 'w')
			output = [str(md_date(m)), str(md_open(m)), str(md_high(m)), str(md_low(m)), str(md_close(m))]
			if Id == 'HSIY0':
				output.append(str(self.md_svc.get_current_indicator(Id, 'CCI_14')[-1]))
			elif Id == 'IF0001':
				ind = self.md_svc.get_current_indicator(Id, 'DMI_14')
				output += [str(ind['+DI'][-1]), str(ind['-DI'][-1]), str(ind['ADX'][-1])]
			self.files[Id].write(','.join(output) + '\n')

add_runtime_service(DataOutputTest)

def entry_signal(mgr, md):
	pos = mgr.position()
	if pos.quantity != 0:
		return None
	cci = mgr.indicator('CCI_14')
	md_history = mgr.daily_md_until_current_day()
	cur_cci = cci[-1]
	rollback_duration = 10
	dig = None
	if cur_cci > 100.0:
		dig = Diverge(cci, md_high(md_history), False, rollback_duration)
		if dig[0] and dig[1] < 0:
			return Order(mgr.security().Id, OrderType.Market, -1)
	if cur_cci < -100.0:
		dig = Diverge(cci, md_low(md_history), True, rollback_duration)
		if dig[0] and dig[1] > 0:
			return Order(mgr.security().Id, OrderType.Market, 1)
	
	return None

def exit_signal(mgr, pos):
	pct = 0.03
	local = mgr.get_local_data()
	last = local['stop'] if 'stop' in local else None
	if pos.quantity == 0:
		return None
	if pos.quantity > 0:
		price = pos.average_price * (1 - pct)
		if last is not None:
			price = max(price, last)
	else:
		price = pos.average_price * (1 + pct)
		if last is not None:
			price = min(price, last)
	local['stop'] = price
	return Order(mgr.security().Id, OrderType.Stop, pos.quantity * -1, stop_price = price)


register_strategy('HSIY0', entry_signal, exit_signal)

if os.name == 'nt':
	main(['script','c:\\workstation\\config\\config.dos.yaml'])
else:
	main(['script','../config/config.linux.yaml'])
