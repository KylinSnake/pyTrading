from Signals.ExitSignal import *
from Indicators import *


class DMI_SAR_Entry_V1(EntrySignal):
    def __init__(self, mkt, pdi, ndi, adx, sar, direction):
        super(DMI_SAR_Entry_V1, self).__init__(mkt)
        self.pdi = pdi
        self.ndi = ndi
        self.adx = adx
        self.sar = sar
        self.direction = direction

    def entry_signal(self):
        if self.adx[self.current_day] > self.adx[self.current_day - 1]:
            if self.pdi[self.current_day] > self.ndi[self.current_day] and self.direction[self.current_day]:
                return SignalType.BuyOpen
            elif self.pdi[self.current_day] < self.ndi[self.current_day] and not self.direction[self.current_day]:
                return SignalType.SellOpen
        return SignalType.NoAction


class DMI_SAR_Exit_V1(StopExitSignal):
        def __init__(self, mkt, open_signal, open_price, pdi, ndi, adx, sar):
            super(DMI_SAR_Exit_V1, self).__init__(mkt, open_signal, open_price, sar)
            self.pdi = pdi
            self.ndi = ndi
            self.adx = adx

        def signal(self):
            if self.adx[self.current_day] < self.adx[self.current_day - 1]:
                if self.adx[self.current_day] > max(self.ndi[self.current_day], self.pdi[self.current_day]):
                    return SignalType.Stop
            return super(DMI_SAR_Exit_V1, self).signal()


class CCI_Diverge_Entry_V1(EntrySignal):
    def __init__(self, mkt, cci, roll_back_duration):
        super(CCI_Diverge_Entry_V1, self).__init__(mkt)
        self.cci = cci
        self.roll_back_duration = roll_back_duration

    def entry_signal(self):
        sig = SignalType.NoAction
        start = self.current_day - self.roll_back_duration
        end = self.current_day
        cci_v = self.cci[end]
        if cci_v > 100:
            dig = Diverge(self.cci[start:end], self.market_data['high'][start:end], False)
            if dig[0] and dig[1] == -1:
                sig = SignalType.SellOpen
        elif cci_v < -100:
            dig = Diverge(self.cci[start:end], self.market_data['low'][start:end],True)
            if dig[0] and dig[1] == 1:
                sig = SignalType.BuyOpen
        return sig
