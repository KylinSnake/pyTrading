from Common import *
from Management.MarketData import *
from Management.Risk import *
from Management.Strategy import *
from Management.Order import *
from Management.Strategy import *

creators = {
	'SecurityCache': SecurityCacheSingleton.initialize,
	'TradeManager': TradeManager.initialize,
	'RiskManager': RiskManager.initialize,
	'MarketDataManager': MarketDataManager.initialize,
	'PositionManager': PositionManager.initialize,
	'OrderManager': OrderManager.initialize,
	'StrategyManager': StrategyManager.initialize
}

__runtime_services_type__ = list()

__services__ = dict()

__runtime_strategy_map__ = dict()

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

def main(argv: list):
	if len(argv) != 2:
		print("%s <yaml file>" % argv[0])
		return False
	config = load_config_from_yaml_file(argv[1])
	for key in config:
		if key in creators:
			if not creators[key](config[key], __services__):
				print("Failed to create %s" % key)
				return False
	#Add runtime servers
	for runtime_type in __runtime_services_type__:
		svc = runtime_type(__services__)
		__services__[svc.name()] = svc
	
	#Add strategy
	strategy_mgr = __services__['StrategyManager']
	for secId in __runtime_strategy_map__:
		(w,v) = __runtime_strategy_map__[secId]
		strategy_mgr.set_signal(secId, w, v)

	#MD trigger running
	get_app_service('MarketDataManager').run()

	return True

