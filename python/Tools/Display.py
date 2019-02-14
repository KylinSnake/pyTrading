import numpy as np
import matplotlib.pyplot as pt
import mpl_finance as finance
import os

class Display:
	def __init__(self, folder, symbol, start = None, last = None, step = None):
		self.folder = folder
		self.symbol = symbol
		self.start = start
		self.last = last
		self.md = None
		self.pos = None
		self.default_step = step
		self.__load_pos__()
		self.__load_mkt__()
		self.ind_map = dict()
		self.formats_map = dict()
		self.default_format = ['b-','g-','r-','c-','m-','y-','k-', 'b--', 'c--', 'k--', 'y--']
		self.__base_param__ = []
		self.__shared_ind_param__ = []
		self.__normal_ind_param__ = []
	
	def __fetch_default_format__(self, name):
		if name not in self.formats_map:
			self.formats_map[name] = 0
		else:
			self.formats_map[name] += 1
		return self.default_format[self.formats_map[name]]
	
	def check_file(self, path):
		if os.path.isfile(path):
			return True
		return False
	
	def __load_mkt__(self):
		mkt_file = os.path.join(self.folder, '%s_md.csv'%self.symbol)

		if not self.check_file(mkt_file):
			raise Exception("Failed to load market data file: %s"%mkt_file)
		mkt_data = np.genfromtxt(mkt_file, encoding='ascii', 
				dtype={'names': ('date', 'open', 'high', 'low', 'close', 'volume'),
				'formats': ('U10', 'f4', 'f4', 'f4', 'f4', 'f4')}, delimiter=',')
		start_index = np.argwhere(mkt_data[:]['date'] == self.pos[0]['date'])[0][0]
		end_index = np.argwhere(mkt_data[:]['date'] == self.pos[-1]['date'])[0][0] + 1
		self.md = mkt_data[start_index : end_index]
	
	def load_indicator(self, ind_name, attrs):
		if ind_name in self.ind_map:
			return True
		ind_file = os.path.join(self.folder, '%s_indicator_%s.csv'%(self.symbol, ind_name))
		if attrs is None or len(attrs) == 0:
			raise Exception('indicator attributes cannot be empty')

		if not self.check_file(ind_file):
			raise Exception("Failed to load indicator file: %s"%ind_file)
		ind_data = np.genfromtxt(ind_file, encoding='ascii', 
				dtype={'names': tuple(['date'] + sorted(attrs)),
				'formats': tuple(['U10'] + ['f4'] * len(attrs))}, delimiter=',', skip_header = 1)
		start_pos_index = np.argwhere(ind_data[:]['date'] == self.pos[0]['date'])[0][0]
		end_pos_index = np.argwhere(ind_data[:]['date'] == self.pos[-1]['date'])[0][0] + 1
		self.ind_map[ind_name] = ind_data[start_pos_index:end_pos_index]
	
	def plot_indicator(self, ax, ind_name, step = None, md_shared = False, line_formats = None, enable_xlabel = True):
		if md_shared:
			self.__shared_ind_param__.append((ax, ind_name, step, line_formats, enable_xlabel))
		else:
			self.__normal_ind_param__.append((ax, ind_name, step, line_formats, enable_xlabel))

	def __plot_indicator__(self, ax, ind_name, step = None, md_shared = False, line_formats = None, enable_xlabel = True):
		ind = self.ind_map[ind_name]
		names = list(ind.dtype.fields.keys())
		names.remove('date')
		if line_formats is None:
			line_formats = dict()
		for i in names:
			if i not in line_formats:
				line_formats[i] = self.__fetch_default_format__(ax)

		cur_step = step
		if cur_step is None:
			cur_step = self.default_step
		if cur_step is None:
			cur_step = int(ind.shape[0]/50)

		if not md_shared:
			ax.grid(True)
			ax.set_xticks(np.arange(0, ind.shape[0], step = cur_step))
			if enable_xlabel:
				ax.set_xticklabels(ind[::cur_step]['date'], rotation = 90, fontsize = 'xx-small')
			else:
				ax.set_xticklabels([])

		for i in names:
			ax.plot(ind[:]['date'], ind[:][i], line_formats[i], label="%s(%s)"%(i, ind_name))

		if not md_shared:
			ax.legend(loc='upper left', shadow=True, fontsize='x-small')
			
	
	def __load_pos__(self):
		pos_file = os.path.join(self.folder, '%s_pos.csv'%self.symbol)
		if not self.check_file(pos_file):
			raise Exception("Failed to load position file: %s"%pos_file)
		mkt_pos = np.genfromtxt(pos_file, encoding='ascii', dtype={'names':('date', 
				'quantity', 'cur_price', 'avg_price', 'stop_price', 'total_amount', 'realized_pnl', 'margin'),
				'formats': ('U10', 'd', 'f4', 'f4', 'f4', 'f4', 'f4','f4')}, delimiter=',')
		if self.start is None:
			self.start = mkt_pos[0]['date']
		elif type(self.start) == int:
			self.start = mkt_pos[self.start]['date']
		elif type(self.start) == str and len(self.start) == 8:
			self.start = '%s-%s-%s'%(self.start[0:4],self.start[4:6],self.start[6:])
		else:
			raise Exception('Wrong format on date %s'%self.start)

		if self.last is None:
			self.last = mkt_pos[-1]['date']
		elif type(self.last) == int:
			self.last = mkt_pos[self.last]['date']
		elif type(self.last) == str and len(self.last) == 8:
			self.last = '%s-%s-%s'%(self.last[0:4],self.last[4:6],self.last[6:])
		else:
			raise Exception('Wrong format on date %s'%self.last)

		assert(self.last>=self.start)

		start_index = np.argwhere(mkt_pos[:]['date'] >= self.start)[0][0]
		end_index = np.argwhere(mkt_pos[:]['date'] <= self.last)[-1][0] + 1

		self.pos = mkt_pos[start_index:end_index]
	
	def display_md(self, ax, step = None, with_pos = True, enable_xlabel = True):
		self.__base_param__.append((ax, step, with_pos, enable_xlabel))
	
	def render(self):
		for (a,b,c,d) in self.__base_param__:
			self.__display_md__(a,b,c,d)
		for (a,b,c,d,e) in self.__normal_ind_param__:
			self.__plot_indicator__(a,b,c,False,d,e)

	def __display_md__(self, ax, step = None, with_pos = True, enable_xlabel = True):
		cur_step = step
		if cur_step is None:
			cur_step = self.default_step
		
		ax.set_title("%s From %s to %s"%(self.symbol, self.md[0]['date'], self.md[-1]['date']))
		ax.set_ylabel('Price')
		ax.grid(True)
		finance.candlestick2_ohlc(ax, self.md[:]['open'], self.md[:]['high'],
							self.md[:]['low'], self.md[:]['close'],
							colorup='r', width=0.4, colordown='g')
		length = self.md.shape[0]
		if cur_step is None:
			cur_step = int(length/50)
		ax.set_xticks(np.arange(0, length, step = cur_step))

		if enable_xlabel:
			ax.set_xticklabels(self.md[::cur_step]['date'], rotation = 90, fontsize = 'xx-small')
		else:
			ax.set_xticklabels([])
		
		ax2 = ax.twinx()
		ax2.fill_between(range(0, self.md.shape[0]), self.md[:]['volume'], alpha=.4, facecolor='#00ffe8')
		ax2.grid(False)
		ax2.set_ylim(0, 3 * max(self.md[:]['volume']))
		ax2.axes.yaxis.set_ticklabels([])

		for (a,b,c,d,e) in self.__shared_ind_param__:
			self.__plot_indicator__(a,b,c,True,d,e)

		label = False
		if with_pos:
			l = list()
			for i in range(0,self.pos.shape[0]):
				if self.pos[i]['quantity'] == 0:
					if len(l) > 0:
						if label is False:
							ax.plot(l, self.pos[l[0]:l[-1]+1]['avg_price'], 'g--', label='Cost Price')
							ax.plot(l, self.pos[l[0]:l[-1]+1]['stop_price'], 'r--', label='Stop Price')
							label = True
						else:
							ax.plot(l, self.pos[l[0]:l[-1]+1]['avg_price'], 'g--')
							ax.plot(l, self.pos[l[0]:l[-1]+1]['stop_price'], 'r--')
						l = list()
				else:
					l.append(i)
		if label or len(self.__shared_ind_param__) > 0:
			ax.legend(loc='upper left', shadow=True, fontsize='x-small')

