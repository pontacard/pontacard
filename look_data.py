import sqlite3
import pandas as pd
import time
import datetime
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

class look_sales():
    def __init__(self,db_file_name,Cmp_scale,EPS_grow,sales_grow,al_grow_EPS,ROE,RS_Deviation):
        self.db_file_name = db_file_name
        self.Cmp_scale = Cmp_scale #単位は百万円
        self.EPS_grow = EPS_grow #前のEPSより何%伸びたか
        self.temp_list = [] #最初にこれからのループの範囲を決める
        self.brand_list = pd.DataFrame() #監視銘柄
        self.sub_list = pd.DataFrame() #欠損値のあるものの有能な銘柄
        self.today = datetime.date.today()
        self.sales_grow = sales_grow
        self.al_grow_EPS = al_grow_EPS
        self.ROE = ROE
        self.RS_Deviation = RS_Deviation


    def get_sales(self,table):
        colum_list = ['code,season,date,sales,operating_profit,ordinal_profit,final_profit,EPS,profit_rate',
                      "code,date,operating_profit,free_CF,operating_CF,invest_CF,finance_CF,stock_cash,cash_rate",
                      "code,date,BPS,capital_ratio,assets,equity_asset,surpuls,DE_ratio"]

        if table == "quarter_sales":
            colum = colum_list[0]
        elif table == "cash_flow":
            colum = colum_list[1]
        else:
            colum = colum_list[2]

        conn = sqlite3.connect(self.db_file_name)

        #df = pd.read_sql(f'SELECT {colum} FROM {table}', conn)

        df = pd.read_sql(f'SELECT {colum} '
                         f'FROM {table}',
                         conn,
                         parse_dates=('date',),
                         index_col='code')
        #print(df)

        return df

    def create_stock_data(self, code_list, start_date, end_date):
        """指定した銘柄(code_list)それぞれの単元株数と日足(始値・終値）を含む辞書を作成
        """
        stocks = {}
        conn = sqlite3.connect(self.db_file_name)
        prices = pd.read_sql('SELECT code, date, open, close ,high, low '
                             'FROM prices1 '
                             'WHERE date BETWEEN ? AND ?'
                             'ORDER BY code',
                             conn,
                             params=(start_date, end_date),
                             parse_dates=('date',),
                             index_col='code')
        # print(code,"\n")
        return prices

    def check_scale(self,finance_list):
        for i in range (1301,9999):
            try:
                asset = finance_list.at[str(i),"assets"]#総資産
                #print(i)
                try:
                    if asset[-1] <= self.Cmp_scale:  #総資産が規定値より下→中小企業のみを選ぶ
                            self.temp_list.append(i)
                except:
                    if asset <= self.Cmp_scale:  #assetのlen=1だとバグるから
                            self.temp_list.append(i)


            except KeyError:
                continue
        #print(self.temp_list)

        return self.brand_list

    def check_EPS(self,sales_list):
        EPS_list = []
        for i in self.temp_list:
            try:
                EPS = sales_list.at[str(i),"EPS"]
                for j in range(1,4):
                    try:                             #一年前の決済データがあるか
                        if EPS[-j-4] == 0:           #growが発散しないように
                            grow = EPS[-j]
                        elif EPS[-j-4] > 0:
                            grow = (EPS[-j] / EPS[-j-4]) * 100
                        else:
                            grow = ((EPS[-j] / abs(EPS[-j-4])) * 100) + 100
                        self.brand_list.loc[f"grow_EPS{j}", i] = grow
                    except IndexError:
                        self.brand_list.loc[f"grow_EPS{j}", i] = None


            except KeyError:
                self.brand_list.loc["grow_EPS1",i] = None
                self.brand_list.loc["grow_EPS2", i] = None
                self.brand_list.loc["grow_EPS3", i] = None

    def check_sales(self,sales_list):
        for i in self.temp_list:
            try:
                sales = sales_list.at[str(i), "sales"]
                for j in range(1, 4):
                    try:  # 一年前の決済データがあるか
                        if sales[-j - 4] == 0:  # growが発散しないように
                            grow = sales[-j]
                        else:
                            grow = (sales[-j] / abs(sales[-j - 4])) * 100
                        self.brand_list.loc[f"sales_grow{j}", i] = grow
                    except IndexError:
                        self.brand_list.loc[f"sales_grow{j}", i] = None


            except KeyError:
                self.brand_list.loc["sales_grow1", i] = None
                self.brand_list.loc["sales_grow2", i] = None
                self.brand_list.loc["sales_grow3", i] = None

    def annual_EPS(self,sales_list):
        for i in self.temp_list:
            try:
                EPS = sales_list.at[str(i),"EPS"]
                list = [0,0]
                for j in range(2):
                    tmp = 0
                    for k in range(4):
                        try:                             #一年前の決済データがある
                            tmp += EPS[4*j + k]

                        except IndexError:
                            pass
                    list[j] = tmp
                    self.brand_list.loc[f"annual_EPS{j+1}", i] = tmp
                if list[0] == 0:  # growが発散しないように
                    grow = list[1]
                elif list[0] > 0:
                    grow = (list[1] / list[0]) * 100
                else:
                    grow = ((list[1] / abs(list[0])) * 100) + 100
                self.brand_list.loc[f"anl_grow_EPS", i] = grow


            except KeyError:
                self.brand_list.loc[f"annual_EPS{1}", i] = None
                self.brand_list.loc[f"annual_EPS{2}", i] = None
                self.brand_list.loc[f"anl_grow_EPS", i] = None


    def check_ROE(self,finance_list):
        for i in self.temp_list:
            #print(i)
            try:
                ROE = finance_list.at[str(i),"capital_ratio"][-1]
            except IndexError:
                ROE = finance_list.at[str(i),"capital_ratio"]
            self.brand_list.loc["ROE", i] = ROE

    def relative_strength(self,stock_list):
        RS = pd.DataFrame()
        for i in self.temp_list:
            Cs =0
            try:    #名証、札証の株コードだとここに引っかかる。
                Cs = stock_list.loc[str(i)]
            except KeyError:
                continue
            try:
                C252 = Cs.iloc[-240]["close"]
                C189 = Cs.iloc[-180]["close"]
                C126 = Cs.iloc[-120]["close"]
                C63 = Cs.iloc[-60]["close"]
                C = Cs.iloc[-1]["close"]
                ans = ((((C-C63)/C63) * 0.4) + (((C-C126)/C126) * 0.3)
                       + (((C-C189)/C189) * 0.2) + (((C-C252)/C252) * 0.1)) * 100
                RS.loc[i,"Values"] = ans
            except IndexError:
                #print(i,len(Cs))
                RS.loc[i,"Values"] = 1
        #RSD = RS.T.round()
        RSD = RS

        df_score = RSD['Values']  #偏差値の計算と追加
        df_score_std = df_score.std(ddof=0)
        df_score_mean = df_score.mean()
        dv_ary = []
        for index, row in RSD.iterrows():
            x = row['Values']
            a = (x - df_score_mean) / df_score_std * 10 + 50
            b = round(a)
            dv_ary.append(b)

        # Seriesに変換
        dv = pd.Series(dv_ary).astype(int)
        print(dv)
        dv.index = RSD.index
        # DataFrameと結合
        RSD['DeviationValue'] = dv
        print(RSD)
        self.brand_list.loc["RS_Deviation"] = dv.T



    def screen(self):
        sales_list = self.get_sales("quarter_sales")
        CF_list = self.get_sales("cash_flow")
        finance_list = self.get_sales("finance")

        self.check_scale(finance_list)
        self.brand_list =pd.DataFrame(columns=self.temp_list)

        #print(self.brand_list)
        self.check_EPS(sales_list)
        self.check_sales(sales_list)
        self.annual_EPS(sales_list)
        self.check_ROE(finance_list)
        #print(self.brand_list)

        di = datetime.timedelta(days=450)
        ago = self.today - di
        # print(self.temp_list)
        stock_list = self.create_stock_data(self.temp_list, ago, self.today)
        #print(stock_list)
        self.relative_strength(stock_list)
        #print(self.brand_list)

        return 0

    def write_table(self):
        print(list(self.brand_list.index))
        conn = sqlite3.connect(self.db_file_name)
        with conn:
            sql = 'DELETE FROM look_brand'
            conn.execute(sql)

        for code in self.brand_list.index:
            with conn:
                sql = f"""
                            INSERT INTO 
                            look_brand (code)
                            VALUES(?)
                            """
                conn.execute(sql,(code,))
            #print(1)


    def check_it_out(self):
        self.screen()
        brand = self.brand_list.T #扱いやすいようにデータリストの転置
        brand = brand[brand["grow_EPS1"] >= self.EPS_grow] #直前四半期EPS成長率
        brand = brand[brand["grow_EPS2"] >= self.EPS_grow]
        brand = brand[brand["sales_grow1"] >= self.sales_grow]
        brand = brand[brand["anl_grow_EPS"] >= self.al_grow_EPS]
        brand = brand[brand["ROE"] >= self.ROE]
        brand = brand[brand["RS_Deviation"] >= self.RS_Deviation]
        self.brand_list = brand
        print(brand.head(60))

        self.write_table()









if __name__ == '__main__':
    a = look_sales("/Users/tatsumiryou/sqlite.db",300000,120,120,125,10,57)
    a.check_it_out()