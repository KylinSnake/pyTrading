from enum import Enum, unique


@unique
class SecurityType(Enum):
    Unknown = 0
    Future = 1
    Option = 2
    Stock = 3
    Index = 4


class Security:

    def __init__(self):
        self.id: str = None
        self.type: SecurityType = SecurityType.Unknown
        self.lot_size: int = 0
        self.currency: str = None
        self.fx_rate: float = 1.0
        self.trans_cost_multiplier: float = 0.0
        self.trans_cost_fix_amount: float = 0.0
        self.exchange: str = None

    def init_from_token(self, token):
        self.id = token[1]
        self.lot_size = int(token[2])
        self.currency = token[3]
        self.fx_rate = float(token[4])
        self.trans_cost_multiplier = float(token[5])
        self.trans_cost_fix_amount = float(token[6])
        self.exchange = token[7]

    def conversion(self):
        return 1.0


class Future(Security):
    def __init__(self):
        super(Future, self).__init__()
        self.type = SecurityType.Future
        self.conversion_ratio: float = 0.0
        self.init_margin_ratio: float = 0.0
        self.call_margin_ratio: float = 0.0

    def init_from_token(self, token):
        super(Future, self).init_from_token(token)
        self.conversion_ratio = float(token[8])
        self.init_margin_ratio = float(token[9])
        self.call_margin_ratio = float(token[10])

    def conversion(self):
        return self.conversion_ratio


class SecurityCache:
    def __init__(self):
        self.map = dict()

    def get_security(self, sec_id):
        if sec_id in self.map:
            return self.map[sec_id]
        return None

    def insert_security(self, security):
        sec_id = security.id
        if sec_id in self.map:
            return False, self.map[sec_id]
        self.map[sec_id] = security
        return True, security

    def create_security(self, token):
        if token[0] == "F":
            future = Future()
            future.init_from_token(token)
            self.insert_security(future)

    def load_securities_from_file(self, filename):
        with open(filename, 'r') as f:
            for line in f.readlines():
                if line.startswith("#"):
                    continue
                self.create_security(line.strip().split(','))
        return len(self.map) > 0


class SecurityCacheSingleton:
    __instance__: SecurityCache = SecurityCache()

    @staticmethod
    def initialize(file: str, services: dict):
        return SecurityCacheSingleton.get().load_securities_from_file(file)

    @staticmethod
    def get():
        return SecurityCacheSingleton.__instance__

