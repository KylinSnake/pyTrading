from Management.Util import *


class MDReplayer:
    def __init__(self, md: np.ndarray, sec_id: str, start_index: int):
        self.sec_id = sec_id
        self.daily_md = md
        self.init_start = start_index
        self.daily_current = self.init_start
        self.monthly_md = np.empty(self.daily_md.shape, self.daily_md.dtype)
        self.weekly_md = np.empty(self.daily_md.shape, self.daily_md.dtype)
        self.monthly_md[0] = self.daily_md[0]
        self.weekly_md[0] = self.daily_md[0]
        self.monthly_current = 0
        self.weekly_current = 0
        self.accumulate_monthly_md(0, self.daily_current)
        self.accumulate_weekly_md(0, self.daily_current)

    def get_monthly_md_until_current(self):
        return self.monthly_md[:self.monthly_current + 1]

    def get_weekly_md_until_current(self):
        return self.weekly_md[:self.weekly_current + 1]

    def has_next_day(self):
        return self.daily_current < self.daily_md.shape[0]

    def peak_current_date(self):
        if self.has_next_day():
            return md_date(self.daily_md[self.daily_current])
        return None

    def pop_current_and_move_next(self):
        if self.has_next_day():
            ret = self.daily_md[self.daily_current]
            self.accumulate_weekly_md(self.daily_current, self.daily_current + 1)
            self.accumulate_monthly_md(self.daily_current, self.daily_current + 1)
            self.daily_current += 1
            return ret
        return None

    def accumulate_weekly_md(self, begin: int, end: int):
        self.weekly_current = self.calculate_duration_md_until_current(
            self.weekly_md, begin, end, self.weekly_current, is_same_week
        )

    def accumulate_monthly_md(self, begin: int, end: int):
        self.monthly_current = self.calculate_duration_md_until_current(
            self.monthly_md, begin, end, self.monthly_current, is_same_month
        )

    def calculate_duration_md_until_current(self, ret: np.ndarray, daily_begin: int,
                                            daily_end: int, output_begin: int, func):
        for i in range(daily_begin, daily_end):
            daily = self.daily_md[i]
            output = ret[output_begin]
            if func(md_date(daily), md_date(output)):
                set_close(output, md_close(daily))
                if md_high(daily) > md_high(output):
                    set_high(output, md_high(daily))
                if md_low(daily) < md_low(output):
                    set_low(output, md_low(daily))
            else:
                output_begin += 1
                ret[output_begin] = daily
        return output_begin


class MarketDataManager:
    @staticmethod
    def initialize(config: dict, services: dict):
        name = config['name'] if config is not None and 'name' in config else 'MarketDataManager'
        md = config['MarketData']
        ind = config['Indicator']
        services[name] = MarketDataManager(md, ind)
        return True

    def __init__(self, md: dict, ind: dict):
        self.md_list = []
        self.listeners = []
        for item in md:
            sec_id = str(item["SecId"])
            file_path = item["File"]
            start = int(item["Start"]) if "Start" in item else 100
            self.md_list.append(MDReplayer(load_market_data_from_file(file_path),
                                           sec_id, start))

    def subscribe(self, f):
        self.listeners.append(f)

    def notify(self, msg: dict):
        for f in self.listeners:
            f(msg)

    def run(self):
        while True:
            dates = [x.peak_current_date() for x in self.md_list if x.has_next_day()]
            if len(dates) == 0:
                break
            min_date = min(dates)
            msg = dict()
            for x in self.md_list:
                if x.peak_current_date() == min_date:
                    msg[x.sec_id] = x.pop_current_and_move_next()
            self.notify(msg)




