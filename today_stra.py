import sqlite3
import datetime
from collections import defaultdict
import pandas as pd
from BACKTEST import myportfolio as sim
from Today_trade import gdline
from matplotlib import pyplot as plt
import sqlite3
import numpy as np
from Today_trade.regi_macd import Regi_Macd
from slack_sdk import WebClient

class get_ready:
    def __init__(self,db_file_name,today):
        self.db_file_name = db_file_name
        self.code_list = []
        self.today = today
        self.price = []
        self.result = []

    def get_code(self,table):
        conn = sqlite3.connect(self.db_file_name)
        code_df = pd.read_sql(f'SELECT code from {table}',conn)
        #print(code_df.values.tolist())
        self.code_list = []
        for code in code_df.values.tolist():
            self.code_list.append(code[0])
            #print(code)
        #print(self.code_list)

    def get_all_4date(self,startday,endday,code):  # データベースに接続
        conn = sqlite3.connect(self.db_file_name)
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

    def make_stra(self):
        SLACK_ACCESS_TOKEN = 'xoxb-3384704669223-3393126568294-DcXVaGANFXV8fb4xD04RSR4v'
        CHANNEL_ID = 'C03GLMX555E'

        # Slackクライアントを作成
        client = WebClient(SLACK_ACCESS_TOKEN)

        self.get_code("look_brand")
        #print(self.code_list)


        #self.price = self.get_all_4date(self.before, self.today,self.code_list)
        self.result = pd.DataFrame(index=self.code_list, columns=["upper_power", "down_power", "registance_power"])
        self.result.fillna(0, inplace=True)
        #print(self.code_list)
        for code in self.code_list:
            #print(code)
            #self.result = gdline.golde().goldead(prices,code,self.result)
            a = Regi_Macd(self.today,code,100,1.8,10,-10,12,26,9,359,0.5,1)
            self.result = a.breaklist(self.result)

        self.get_code("hold_brand")
        #print(self.code_list)
        for code in self.code_list:
            #self.result = gdline.golde().goldead(prices,code,self.result)
            a = Regi_Macd(self.today,code,100,1.8,10,-10,12,26,9,359,0.5,1)
            self.result = a.MACD_hist(self.result)


        #print(self.result)
        up = self.result.query("upper_power > 0").index
        down = self.result.query("down_power > 0").index



        # パブリックチャンネルにメッセージを投稿（chat.postMessageメソッド）
        if len(up):
            msg = f"{list(up)}買うしかないっっ！"
            response = client.chat_postMessage(channel=CHANNEL_ID, text=msg, icon_emoji=':robot_face:',
                                               username='Slack Bot')
        if len(down):
            msg = f"{list(down)}売るしかないっっ！"
            response = client.chat_postMessage(channel=CHANNEL_ID, text=msg, icon_emoji=':robot_face:',
                                               username='Slack Bot')


if __name__ == '__main__':
    today = datetime.date.today()
    #today = datetime.date(2022,1,5)
    se = datetime.date(2021,5,16)
    a = get_ready("/Users/tatsumiryou/sqlite.db",today)
    a.make_stra()


