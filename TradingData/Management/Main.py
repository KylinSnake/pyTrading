from Management.MarketData import *
from Management.Risk import *

creators = {
    'SecurityCache': SecurityCacheSingleton.initialize,
    'TradeManager': TradeManager.initialize,
    'RiskManager': RiskManager.initialize,
    'MarketDataManager': MarketDataManager.initialize,
    'PositionManager': PositionManager.initialize
}


def main(argv: list):
    if len(argv) != 2:
        print("%s <yaml file>" % argv[0])
        return False
    config = load_config_from_yaml_file(argv[1])
    services = dict()
    for key in config:
        if key in creators:
            if not creators[key](config[key], services):
                print("Failed to create %s" % key)
                return False

    return True


if __name__ == '__main__':
    main(['script','c:\\workstation\\data\\config.yaml'])