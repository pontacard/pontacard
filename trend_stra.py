import pandas as pd
import numpy  as np
import datetime
import seaborn
import sqlite3
import matplotlib.pyplot as plt
from scipy.stats import linregress
from  BACKTEST import myportfolio as sim
import time
from  BACKTEST import useful
import cmath

# 投資分析にのみ必要なモジュール
import mplfinance.original_flavor as mpf

# For suppressing warning
# https://github.com/numpy/numpy/issues/11448
np.seterr(invalid='ignore')    #０除算のエラー回避

class trend():
    def __init__(self,db_file_name,code_list,start_date,end_date,watch_len,day_sum_rate,high_grad,low_grad):
        self.end_date = end_date
        self.start_date = start_date
        self.code_list = code_list
        self.db_file_name = db_file_name
        self.stock_4data = []
        self.watch_len = watch_len
        self.sec_4data = pd.DataFrame()
        self.day_sum_rate = day_sum_rate    #傾きの合計がwatch_lenにこれを掛けた数を超えたらシグナル
        self.high_grad = high_grad          #これより傾きが小さい高音のラインだけをひく
        self.low_grad = low_grad            #これより傾きが大きい安値のラインだけを引く

    def get_all_4date(self,startday,endday,code):  # データベースに接続
        conn = sqlite3.connect(self.db_file_name)
        cur = conn.cursor()
        cur.execute("SELECT date, open, high, low, close  FROM prices1 WHERE code = ?", (code,)) # (code,)にすることで数値をタプルにしている
        #print("be")
        items_list = cur.fetchall()
        #print(items_list)
        fourdata = []
        date = []
        items_lists = list(items_list)
        #print(items_lists)
        for i in items_list:
            fourdata.append(list(i))

        #print(fourdata)
        df = pd.DataFrame(fourdata,
                          columns=['date', 'open', 'high', 'low', 'close'])
        #print(type(startday))
        #print(df['date'].values)

        df['date'] = pd.to_datetime(df['date'])
        df = df[(df['date'] >= pd.to_datetime(startday)) & (df['date'] <= pd.to_datetime(endday))]
        df.index = np.arange(len(df))
        # 日付スタンプ
        df['time_id'] = df.index + 1


        return df


    def get4date(self,startday,endday):  # データベースに接続
        #print(self.sec_4data, "here")
        self.sec_4data['date'] = pd.to_datetime(self.sec_4data['date'])
        df = self.sec_4data[(self.sec_4data['date'] >= pd.to_datetime(startday)) & (self.sec_4data['date'] <= pd.to_datetime(endday))]
        df.index = np.arange(len(df))
        # 日付スタンプ
        #df['time_id'] = df.index + 1
        #print(df)

        return df
        # df = get4date('/Users/tatsumiryou/sqlite.db',1301)[-500:]

    def get_highpoint(self, start, end,data):
        #data = self.get4date()[:-1]
        chart = data[start:end + 1].copy()
        while len(chart) > 3:
            regression = linregress(
                x=chart['time_id'],
                y=chart['high'],
            )
            chart = chart.loc[chart['high'] > regression[0] * chart['time_id'] + regression[1]]
        return chart

        # 安値の始点/支点を取得

    def get_lowpoint(self, start, end,data):
        #data = self.get4date()[:-1]
        chart = data[start:end + 1].copy()
        while len(chart) > 3:
            regression = linregress(
                x=chart['time_id'],
                y=chart['low'],
            )
            chart = chart.loc[chart['low'] < regression[0] * chart['time_id'] + regression[1]]
        return chart

    def g_trendlines(self, min_interval,startday,endday):
        support = []
        registance = []
        data = self.get4date(startday,endday)
        #print(data)
        # print(data.index)

        # 高値の下降トレンドラインを生成
        # print(self.watch_len)
        for i in range(1, self.watch_len, self.watch_len // 20):
            # print(i)
            # print(self.watch_len)
            highpoint = self.get_highpoint(i, i + self.watch_len,data)
            # ポイントが2箇所未満だとエラーになるので回避する
            if len(highpoint) < 2:
                continue
            # 始点と支点が近過ぎたらトレンドラインとして引かない
            if abs(highpoint.index[0] - highpoint.index[1]) < min_interval:
                continue
            regression = linregress(
                x=highpoint['time_id'],
                y=highpoint['high'],
            )
            # print(regression[0] < 0.0, 'reg_high: ', regression[0], ', ', regression[1], )

            # 上昇してるときだけ
            if regression[0] < self.high_grad:
                registance.append(regression[0] * data['time_id'][i:i + self.watch_len * 2] + regression[1])

        # 安値の上昇トレンドラインを生成
        for i in range(1, self.watch_len, self.watch_len // 20):
            lowpoint = self.get_lowpoint(i, i + self.watch_len,data)
            # ポイントが2箇所未満だとエラーになるので回避する
            if len(lowpoint) < 2:
                continue
            # 始点と支点が近過ぎたらトレンドラインとして引かない
            if abs(lowpoint.index[0] - lowpoint.index[1]) < min_interval:
                continue
            regression = linregress(
                x=lowpoint['time_id'],
                y=lowpoint['low'],
            )
            # print(regression[0] > 0.0, 'reg_low: ', regression[0], ', ', regression[1], )

            # 上昇してるときだけ
            if regression[0] > self.low_grad:
                support.append(regression[0] * data['time_id'][i:i + self.watch_len * 2] + regression[1])

        return registance, support, data


    def creat_break_point_list(self,startday,endday,code):

        days = (endday-startday).days
        #print(days + 1)
        #linemake = srline(self.db_file_name,days, days//10, code, startday, endday)
        #registance,support = linemake.g_trendlines(days,days//10)
        registance,support,data = self.g_trendlines(days//10,startday,endday)

        fourdata = data
        high = fourdata.iloc[-1]["high"]
        low = fourdata.iloc[-1]["low"]
        day = str(fourdata.iloc[-1]["date"])
        tdatetime = datetime.datetime.strptime(day, '%Y-%m-%d %H:%M:%S')
        tdate = datetime.date(tdatetime.year, tdatetime.month, tdatetime.day)
        up_break_dic = {}
        down_break_dic = {}
        len_list = []
        for i in registance:
            #print(1)
            i.plot()
            if i.iloc[-1] <= high:
                #print(len(i))
                len_list.append(len(i))
        p = sum(len_list)
        #print(p)
        if p >= self.watch_len * self.day_sum_rate:
            temdic = {tdate:[code]}
            up_break_dic.update(temdic)
            print(up_break_dic,"  buy  ",p)

        len_list = []
        for i in support:
            #print(1)
            i.plot()
            #print(len(i))
            #print(i)
            if i.iloc[-1] >= low:
                #print(len(i))
                len_list.append(len(i))

        p = sum(len_list)
        if p >= self.watch_len * self.day_sum_rate/1.5:
            temdic = {tdate: [code]}
            down_break_dic.update(temdic)
            print(up_break_dic, "  buy  ", p)
        #print(down_break_dic,up_break_dic)
        df = fourdata
        #print(df)


        df['high'].plot()
        df['low'].plot()
        plt.legend()
        #plt.show()
        #time.sleep(0.2)
        plt.pause(0.0001)
        plt.close()
        #print(1)



        return up_break_dic,down_break_dic,df

    def get_close_price_func(self,date, code,stocks):
        date1 = str(date)
        return stocks[code]['prices']['close'][date1]

    def get_open_price_func(self,date, code,stocks):
        date1 = str(date)
        #print(date, stocks[code]['prices']['open'][date1])
        return stocks[code]['prices']['open'][date1]

    def secure_profit(self,buydict, code, pro_per,stocks):
        sell = {}
        before = datetime.date
        count = 0
        for buy_day in buydict:
            # print(buy_day-self.end_date.date())
            period = (self.end_date.date() - buy_day).days
            buy_price = self.get_open_price_func(buy_day, code, stocks)
            for date in range(period):
                day = buy_day + datetime.timedelta(days=date)
                try:
                    today_price = self.get_open_price_func(day, code, stocks)
                    # print(before, buy_price, today_price)
                    if ((today_price / buy_price) - 1) * 100 >= pro_per:
                        sell.update({day: [code]})
                        break
                except:
                    pass
        #print(sell)
        return sell

    def losscut(self,buydict, code, losscutper,stocks):
        sell = {}
        before = datetime.date
        count = 0
        for buy_day in buydict:
            #print(buy_day-self.end_date.date())
            period = (self.end_date.date() - buy_day).days
            buy_price = self.get_open_price_func(buy_day, code,stocks)
            for date in range(period):
                day = buy_day + datetime.timedelta(days=date)
                try:
                    today_price = self.get_open_price_func(day, code,stocks)
                    # print(before, buy_price, today_price)
                    if (1 - (today_price / buy_price)) * 100 >= losscutper:
                        sell.update({day: [code]})
                        return sell
                except:
                    #print(day)
                    pass
        #print(sell)
        return sell

    def simulate_golden_dead_cross(self,
                                   deposit,
                                   order_under_limit,
                                   secure_profit_per,
                                   losscut_per):

        before = self.start_date - datetime.timedelta(days=self.watch_len)
        self.stock_4data = useful.create_stock_data(self.db_file_name, self.code_list, before, self.end_date)
        print(self.stock_4data)
        stocks = self.stock_4data     #portforioを使うために必要(無い方が綺麗に書けそうだが、変更が難しそうだからこれで妥協)

        up_dict = {}
        down_dict = {}
        #data_start = start - datetime.timedelta(days=watch_len)


        for code in self.code_list:
            #print(creat_break_point_list(db_file_name, start_date, end_date, code)[2].head(50))

            #print((start_date - end_date).days)
            self.sec_4data = self.get_all_4date(before,self.end_date,code)

            for i in range((self.end_date - self.start_date).days):

                data_start = self.start_date - datetime.timedelta(days=self.watch_len-i)
                date_end = self.start_date + datetime.timedelta(days=i)
                #print(code)
                up, down = self.creat_break_point_list(data_start,date_end,code)[:2]


                up_dict.update(up)
                down_dict.update(down)

                #print(get_open_price_func(date_end,code))
                #print(gd,dd)
                #print(2,golden_dict,dead_dict)
                #print(up_dict,down_dict)

                #print(self.stock_4data)


                losscuts = self.losscut(up_dict,code,losscut_per,self.stock_4data)
                secure_PF = self.secure_profit(up_dict,code,secure_profit_per,self.stock_4data)
                down_dict.update(losscuts)
                down_dict.update(secure_PF)
                #print(down_dict)



        #print(up_dict,"\n", down_dict)

        def get_close_price_func(date, code):
            date1 = str(date)
            return stocks[code]['prices']['close'][date1]

        def get_open_price_func(date, code):
            date1 = str(date)
            return stocks[code]['prices']['open'][date1]

        def trade_func(date, portfolio):
            order_list = []
            # Dead crossが発生していて持っている株があれば売る
            #print(up_dict)
            if date in down_dict:
                for code in down_dict[date]:

                    if code in portfolio.stocks:
                        order_list.append(
                            sim.SellMarketOrder(code,
                                                portfolio.stocks[code].current_count))
            # 保有していない株でgolden crossが発生していたら買う
            if date in up_dict:

                for code in up_dict[date]:
                    if code not in portfolio.stocks:
                        order_list.append(
                            sim.BuyMarketOrderMoreThan(code,
                                                       stocks[code]['unit'],
                                                       order_under_limit))
            return order_list

        a = sim.simulate(self.start_date, self.end_date,
                         deposit,
                         trade_func,
                         get_open_price_func, get_close_price_func)


        return a



if __name__ == '__main__':
    start = datetime.datetime(2022,2,10)
    end = datetime.datetime(2022,4,30)
    cla = trend('/Users/tatsumiryou/sqlite.db',[6658],start,end,100,2.8,10,-10)
    cla.simulate_golden_dead_cross(200000,10000,10,3)
    #simulate_golden_dead_cross('/Users/tatsumiryou/sqlite.db',start,end,[3907],1000000,10000,100)
