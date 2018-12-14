from Management import *
from Indicators import *
from Common.Util import logger
import os

def entry_signal(mgr, md):
	pos = mgr.position()
	if pos.quantity != 0:
		return None
	local = mgr.get_local_data()
	if 'stop' in local:
		del local['stop']
	cci = mgr.indicator('CCI_18')
	md_history = mgr.daily_md_until_current_day()
	cur_cci = cci[-1]
	rollback_duration = 18
	dig = None
	if cur_cci > 100.0:
		dig = Diverge(cci, md_high(md_history), False, rollback_duration)
		if dig[0] and dig[1] < 0:
			mgr.add_open_order(Side.Sell)
	elif cur_cci < -100.0:
		dig = Diverge(cci, md_low(md_history), True, rollback_duration)
		if dig[0] and dig[1] > 0:
			mgr.add_open_order(Side.Buy)

def exit_signal(mgr, pos):
	pct = 0.03
	local = mgr.get_local_data()
	last = local['stop'] if 'stop' in local else None
	if pos.quantity == 0:
		return None
	if pos.quantity > 0:
		c_price = pos.current_price * (1 - pct)
		if last is not None:
			price = max(c_price, last)
		else:
			price = c_price
	else:
		c_price = pos.current_price * (1 + pct)
		if last is not None:
			price = min(c_price, last)
		else:
			price = c_price
	local['stop'] = price

	mgr.add_close_order(OrderType.Stop, stop_price = price)


register_strategy('HSIY0', entry_signal, exit_signal)

if os.name == 'nt':
	main(['script','c:\\workstation\\config\\config.dos.yaml'])
else:
	main(['script','../config/config.linux.yaml'])
