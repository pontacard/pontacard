import sqlite3
import datetime
from collections import defaultdict
import pandas as pd
from matplotlib import pyplot as plt
import sqlite3
import numpy as np
from BACKTEST import useful
import talib as ta



class MACD():
    def __init__(self,short_days,long_days,signal_days,code,start_date,end_date,db_file_name):
        self.stock_list = []
        self.short_days = short_days
        self.long_days = long_days
        self.signal_days = signal_days
        self.code = code
        self.start_date = start_date
        self.end_date = end_date
        self.db_file_name = db_file_name

    def ta_macd(self):
        start = self.start_date - datetime.timedelta(days=100)
        prices = useful.get_all_4date(self.db_file_name, start, self.end_date, self.code)

        closes = np.array(prices["close"])

        macd, macd_signal, macd_hist = ta.MACD(closes,self.short_days,self.long_days,self.signal_days)
        prices["MACD"] = macd
        prices["MACD_signal"] = macd_signal
        prices["MACD_hist"] = macd_hist
        #print(prices)
        #print(macd_hist,macd_signal)
        macd= pd.DataFrame(macd)
        macd.index = prices["date"]
        #print(macd)
        macd_hist = pd.DataFrame(macd_hist)
        macd_hist.index = prices["date"]
        macd_signal = pd.DataFrame(macd_signal)
        macd_signal.index = prices["date"]

        return prices

    def MACD_dead(self,code):

        data_list = self.ta_macd()
        #print(data_list)
        dy = np.gradient(data_list["MACD"])  # yの勾配を計算
        print(dy)

        which_above = data_list["MACD"] > data_list["MACD_signal"]
        cross = which_above  != which_above.shift(1)
        dead_cross = cross & (which_above  == False)
        #golden_cross.drop(golden_cross.head(self.long_days).index, inplace=True)
        #dead_cross.drop(dead_cross.head(self.long_days).index, inplace=True)

        #print(data_list[dead_cross])
        #print(data_list.head(60))

        dead_list = data_list[dead_cross]["date"][1:] # 日付のリストに変かん
        #print(dead_list)

        dcodes = [[code]] * len(dead_list)
        dd = dict(zip(dead_list, dcodes))


        return dd




    def generate_cross_date_list(self):
        prices = useful.get_all_4date(self.db_file_name,self.start_date,self.end_date,self.code)


        # ゴールデンクロス・デッドクロスが発生した場所を得る
        #print(prices["date"])
        #print(prices)
        short_EMA = pd.DataFrame(index=prices["date"])
        long_EMA = pd.DataFrame(index=prices["date"])
        signal_EMA = pd.DataFrame(index=prices["date"])
        yes = 0
        yesta = 0
        for i,date in enumerate(prices["date"]):
            k = 2/(self.short_days +1)
            #print(prices[(prices["date"] == date)])
            short_EMA.loc[date] = prices.iat[i,4] * k + yes * (1-k)
            print("ここ",prices.iat[i,4] * k + yes)
            yes = short_EMA.loc[date]

            L  = 2/(self.long_days +1)
            long_EMA.loc[date] = prices.iat[i,4] * L + yesta * (1-L)
            yesta = long_EMA.loc[date]

            g = 2 / (self.signal_days + 1)
            long_EMA.loc[date] = prices.iat[i,4] * g + yesta * (1 - g)
            yesta = signal_EMA.loc[date]

        print(short_EMA)

        dy = np.gradient(short_EMA) # yの勾配を計算
        print(dy)
        # 結果を表示
        print(prices)

        plt.plot(short_EMA, label="EMA11")
        plt.plot(long_EMA, label = "EMA22")
        plt.plot(signal_EMA, label="EMA")
        plt.plot(prices)
        #plt.plot(prices.index, dy, "g-o", label="dy")
        plt.grid()
        plt.legend()
        plt.show()


if __name__ == '__main__':
    start = datetime.datetime(2019, 12, 1)
    end = datetime.datetime(2020, 7, 9)
    startday = datetime.datetime(2020, 2, 1)
    endday = datetime.datetime(2020, 4, 26)
    days = (end - start).days
    code = 6658
    macd = MACD(13,26,9,code,start, end,'/Users/tatsumiryou/sqlite.db')
    macd.MACD_dead(code)