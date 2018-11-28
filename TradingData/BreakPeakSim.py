from Indicators import *
from Signals import *
from Simulator import *
import matplotlib.pyplot as plt
import mpl_finance as finance


filename = "C:\\workstation\\data\\HSIY0 history.csv"

sim = Simulator()
sim.load_market_data(filename)
mkt_data = sim.market_data
sim.add_indicator("10D_high", maximum_past_days_with_today(
    mkt_data['high'], 10))
sim.add_indicator("10D_low", minimum_past_days_with_today(
    mkt_data['low'], 10))
sim.add_indicator("TR", TR(mkt_data[:]['high'], mkt_data[:]['low'], mkt_data[:]['close']))
sim.add_indicator("14D_ATR", EMA(sim.indicators['TR'], 14))
sim.add_indicator("7D_ATR", EMA(sim.indicators['TR'], 7))
sim.add_indicator("18D_DMI", DMI(mkt_data[:]['high'], mkt_data[:]['low'], mkt_data[:]['close'], 18))
sim.add_indicator("SAR", SAR(mkt_data[:]['high'], mkt_data[:]['low']))
sim.add_indicator("18D_CCI", CCI(mkt_data[:]['high'], mkt_data[:]['low'], mkt_data[:]['close'], 18))


def entry_signal_gen(mkt, ind):
    cci = ind['18D_CCI']
    return CCI_Diverge_Entry_V1(mkt, cci, 18)

def exit_signal_gen(mkt, ind, sig, price, entry):
    #(pdi, ndi, adx) = ind['18D_DMI']
    (sar, direction) = ind['SAR']
    #return DMI_SAR_Exit_V1(mkt, sig, price, pdi, ndi, adx, sar)
    return FixPercentageExitSignal(mkt, sig, price, 0.03)


sim.entry_signal_generator = entry_signal_gen
sim.exit_signal_generator = exit_signal_gen


def show(result, mkt, ind, ax, ax2, ax3, step = 10):
    start = result.start
    end = result.end

    (pdi, ndi, adx) = ind['18D_DMI']
    ax2.plot(np.arange(0, end - start), pdi[start:end], 'r-')
    ax2.plot(np.arange(0, end - start), ndi[start:end], 'g-')
    ax2.plot(np.arange(0, end - start), adx[start:end], 'b-')
    ax2.grid(True)
    ax2.set_xticks(np.arange(0, end - start, step=step))
    ax2.set_xticklabels(mkt[start:end:step]['date'], rotation=45)

    cci = ind["18D_CCI"]
    ax3.plot(np.arange(0, end - start), cci[start:end], 'r-')
    ax3.plot(np.arange(0, end - start), np.full(end-start, 100), 'g--')
    ax3.plot(np.arange(0, end - start), np.full(end-start, -100), 'b--')
    ax3.grid(True)

    ax3.set_xticks(np.arange(0, end - start, step=step))
    ax3.set_xticklabels(mkt[start:end:step]['date'], rotation=45)

    ax.grid(True)
    ax.set_xticks(np.arange(0, end - start, step=step))
    ax.set_xticklabels(mkt[start:end:step]['date'], rotation=45)
    (sar, direction) = ind["SAR"]
    '''for i in range(start, end):
        if direction[i] == direction[i+1]:
            ax.plot(np.array([i-start, i-start + 1]), sar[i:i+2], 'b-')
        elif direction[i] != direction[i-1]:
            ax.plot(np.array([i-start]), np.array([sar[i]]), 'b-')'''

    trades = result.trades
    for i in range(0, int(len(trades)/2)):
        price = trades[i*2][0]
        dates = np.array([trades[i*2][2], trades[i*2+1][2]])
        ax.plot(dates - result.start, np.full(2, price), 'g-')
    for stop_list in result.stops:
        stop_points = np.array(stop_list)
        ax.plot(stop_points[:, 0] - result.start, stop_points[:,1], 'r-')
    finance.candlestick2_ohlc(ax, mkt[start:end]['open'], mkt[start:end]['high'],
                              mkt[start:end]['low'], mkt[start:end]['close'],
                              colorup='r', width=0.4, colordown='g')


def test():
    sim.run()
    for result in sim.simulation_results:
        trades = result.trades
        start = result.start
        total_profit = 0
        for i in range(0, int(len(trades) / 2)):
            open_price = trades[i * 2][0]
            close_price = trades[i * 2 + 1][0]
            qty = trades[i * 2][1]
            begin = trades[i * 2][2]
            end = trades[i * 2 + 1][2]
            init_stop = result.stops[i][0][1]
            profit = (close_price-open_price)*qty
            r = abs(open_price - init_stop)
            total_profit += profit
            out_str = 'Date=%s-%s, Open=%.2f, Close=%.2f, Qty=%.1f, InitStop=%.2f, Profit=%.2f, R=%.4f, PR=%.4f'%(
                mkt_data[int(begin)]['date'],
                mkt_data[int(end)]['date'], open_price, close_price, qty, init_stop, profit, r, profit/r)
            #print (out_str)
        print ("profit is %.2f"%total_profit)


    fig = plt.figure(figsize=(20, 15), dpi=80)
    show(sim.simulation_results[0], mkt_data, sim.indicators, fig.add_subplot(3, 1, 1), fig.add_subplot(3, 1, 2), fig.add_subplot(3, 1, 3), 5)

    plt.show()


'''sim.append_simulation_range(100, 350)
sim.append_simulation_range(350, 600)'''
sim.append_simulation_range(600, 850)
'''sim.append_simulation_range(850, 1100)
sim.append_simulation_range(100, 1100)'''


if __name__ == "__main__":
    test()