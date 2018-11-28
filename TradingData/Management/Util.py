import numpy as np
from matplotlib.dates import strpdate2num, num2date
import datetime
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


def is_same_month(d1: np.datetime64, d2: np.datetime64):
    c1: datetime.datetime = d1.astype(datetime.datetime)
    c2: datetime.datetime = d2.astype(datetime.datetime)
    return c1.year == c2.year and c1.month == c2.month


def is_same_week(d1: np.datetime64, d2: np.datetime64):
    c1: datetime.datetime = d1.astype(datetime.datetime)
    c2: datetime.datetime = d2.astype(datetime.datetime)
    return c1.isocalendar() == c2.isocalendar()

def __md_access__(d, attr: str):
    if type(d) == np.ndarray:
        return d[:][attr]
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


def load_market_data_from_file(filename: str):
    return np.genfromtxt(filename, encoding='ascii', skip_header=1,
                         dtype={'names': ('date', 'open', 'high', 'low', 'close', 'volume'),
                                'formats': ('M8[D]', 'f4', 'f4', 'f4', 'f4', 'f4')},
                         delimiter=',',
                         converters={0: lambda x: num2date(strpdate2num('%Y-%m-%d')(x))})


def load_config_from_yaml_file(filename: str):
    return load(open(filename), Loader=Loader)
