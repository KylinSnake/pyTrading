import numpy as np
from matplotlib.dates import strpdate2num, num2date
import datetime
import logging
import yaml, os, re
try:
	from yaml import CLoader as Loader
except ImportError:
	from yaml import Loader

pattern = re.compile( r"^(.*)<%= ENV\['(.*)'\] %>(.*)" )
md_type={'names': ('date', 'open', 'high', 'low', 'close', 'volume'), \
			'formats': ('M8[D]', 'f4', 'f4', 'f4', 'f4', 'f4')}


FORMAT = '%(asctime)-15s %(levelname)-8s %(message)s (%(filename)s: Line %(lineno)d Function: %(funcName)s)'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger(__name__)

__runtime_services_type__ = list()

__services__ = dict()

__runtime_strategy_map__ = dict()

__runtime_md__ = dict()

def register_strategy(secId: str, entry, exit):
	if entry is None or exit is None:
		raise
	__runtime_strategy_map__[secId] = (entry, exit)

def add_runtime_service(service: type):
	__runtime_services_type__.append(service)

def get_app_service(name: str):
	if name in __services__:
		return __services__[name]
	return None

def config_market_data(secId: str, md_file = None, start = None, last = None, indicators: dict = {}):
	if secId not in __runtime_md__:
		__runtime_md__[secId] = {'File':md_file, 'Start':start, 'Last':last, 'Indicators':indicators}
	else:
		if md_file is not None:
			__runtime_md__[secId]['File'] = md_file
		if start is not None:
			__runtime_md__[secId]['Start'] = start
		if last is not None:
			__runtime_md__[secId]['Last'] = last
		if len(indicators.keys()) > 0:
			__runtime_md__[secId]['Indicators'] = indicators

def get_md_override_map():
	return __runtime_md__

def replace_env(value):
	while True:
		g = pattern.match(value)
		if g is None:
			break;
		before, envVar,after = g.groups()
		value = before + os.environ[envVar] + after
	return value

def is_same_month(d1: np.datetime64, d2: np.datetime64):
	c1: datetime.datetime = d1.astype(datetime.datetime)
	c2: datetime.datetime = d2.astype(datetime.datetime)
	return c1.year == c2.year and c1.month == c2.month


def is_same_week(d1: np.datetime64, d2: np.datetime64):
	c1: datetime.datetime = d1.astype(datetime.datetime)
	c2: datetime.datetime = d2.astype(datetime.datetime)
	return c1.isocalendar() == c2.isocalendar()

def normalize_date_str(value):
	if type(value) == int:
		if len(str(value)) == 8:
			value = str(value)
	if type(value) == str:
		if len(value) == 8 and value.isdigit():
			return '%s-%s-%s'%(value[0:4],value[4:6],value[6:8])
		if len(value) == 10 and value[0:4].isdigt() and int(value[5:7]) <= 12 and int(value[8:10]) <= 31:
			return '%s-%s-%s'%(value[0:4],value[5:7],value[8:10])
	return None

def get_md_start_index(d, start_str):
	ret = np.argwhere(md_date(d) >= np.datetime64(start_str))
	if len(ret) > 0:
		return ret[0][0]
	return None

def get_md_last_index(d, last_str):
	ret = np.argwhere(md_date(d) <= np.datetime64(last_str))
	if len(ret) > 0:
		return ret[-1][0]
	return None

def __md_access__(d, attr: str):
	if type(d) == np.ndarray:
		return d[:][attr] if d.shape[0] != 1 else d[0][attr]
	return d[attr]


def md_date(d):
	return __md_access__(d, 'date')


def set_date(d, date):
	d['date'] = date


def md_open(d):
	return __md_access__(d, 'open')


def set_open(d, px: float):
	d['open'] = px


def md_close(d):
	return __md_access__(d, 'close')


def set_close(d, px: float):
	d['close'] = px


def md_high(d):
	return __md_access__(d, 'high')


def set_high(d, px: float):
	d['high'] = px


def md_low(d):
	return __md_access__(d, 'low')


def set_low(d, px: float):
	d['low'] = px


def md_volume(d):
	return __md_access__(d, 'volume')


def set_volume(d, px: float):
	d['volume'] = px

def md_get_accessor(name:str):
	import Util
	return getattr(Util, 'md_' + name)

def md_set_accessor(name:str):
	import Util
	return getattr(Util, 'set_' + name)

def load_market_data_from_file(filename: str):
	return np.genfromtxt(filename, encoding='ascii', skip_header=1,
						 dtype=md_type,
						 delimiter=',',
						 converters={0: lambda x: num2date(strpdate2num('%Y-%m-%d')(x))})


def load_config_from_yaml_file(filename: str):
	f = open(filename, 'r')
	data = ""
	for line in f.readlines():
		l = replace_env(line.strip('\n'))
		data += l+'\n'
	print("\n***** Load YAML config file as following *****\n")
	print(data)
	print("**********************************************")
	ret = yaml.load(data, Loader=Loader)
	return ret;

