import datetime
import os
import sys
import socket
import json
from os.path import isfile, join
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

def query_shfe(ret: dict, start_time, last_time = None):
	today = datetime.datetime.today().date().strftime('%Y%m%d')
	delta_time = datetime.timedelta(days=1)
	lots_map = {'AU':1000, 'AG':15, 'CU':5, 'AL':5, 'ZN':5, 'RU':10, 'FU':50, 'BU':10, 'RB':10, 'WR':10, 'HC':10, 'PB':5, 'SP':10, 'NI':1, 'SN':1, 'SC':1000}
	if last_time is None:
		last_time = start_time
	while start_time <= last_time:
		cur_day=start_time.strftime('%Y%m%d')
		if start_time.weekday() >= 5:
			start_time = start_time + delta_time
			print ('%s is weekend, ignore'%cur_day)
			continue

		print("send url request on %s"%cur_day)
		request_1 = Request('http://www.shfe.com.cn/data/dailydata/kx/kx%s.dat'%cur_day)
		request_2 = Request('http://www.shfe.com.cn/data/dailydata/ck/%sdailyTimePrice.dat'%cur_day)

		start_time = start_time + delta_time
		def send(req):
			i = 0
			while True:
				try:
					return json.load(urlopen(req, timeout = 30))
				except socket.timeout as e:
					i = i + 1
					if i < 3:
						print ('URL is timeout in %d time, retry it again [error=%s]'%(i, str(e)))
					else:
						raise e
				except HTTPError as e:
					if e.code == 404:
						return None
					else:
						raise e

		json_data = send(request_1)
		if json_data is None:
			print('No Kx data on %s'%cur_day)
			continue

		def t(a):
			if type(a) == str:
				return float(a.strip()) if len(a.strip()) > 0 else 0.0
			return float(a)

		for item in json_data['o_curinstrument']:
			key=item['PRODUCTID'].split('_')[0].upper().strip()
			if key in lots_map:
				lots = lots_map[key]
			else:
				print('No lots found %s, ignore'%key)
				continue

			if key not in ret:
				ret[key]=dict()
			if cur_day not in ret[key]:
				ret[key][cur_day]=list()
			record = dict()
			record['code'] = key.lower() + item['DELIVERYMONTH'].strip()
			record['date'] = cur_day
			record['open'] = t(item['OPENPRICE'])
			record['high'] = t(item['HIGHESTPRICE'])
			record['low'] = t(item['LOWESTPRICE'])
			record['close'] = t(item['CLOSEPRICE'])
			record['settle'] = t(item['SETTLEMENTPRICE'])
			record['volume'] = t(item['VOLUME']) * lots
			record['outstanding'] = t(item['OPENINTEREST']) * lots
			record['turnover'] = record['volume'] * record['settle']
			ret[key][cur_day].append(record)
					
		print("Process on %s is done"%cur_day)
	

def query_dce(ret: dict, start_time, last_time = None):
	today = datetime.datetime.today().date().strftime('%Y%m%d')
	url='http://www.dce.com.cn/publicweb/quotesdata/dayQuotesCh.html'
	delta_time = datetime.timedelta(days=1)
	lots_map = {"C":10,"CS":10,"A":10,"B":10,"M":10,"Y":10,"P":10,"FB":500,"BB":500,"JD":10,"L":5,"V":5,"PP":5,"J":100,"JM":60,"I":100,"EG":10}
	if last_time is None:
		last_time = start_time
	while start_time <= last_time:
		cur_day=start_time.strftime('%Y%m%d')
		if start_time.weekday() >= 5:
			start_time = start_time + delta_time
			print ('%s is weekend, ignore'%cur_day)
			continue
		post_fields={'variety':'all', 'trade_type':'0', 'year':'%d'%start_time.year, 'month':'%d'%(start_time.month-1), 'day':'%d'%start_time.day, 'currDate':'%s'%today}

		print("send url request on %s"%cur_day)
		request = Request(url, urlencode(post_fields).encode())
		i = 0
		while True:
			try:
				response = urlopen(request, timeout = 30).read().decode()
				break;
			except socket.timeout as e:
				i = i + 1
				if i < 3:
					print ('URL is timeout in %d time, retry it again [error=%s]'%(i, str(e)))
				else:
					raise e
		soup = BeautifulSoup(response, features='lxml')
		start_time = start_time + delta_time

		name_map=dict()
		for i in soup.find_all('li', attrs={'class':"keyWord_100"}):
			key = i.text.strip()
			jsp=i.find('input')['onclick']
			i1=jsp.find("'")
			i2=jsp.find("'", i1+1)
			value = jsp[i1+1:i2]
			name_map[key] = value

		if soup.find('span') is None:
			print("No data in %s, ignore"%cur_day)
			continue
		date_str = soup.find('span').text.replace("&"," ")[5:13].strip()

		if cur_day != date_str:
			raise Exception("The page is obsolated, expected day = %s, actual day = %s"%(cur_day, date_str))

		for i in soup.find_all('tr'):
			els = [x.text.strip() for x in i.find_all('td')]
			if len(els) > 0:
				element = ["0" if v == '-' else v for v in els]
				if element[0] in name_map:
					key = name_map[element[0]].upper()
					if key not in ret:
						ret[key]=dict()
					if cur_day not in ret[key]:
						ret[key][cur_day]=list()
					lots = lots_map[key]
					record = dict()
					record['code'] = name_map[element[0]] + element[1]
					record['date'] = cur_day
					record['open'] = float(element[2])
					record['high'] = float(element[3])
					record['low'] = float(element[4])
					record['close'] = float(element[5])
					record['last_settle'] = float(element[6])
					record['settle'] = float(element[7])
					record['volume'] = float(element[10]) * lots
					record['outstanding'] = float(element[11]) * lots
					record['turnover'] = float(element[13]) * 10000
					ret[key][cur_day].append(record)
		print("Process on %s is done"%cur_day)

def generate_daily(short_exch):
	if short_exch == "DCE":
		func = query_dce
	elif short_exch == "SHFE":
		func = query_shfe
	else:
		print("Unknown exchange")
		exit(-1)
	
	print ('start to generate %s data'%short_exch)
	output_dir = join(join(os.environ['MD_DIR'],short_exch), 'daily')
	hist_dir = join(join(os.environ['MD_DIR'],short_exch), 'history')
	if isfile(join(output_dir, '.last')):
		with open(join(output_dir, '.last')) as f:
			start_str = f.readline()
	else:
		with open(join(hist_dir, '.last')) as f:
			start_str = f.readline()
	start_time = (datetime.datetime.strptime(start_str, '%Y%m%d') + datetime.timedelta(days=1)).date()
	content = dict()

	last = start_str
	func(content, start_time, datetime.datetime.today().date())
	for key in content:
		f=open(join(output_dir, '%s_md.csv'%key), 'a')
		for date in sorted(content[key].keys()):
			if len(content[key][date]) > 0:
				rec = max(content[key][date], key = lambda x: x['turnover'])
				f.write('%s,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%s\n'%(rec['date'], rec['open'], rec['high'], rec['low'], rec['close'], rec['volume'], rec['turnover'], rec['outstanding'], rec['code']))
				if last < rec['date']:
					last=rec['date']
		f.close()
	
	with open(join(output_dir, '.last'), 'w') as f:
		f.write(last)
	
	print('Success download daily date for %s from %s to %s'%(short_exch, start_str, last))

generate_daily(sys.argv[1])

