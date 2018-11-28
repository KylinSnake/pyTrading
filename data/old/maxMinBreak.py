# -*- coding: utf-8 -*-
"""
Created on Sun Aug 27 00:15:50 2017

@author: Roy
"""

import numpy as ny
import matplotlib.pyplot as plt
import matplotlib.finance as finance


min_data = ny.genfromtxt('C:\workstation\data\AU1712_0825_1min.csv', comments='#', dtype=None
            ,delimiter=',', names=True)
tick_data = ny.genfromtxt('C:\workstation\data\AU1712_0825_tick.csv', comments='#', dtype=None
            ,delimiter=',', names=True)
fig=plt.figure()
ax1=fig.add_subplot('111')
#ax2=fig.add_subplot('211')
N=10
'''
ax1.grid(True)
finance.candlestick2_ohlc(ax1,min_data[:]['open'],min_data[:]['high']
        ,min_data[:]['low'],min_data[:]['close'],colorup='r',width=0.4,colordown='g')
        

max_num=[ny.max(min_data[max(x-N,0):x]['high']) for x in range(1,min_data.shape[0])]
min_num=[ny.min(min_data[max(x-N,0):x]['close']) for x in range(1,min_data.shape[0])]
min_num.insert(0, min_data[0]['low'])
max_num.insert(0, min_data[0]['high'])
ax2.plot(max_num)
ax2.plot(min_num)
'''

ax1.grid(True)
ax2.grid(True)
ax1.plot(tick_data[:]['last'])
ax1.scatter(range(0, tick_data.shape[0]), tick_data[:]['ask'], color='r')
ax1.scatter(range(0, tick_data.shape[0]), tick_data[:]['bid'], color='g')
#ax2.plot(tick_data[:]['ask'] - tick_data[:]['bid'] , color='b')
#ax2.plot(tick_data[:]['asize1'], color='r')
#ax2.plot(tick_data[:]['bsize1'], color='g')
plt.show()
