import sqlite3
import datetime
from collections import defaultdict
import pandas as pd
from BACKTEST import myportfolio as sim
from matplotlib import pyplot as plt
import sqlite3
import numpy as np



def create_stock_data(db_file_name, code_list, start_date, end_date):
    """指定した銘柄(code_list)それぞれの単元株数と日足(始値・終値）を含む辞書を作成
    """
    stocks = {}
    tse_index = sim.tse_date_range(start_date, end_date)
    conn = sqlite3.connect(db_file_name)
    for code in code_list:
        try:
            unit = conn.execute('SELECT unit from brand WHERE code = ?',
                                (code,)).fetchone()[0]
        except:
            print(f"{code}がデータベースの'brand'テーブルに存在しないので、最小購入単位を100に仮定します")
            unit = 100
        prices = pd.read_sql('SELECT date, open, high, low, close '
                                 'FROM prices1 '
                                 'WHERE code = ? AND date BETWEEN ? AND ?'
                                 'ORDER BY date',
                                 conn,
                                 params=(code, start_date, end_date),
                                 parse_dates=('date',),
                                 index_col='date')
        stocks[code] = {'unit': int(str(unit).replace(",","")),
                            'prices': prices.reindex(tse_index, method='ffill')}
        #print(code,"\n")
    return stocks


def losscut(buydict, code, losscutper,get_open_price_func):  # buydictはdatetimeの配列
    sell = {}
    before = datetime.date
    count = 0
    for after in buydict:
        if count != 0:
            period = (after - before).days
            buy_price = get_open_price_func(before, code)  # 株を買った日の株価を取ってくる

            for date in range(period):
                day = before + datetime.timedelta(days=date)
                try:
                    today_price = get_open_price_func(day, code)  # 今日の株価
                    # print(before, buy_price,today_price)
                    if (1 - (today_price / buy_price)) * 100 >= losscutper:  # 今日の株価と株を買った日の株価を比較
                        sell.update({day: [code]})  # ロスカットのための売り注文
                        # print(1)
                except KeyError:
                    continue
        count += 1
        before = after
    return sell  # 辞書型で返す


def get_all_4date(db_file_name,startday,endday,code):  # データベースに接続
        conn = sqlite3.connect(db_file_name)
        cur = conn.cursor()
        cur.execute("SELECT date, open, high, low, close  FROM prices1 WHERE code = ?", (code,)) # (code,)にすることで数値をタプルにしている
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

        df['date'] = pd.to_datetime(df['date'])
        df = df[(df['date'] >= pd.to_datetime(startday)) & (df['date'] <= pd.to_datetime(endday))]
        df.index = np.arange(len(df))

        return df