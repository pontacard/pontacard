import pandas as pd
import numpy  as np
import datetime
import seaborn
import sqlite3
import matplotlib.pyplot as plt
from scipy.stats import linregress
import cmath
from BACKTEST.grad_macd import Lgrad
from BACKTEST.trend_stra import trend
from BACKTEST.make_macd import MACD


class Regi_Macd():
    def __init__(self,today,code,watch_len,day_sum_rate,high_grad,low_grad,short_days,long_days,signal_days,above_arg,under_arg,alpha):
        self.watch_len = watch_len
        self.sec_4data = pd.DataFrame()
        self.day_sum_rate = day_sum_rate  # 傾きの合計がwatch_lenにこれを掛けた数を超えたらシグナル
        self.high_grad = high_grad  # これより傾きが小さい高音のラインだけをひく
        self.low_grad = low_grad
        self.short_days = short_days
        self.long_days = long_days
        self.signal_days = signal_days
        self.under_arg = under_arg
        self.above_arg = above_arg  # レンジ相場か確かめるためのパラメーター、この二つの角度が狭いほど、買いシグナルが絞られる。
        self.alpha = alpha  # これが小さいほど、売りシグナルがよく出る(macd_histの変化率が減った時に、前日のmacd_histがこれの定数倍以上だったらシグナル)
        self.code = code
        self.today = today


    def breaklist(self,result):
        diff = datetime.timedelta(days= self.watch_len)
        #print(type(self.today))
        before = self.today - diff


        Lgrads = Lgrad('/Users/tatsumiryou/sqlite.db',self.code,before,self.today,self.watch_len,self.day_sum_rate,self.high_grad,self.low_grad,self.short_days,self.long_days,self.signal_days,self.above_arg,self.under_arg,self.alpha)
        #to64day = pd.to_datetime(today)
        #be64fore = pd.to_datetime(before)
        #print(to64day)
        Lgrads.sec_4data = Lgrads.get_all_4date(before, self.today, self.code)
        try:
            sup = Lgrads.creat_break_point_list(before,self.today,self.code)
        except IndexError:
            return result
        try:
            a = sup[0][self.today]
            print(0)
            result.loc[self.code, 'upper_power'] += 10
        except KeyError:
            pass
        #print(result)

        return result

    def MACD_hist(self,result):
        diff = datetime.timedelta(days=self.watch_len)
        # print(type(self.today))
        before = self.today - diff
        mac = MACD(self.short_days, self.long_days, self.signal_days, self.code, before, self.today,
                   '/Users/tatsumiryou/sqlite.db')
        data_list = mac.ta_macd()
        sell = {}
        buy_list =[]
        #print(data_list)
        dy1 = np.gradient(data_list["MACD_hist"])
        data_list["hist_grad"] = dy1



        hist = data_list.query(f"date <= @self.today")
        hist = hist.query(f"date >= @before")
        histup = data_list[data_list["MACD_hist"] > 0]["MACD_hist"]  # 過去60日のhistが０より大きいところ
        #print(hist)
        #print(histup)
        top5 = histup.quantile(0.95)
        #print(data_list)
        try:
            if data_list.iloc[-1]["hist_grad"] < 0 and data_list.iloc[-2]["MACD_hist"] > self.alpha * top5:
                result.loc[self.code, 'down_power'] += 10
        except IndexError:
                pass

        return result





if __name__ == '__main__':
    today = datetime.date.today()
    today = datetime.date(2022, 1, 4)
    code = 4966
    cla = Regi_Macd(today,code,100,1.8,10,-10,12,26,9,359,2,1)
    #cla.sec_4data = cla.get_all_4date(start,end,code)
    #cla.creat_break_point_list(startday,endday,code)
    #cla.breaklist()
    cla.MACD_hist(pd.DataFrame(index=[code], columns=["upper_power", "down_power", "registance_power"]))
