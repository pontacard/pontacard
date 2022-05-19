import datetime
from BACKTEST.trend_stra import trend
from scipy.stats import linregress
import numpy as np
import matplotlib.pyplot as plt
import cmath
from BACKTEST.make_macd import MACD
from BACKTEST import myportfolio as sim
import time
from BACKTEST import useful
import talib as ta

np.seterr(invalid='ignore')    #０除算のエラー回避

class Lgrad(trend):
    def __init__(self,db_file_name,code_list,start_date,end_date,watch_len,day_sum_rate,high_grad,low_grad,short_days,long_days,signal_days,above_arg,under_arg,alpha):
        super().__init__(db_file_name,code_list,start_date,end_date,watch_len,day_sum_rate,high_grad,low_grad)
        self.stock_list = []
        self.short_days = short_days
        self.long_days = long_days
        self.signal_days = signal_days
        self.under_arg = under_arg
        self.above_arg = above_arg        #レンジ相場か確かめるためのパラメーター、この二つの角度が狭いほど、買いシグナルが絞られる。
        self.alpha = alpha                #これが小さいほど、売りシグナルがよく出る(macd_histの変化率が減った時に、前日のmacd_histがこれの定数倍以上だったらシグナル)


    def deg_mean(self,angles, deg=True):
        '''Circular mean of angle data(default to degree)
        '''
        a = np.deg2rad(angles) if deg else np.array(angles)  #ラジアンに統一
        angles_complex = np.frompyfunc(cmath.exp, 1, 1)(a * 1j)     #e^iθ
        mean = cmath.phase(angles_complex.sum()) % (2 * np.pi)      #総和、また、cmath.phaseは結果を[-π, π]の範囲で返すため、2πで割った余りを計算することで0から2πにした
        return round(np.rad2deg(mean) if deg else mean, 7)

    def s_deg(self,df,hdeg,ldeg):   #傾きを正規化してからの角度に変換(見かけのスケールにする)
        high = df['high'].max()
        low = df['low'].min()
        lenge = len(df)

        for i,deg in enumerate(hdeg):
            ans = deg *lenge/(high - low)
            ans = np.degrees(np.arctan(ans))
            hdeg[i] = ans
        for i,deg in enumerate(ldeg):
            ans = deg *lenge/(high - low)
            ans = np.degrees(np.arctan(ans))
            ldeg[i] = ans

        return hdeg,ldeg

    def g_trendlines(self, min_interval, startday, endday):
        support = []
        registance = []
        #print(startday,endday)
        #data = self.get4date(startday, endday)[:-1]
        data = self.get4date(startday, endday)
        #print(data)
        hgra = []
        regression = []

        # 高値の下降トレンドラインを生成
        # print(self.watch_len)
        for i in range(1, self.watch_len, self.watch_len // 20):
            # print(i)
            # print(self.watch_len)
            highpoint = self.get_highpoint(i, i + self.watch_len, data)
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
                #print("koko",regression[0],np.degrees(np.arctan(regression[0])))
                hgra.append(regression[0])
        #print(hgra)

        return registance, data, hgra

    def MACD_dead(self,code):
        mac = MACD(self.short_days,self.long_days,self.signal_days,code,self.start_date,self.end_date,self.db_file_name)
        data_list = mac.ta_macd()

        which_above = data_list["MACD"] > data_list["MACD_signal"]
        cross = which_above != which_above.shift(1)
        dead_cross = cross & (which_above == False)

        dead_list = data_list[dead_cross]["date"][1:]  # 日付のリストに変かん

        #print(dead_list)
        #print(dead_list)
        #print(dy1[dead_cross],dy2[dead_cross])

        dcodes = [[code]] * len(dead_list)
        dd = dict(zip(dead_list, dcodes))

        return dd

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

    def MACD_hist(self,buydict,code):
        mac = MACD(self.short_days, self.long_days, self.signal_days, code, self.start_date, self.end_date,
                   self.db_file_name)
        data_list = mac.ta_macd()
        sell = {}
        buy_list =[]
        dy1 = np.gradient(data_list["MACD_hist"])
        data_list["hist_grad"] = dy1

        for buy_day in buydict:
            for date in range(100):
                day = buy_day + datetime.timedelta(days=date)
                before = day + datetime.timedelta(days=date-100)
                hist = data_list.query(f"date < @day")
                hist = hist.query(f"date > @before")
                histup = hist[hist["MACD_hist"] > 0]["MACD_hist"]  # 過去60日のhistが０より大きいところ

                #print(hist)

                #print(histup)

                top5 = histup.quantile(0.95)
                #print(top5)

                # print(dy1)
                """
                for i, dy in enumerate(cnd_list):
                    # print(type(dy),i)
                    #print(hist.iloc[i - 1]["MACD_hist"])
                    if i == 0:
                        continue
                    if dy["hist_grad"] < 0 and hist.iloc[i - 1]["MACD_hist"] > top5:
                        #print(hist.iloc[i]["date"].year)
                        sell_day = datetime.date(year=cnd_list.iloc[i]["date"].year,month= cnd_list.iloc[i]["date"].month,day=cnd_list.iloc[i]["date"].day)
                        sell.update({sell_day: [code]})
                        #print(sell)
                        return sell
                """
                #print(hist.iloc[-2])
                try:
                    if hist.iloc[-1]["hist_grad"] < 0 and hist.iloc[-2]["MACD_hist"] > self.alpha * top5:
                        # print(hist.iloc[i]["date"].year)
                        sell_day = datetime.date(year=hist.iloc[-1]["date"].year, month=hist.iloc[-1]["date"].month,
                                                 day=hist.iloc[-1]["date"].day)
                        sell.update({sell_day: [code]})
                        # print(sell)
                        break
                except IndexError:
                    pass

        return sell







    def creat_break_point_list(self,startday,endday,code):

        days = (endday-startday).days
        registance,data,hdeg = self.g_trendlines(days//10,startday,endday)


        fourdata = data
        high = fourdata.iloc[-1]["high"]
        low = fourdata.iloc[-1]["low"]
        day = str(fourdata.iloc[-1]["date"])
        #print(2)
        #print(day)
        tdatetime = datetime.datetime.strptime(day, '%Y-%m-%d %H:%M:%S')
        tdate = datetime.date(tdatetime.year, tdatetime.month, tdatetime.day)
        up_break_dic = {}
        down_break_dic = {}
        len_list = []

        hg_ave = self.deg_mean(hdeg)

        #print(hg_ave,lg_ave)

        for i in registance:
            i.plot()
            if i.iloc[-1] <= high:
                len_list.append(len(i))
        p = sum(len_list)
        if p >= self.watch_len * self.day_sum_rate:
            if hg_ave > self.above_arg or hg_ave < self.under_arg:       #-4度から6度までの角度
                temdic = {tdate:[code]}
                up_break_dic.update(temdic)
                #print(hdeg,ldeg,self.deg_mean([hdeg,ldeg]))
                print(up_break_dic,"  buy  ",p,hg_ave)
        df = fourdata
        #print(df)


        #df['high'].plot()
        #df['low'].plot()
        #plt.legend()
        #plt.show()
        #time.sleep(0.2)
        #plt.pause(0.0001)
        #plt.close()
        #print(1)

        return up_break_dic,down_break_dic,df

    def simulate_golden_dead_cross(self,
                                   deposit,
                                   order_under_limit,
                                   secure_profit_per,
                                   losscut_per):

        before = self.start_date - datetime.timedelta(days=self.watch_len)
        self.stock_4data = useful.create_stock_data(self.db_file_name, self.code_list, before, self.end_date)
        #print(self.stock_4data)
        stocks = self.stock_4data     #portforioを使うために必要(無い方が綺麗に書けそうだが、変更が難しそうだからこれで妥協)

        up_dict = {}
        down_dict = {}
        #data_start = start - datetime.timedelta(days=watch_len)


        for code in self.code_list:
            print(code)
            #print(creat_break_point_list(db_file_name, start_date, end_date, code)[2].head(50))

            #print((start_date - end_date).days)
            self.sec_4data = self.get_all_4date(before,self.end_date,code)
            #print(self.stock_4data.values())
            tmp_up = {}

            for i in range((self.end_date - self.start_date).days):

                data_start = self.start_date - datetime.timedelta(days=self.watch_len-i)
                date_end = self.start_date + datetime.timedelta(days=i)
                #print(code)
                up, down = self.creat_break_point_list(data_start,date_end,code)[:2]


                up_dict.update(up)
                tmp_up.update(up)
                down_dict.update(down)

                #print(get_open_price_func(date_end,code))
                #print(gd,dd)
                #print(2,golden_dict,dead_dict)
                #print(up_dict,down_dict)

            #print(tmp_up)
            for up in tmp_up:
                up_set = {up:[code]}
                losscuts = self.losscut(up_set,code,losscut_per,self.stock_4data)
                secure_PF = self.secure_profit(up_set,code,secure_profit_per,self.stock_4data)
                down_dict.update(losscuts)
                #print("loss",losscuts)
                down_dict.update(secure_PF)
                #print(11,dead_list)

                hist = self.MACD_hist(up_set,code)
                #print(hist)
                down_dict.update(hist)

            dead_list = self.MACD_dead(code)
            down_dict.update(dead_list)



        #print(up_dict,"\n", down_dict)

        def get_close_price_func(date, code):
            date1 = str(date)
            return stocks[code]['prices']['close'][date1]

        def get_open_price_func(date, code):
            date1 = str(date)
            return stocks[code]['prices']['open'][date1]

        def trade_func(date, portfolio):
            order_list = []
            #print(11,up_dict)
            # Dead crossが発生していて持っている株があれば売る
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
    start = datetime.datetime(2019,11,4)
    end = datetime.datetime(2022,4,30)
    #startday = datetime.datetime(2019,7,20)
    #endday = datetime.datetime(2020,4,26)
    days = (end-start).days
    code = [6651]
    cla = Lgrad('/Users/tatsumiryou/sqlite.db',code,start,end,100,1.8,10,-10,12,26,9,358,4,1)
    #cla.sec_4data = cla.get_all_4date(start,end,code)
    #cla.creat_break_point_list(startday,endday,code)
    cla.simulate_golden_dead_cross(200000,10000,18,3)
