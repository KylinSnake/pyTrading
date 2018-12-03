from Management import *
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
				output.append(str(self.md_svc.get_current_indicator(Id, 'HSI_CCI_14')[-1]))
			elif Id == 'IF0001':
				ind = self.md_svc.get_current_indicator(Id, 'IF0001_DMI_14')
				output += [str(ind['+DI'][-1]), str(ind['-DI'][-1]), str(ind['ADX'][-1])]
			self.files[Id].write(','.join(output) + '\n')

Main.runtime_services_type.append(DataOutputTest)

if __name__ == '__main__':
	if os.name == 'nt':
		main(['script','c:\\workstation\\config\\config.dos.yaml'])
	else:
		main(['script','../config/config.linux.yaml'])
