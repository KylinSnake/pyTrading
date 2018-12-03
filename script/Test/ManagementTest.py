import unittest
from Management import *


class ManagementTest(unittest.TestCase):
	def setUp(self):
		security_str_list = [
			'F,HSI,1,HKD,0.87,0.0001,0.0,HKEX,50.0,0.12,0.07',
			'F,IF01,1,RMB,1.0,0.0003,0.0,SHEX,300.0,0.25,0.12'
		]
		for sec in security_str_list:
			SecurityCacheSingleton.get().create_security(sec.split(','))

	def test_Security(self):
		mgr = SecurityCacheSingleton.get()
		self.assertEqual(len(mgr.map), 2)
		self.assertTrue("HSI" in mgr.map)
		self.assertTrue("IF01" in mgr.map)
		sec: Future = mgr.get_security("HSI")
		self.assertEqual(sec.id, "HSI")
		self.assertEqual(sec.fx_rate, 0.87)
		self.assertEqual(sec.conversion(), sec.conversion_ratio)
		self.assertEqual(sec.conversion_ratio, 50)
		self.assertEqual(sec.init_margin_ratio, 0.12)
		self.assertEqual(sec.currency, "HKD")
		self.assertEqual(sec.exchange, "HKEX")
		self.assertEqual(sec.type, SecurityType.Future)
		self.assertEqual(sec.call_margin_ratio, 0.07)
		self.assertEqual(sec.trans_cost_multiplier, 0.0001)
		self.assertEqual(sec.lot_size, 1)
		self.assertTrue(mgr.get_security("TEST") is None)

	def test_Trade_Position_Risk(self):
		init_cash: float = 3000.0 * 1000.0
		tr_mgr = TradeManager()
		margin_pos_mgr = PositionManager(tr_mgr, init_cash)
		mgr = SecurityCacheSingleton.get()
		margin_risk_mgr: FixPctRiskManager = FixPctRiskManager(margin_pos_mgr, {'RiskPercentage': 2})
		sec: Future = mgr.get_security("HSI")

		self.assertEqual(len(tr_mgr.listeners), 1)
		self.assertEqual(margin_pos_mgr.get_status(), PositionStatus(init_cash, init_cash, 0.0, 0.0))

		margin_quote = margin_risk_mgr.get_open_quantity('HSI', True, 25000, 25000 * 0.98)
		self.assertEqual(margin_quote, int((margin_risk_mgr.pct * init_cash)
										   / (0.02 * 25000 * sec.conversion() * sec.fx_rate)))
		self.assertGreaterEqual(margin_quote, 2)
		tr_mgr.add_trade("20180702", "HSI", 2, 25000)

		self.assertEqual(len(tr_mgr.trades), 1)
		trades = tr_mgr.trades['HSI']
		self.assertEqual(len(trades), 1)
		trade: Trade = trades[0]
		trans_cost = 2*25000.0*sec.trans_cost_multiplier * sec.conversion()
		self.assertEqual(trade.trans_cost, trans_cost)

		self.assertEqual(len(margin_pos_mgr.positions), 1)
		pos: Position = margin_pos_mgr.positions['HSI']
		self.assertEqual(pos.total_amount, 2*25000*sec.conversion()*sec.fx_rate)
		init_cash -= trans_cost * sec.fx_rate
		init_cash -= pos.margin

		self.assertEqual(margin_pos_mgr.get_status(),
						PositionStatus(init_cash + pos.margin, init_cash, 0.0, 0.0))
		self.assertEqual(pos.margin, abs(pos.total_amount) * sec.init_margin_ratio)

		old_margin_pos = copy.copy(pos)
		margin_pos_mgr.on_close_price('20180707', {'HSI': 25500})
		u_pnl = 25500 * sec.fx_rate * pos.quantity * sec.conversion() - pos.total_amount
		init_cash += (old_margin_pos.margin - pos.margin)
		self.assertEqual(pos.margin - float(pos.total_amount) * sec.call_margin_ratio < 0.0000001, True)
		self.assertEqual(margin_pos_mgr.get_status(),
						 PositionStatus(init_cash + pos.margin + u_pnl, init_cash,
						  0.0, u_pnl))
		self.assertEqual(pos.last_update_date, '20180707')

		old_margin_pos = copy.copy(pos)
		tr_mgr.add_trade("20180708", "HSI", -1, 26000)

		self.assertEqual(len(tr_mgr.trades), 1)
		trades = tr_mgr.trades['HSI']
		self.assertEqual(len(trades), 2)
		trade: Trade = trades[1]
		trans_cost = 1 * 26000.0 * sec.trans_cost_multiplier * sec.conversion()
		self.assertEqual(trade.trans_cost, trans_cost)

		amount = old_margin_pos.total_amount * 1 / 2
		init_cash -= trans_cost * sec.fx_rate
		init_cash += (old_margin_pos.margin - pos.margin)
		r_pnl = (26000 - 25000) * 1 * sec.fx_rate * sec.conversion()
		init_cash += r_pnl

		self.assertEqual(len(margin_pos_mgr.positions), 1)
		self.assertEqual(pos.quantity, 1)
		self.assertEqual(pos.current_price, 26000.0)
		self.assertEqual(pos.last_update_date, '20180708')
		self.assertEqual(pos.total_amount, amount)
		self.assertEqual(pos.margin, old_margin_pos.margin * 1 / 2)
		self.assertEqual(pos.realized_pnl, r_pnl)
		u_pnl = pos.current_price * pos.quantity * sec.conversion() * sec.fx_rate - pos.total_amount
		self.assertEqual(margin_pos_mgr.get_status(),
						 PositionStatus(init_cash + pos.margin + u_pnl, init_cash, r_pnl, u_pnl))

		old_margin_pos = copy.copy(pos)
		tr_mgr.add_trade("20180710", "HSI", -2, 25800)

		self.assertEqual(len(trades), 3)
		trade: Trade = trades[2]
		init_cash -= trade.trans_cost * sec.fx_rate
		init_cash += (old_margin_pos.margin - pos.margin)
		profit = pos.current_price * old_margin_pos.quantity * sec.conversion() * sec.fx_rate - old_margin_pos.total_amount
		r_pnl += profit
		init_cash += profit
		u_pnl = 0.0
		self.assertEqual(margin_pos_mgr.get_status(),
						 PositionStatus(init_cash + u_pnl + pos.margin, init_cash, r_pnl, u_pnl))

		self.assertEqual(pos.quantity, -1)
		self.assertEqual(pos.current_price, 25800)
		self.assertEqual(pos.total_amount, 25800 * -1 * sec.fx_rate * sec.conversion())
		self.assertEqual(pos.last_update_date, '20180710')
		self.assertEqual(pos.margin, pos.current_price * abs(pos.quantity) * sec.conversion() * sec.fx_rate
						 * sec.call_margin_ratio)

		old_margin_pos = copy.copy(pos)
		tr_mgr.add_trade("20180711", "HSI", 1, 26200)

		self.assertEqual(len(trades), 4)
		trade: Trade = trades[3]
		self.assertEqual(pos.quantity, 0)
		init_cash -= trade.trans_cost * sec.fx_rate
		
		profit = (pos.current_price * old_margin_pos.quantity * sec.conversion() * sec.fx_rate - old_margin_pos.total_amount)
		r_pnl += profit
		init_cash += profit
		init_cash += old_margin_pos.margin
		self.assertEqual(margin_pos_mgr.get_status(),
						 PositionStatus(init_cash, init_cash, r_pnl, 0.0))

		self.assertEqual(pos.total_amount, 0.0)
		self.assertEqual(pos.current_price, 26200)
		self.assertEqual(pos.last_update_date, '20180711')
		self.assertEqual(pos.margin, 0.0)


if __name__ == '__main__':
	unittest.main()
