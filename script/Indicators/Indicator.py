from Common import *


def SMA(darray, n):
	ret = np.full(darray.shape, 0.0)
	for i in range(n, darray.shape[0]):
		ret[i] = np.average(darray[i-n:i])
	return ret

def EMA(darray, n):
	ret = darray.copy()
	f = 2.0 / (n+1)
	f1 = 1.0 - f
	for i in range(1, darray.shape[0]):
		ret[i] = ret[i-1] * f1 + darray[i] * f
	return ret


def TR(high, low, close):
	m = np.roll(close, 1)
	m[0] = close[0]
	return np.fmax(high, m) - np.fmin(low, m)


def DM(high, low):
	assert high.shape == low.shape
	yest_high = np.roll(high, 1)
	yest_low = np.roll(low, 1)
	zeroes = np.zeros(high.shape[0])
	pdm = np.maximum(high - yest_high, zeroes)
	ndm = np.maximum(yest_low - low, zeroes)

	pdm[0] = 0.0
	ndm[0] = 0.0
	for i in range(1, pdm.shape[0]):
		if pdm[i] > ndm[i]:
			ndm[i] = 0.0
		else:
			pdm[i] = 0.0

	return pdm, ndm


def DI(tr, n, pdm, ndm):
	tr_n = EMA(tr, n)
	pdi = None
	ndi = None
	if pdm is not None:
		pdi = EMA(pdm, n) / tr_n
	if ndm is not None:
		ndi = EMA(ndm, n) / tr_n
	return pdi, ndi


# return +DI, -DI, ADX
def DMI(high, low, close, adx_smoothing, di_length):
	(pdm, ndm) = DM(high, low)
	tr = TR(high, low, close)
	(pdi, ndi) = DI(tr, di_length, pdm, ndm)
	total = pdi + ndi
	return pdi * 100, ndi * 100, EMA(np.divide(np.abs(pdi - ndi),  total, where=total != 0.0), adx_smoothing)*100


def value_of_past_days_with_today(data, n, func):
	ret = np.full(data.shape[0], np.NAN)
	for i in range(n - 1, ret.shape[0]):
		ret[i] = func(data[i - n + 1: i + 1])
	return ret


def maximum_past_days_with_today(data, n):
	return value_of_past_days_with_today(data, n, np.amax)


def minimum_past_days_with_today(data, n):
	return value_of_past_days_with_today(data, n, np.amin)


def SAR(high, low, af_init=0.02, af_cap=0.20, af_step=0.02):
	assert len(high) == len(low)
	ret = np.full(high.shape, np.NAN)
	direction = np.full(high.shape, False)
	ret[0] = high[0]
	af = af_init
	is_down_trend = True
	for i in range(1, len(ret)):
		ep = high[i] if is_down_trend else low[i]
		ret[i] = ret[i-1] + af * (ep - ret[i-1])
		direction[i] = not is_down_trend
		if is_down_trend:
			if ret[i] < high[i-1] or ret[i] < high[i-2]:
				ret[i] = max(high[i-1], high[i-2])
		else:
			if ret[i] > low[i-1] or ret[i] > low[i-2]:
				ret[i] = min(low[i-1], low[i-2])
		if (is_down_trend and ret[i] < high[i]) or (is_down_trend is False and ret[i] > low[i]):
			is_down_trend = not is_down_trend
			af = af_init
		else:
			af = min(af_cap, af + af_step)
	return ret, direction


def CCI(high, low, close, n):
	p = (high + low + close) / 3
	sma = SMA(p, n)
	md = p.copy()
	for i in range(n, p.shape[0]):
		md[i] = np.average(np.abs(p[i-n: i] - np.full(n, sma[i])))
	return (p - sma)/(0.015 * md)


def sign(n):
	return abs(n) / n if n != 0.0 else 0


def Diverge(indicator, price, is_lowest_extreme, n):
	def is_extreme(seq, j):
		if is_lowest_extreme:
			return seq[j] < seq[j-1] and seq[j] < seq[j+1]
		return seq[j] > seq[j-1] and seq[j] > seq[j+1]
	v1 = None
	v2 = None
	for i in range(1, n-1):
		if is_extreme(indicator, n-i-1):
			if v1 is None:
				v1 = -i
			elif v2 is None:
				v2 = -i
		if v1 is not None and v2 is not None:
			break

	if v1 is None or v2 is None:
		return False, None, None

	(a, b) = (sign(indicator[v1]-indicator[v2]), sign(price[v1] - price[v2]))
	return a*b < 0, a, b

def generate_indicator(md: np.ndarray, indicator_type: str, parameters):
	def get_with_default(param: dict, key: str, default_value):
		if key in param:
			return (type(default_value))(param[key])
		return default_value

	if indicator_type == 'CCI':
		n = int(parameters)
		return CCI(md_high(md), md_low(md), md_close(md), n)

	if indicator_type == 'SAR':
		af_init = get_with_default(parameters, 'Init', 0.02)
		af_cap = get_with_default(parameters, 'Cap', 0.20)
		af_step = get_with_default(parameters, 'Step', 0.02)
		return SAR(md_high(md), md_low(md), af_init, af_cap, af_step)
	
	if indicator_type == 'DMI':
		di_length = 14
		adx_smoothing = 14
		if parameters is not None and parameters != "":
			di_length = get_with_default(parameters, 'DI Length', 14)
			adx_smoothing = get_with_default(parameters, 'ADX Smooth', 14)
		(pdi, ndi, adx) = DMI(md_high(md), md_low(md), md_low(md), adx_smoothing, di_length)
		return { '+DI':pdi, '-DI':ndi, 'ADX':adx }
	
	if indicator_type == 'SMA' or indicator_type == 'EMA':
		func = SMA if indicator == 'SMA' else EMA
		price_attr = str(parameters['MDAttribute']).lower()
		n = int(parameters['Days'])
		return func(md_get_accessor(price_attr)(md), n)
	
	if indicator_type == 'TR':
		return TR(md_high(md), md_low(md), md_close(md))
	
	raise ValueError('No indicator type found: %s'%indicator_type)
