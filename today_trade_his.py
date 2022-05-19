from slack_sdk import WebClient
import re
import datetime
import sqlite3

SLACK_ACCESS_TOKEN = 'xoxb-3384704669223-3393126568294-DcXVaGANFXV8fb4xD04RSR4v'
CHANNEL_ID = 'C03BR934R0A'

# Slackクライアントを作成
client = WebClient(SLACK_ACCESS_TOKEN)

result = client.conversations_list()

def check_message():
    SLACK_ACCESS_TOKEN = 'xoxb-3384704669223-3393126568294-DcXVaGANFXV8fb4xD04RSR4v'
    CHANNEL_ID = 'C03BR934R0A'

    # Slackクライアントを作成
    client = WebClient(SLACK_ACCESS_TOKEN)

    result = client.conversations_list()
    #print(result)

    conn = sqlite3.connect('/Users/tatsumiryou/sqlite.db')

    message = client.conversations_history(channel=CHANNEL_ID)        #slack特有のオブジェクト、getで情報を引き出す

    last_messages = message.get("messages")[:20]

    for mess in last_messages:
        texts = mess["text"]
        data = texts.split()
        #print(texts)
        try:
            if data[3] == "buy":
                date = datetime.datetime.strptime(data[0], '%Y-%m-%d')
                date = datetime.date(date.year, date.month, date.day)
                #print(data)
                data_list = [str(date)] +data[1:3] + [data[4]]      #メッセージの内容をlistにまとめた

                cur = conn.cursor()
                cur.execute(f"SELECT code, buy_day, sell_day  FROM trade_recode WHERE code = {data[1]}")
                recode_list = cur.fetchall()

                #print(recode_list)
                for recode in recode_list:
                    if recode[1] == str(date):
                        #print(1111)
                        return 0                    #trade_recodeに記録されてたら重複防止でreturn


                with conn:
                    sql = 'INSERT INTO hold_brand(date,code,get_price,quantity) VALUES(?,?,?,?)'        #holdbrandに追加
                    try:
                        conn.executemany(sql, [tuple(data_list)])
                    except sqlite3.IntegrityError:
                        pass

            elif data[3] == "sell":
                date = datetime.datetime.strptime(data[0], '%Y-%m-%d')
                date = datetime.date(date.year, date.month, date.day)
                # print(data)
                data_list = [str(date)] + data[1:3] + [data[4]]
                #print(data_list)


                cur = conn.cursor()
                #print([(data[1],),(str(date),)])
                cur.execute(f"SELECT code, buy_day, sell_day  FROM trade_recode WHERE code = {data[1]}")
                recode_list = cur.fetchall()
                #print(recode_list)

                for recode in recode_list:
                    if recode[2] == str(date):
                        return 0

                cur = conn.cursor()
                cur.execute("SELECT date,code, get_price, quantity  FROM hold_brand WHERE code = ?",
                            (data[1],))
                item_list = cur.fetchall()
                #print(item_list)


                ans = [item_list[0][1]] + [item_list[0][0]] + [str(date)] + [item_list[0][2]] + data_list[2:]    #trade_recodeに入れるデータ
                cur = conn.cursor()
                cur.execute('DELETE FROM hold_brand  WHERE code = ?',(data[1],))            #売ったらholdbrandから削除

                with conn:
                    sql = 'INSERT INTO trade_recode (code,buy_day,sell_day, buy_price, sell_price, quantity) VALUES(?,?,?,?,?,?)'
                    conn.executemany(sql,[tuple(ans)])      #traderecodeに追加

            elif data[3] == "addbuy":
                date = datetime.datetime.strptime(data[0], '%Y-%m-%d')
                date = datetime.date(date.year, date.month, date.day)
                # print(data)
                data_list = [str(date)] + data[1:3] + [data[4]]

                cur = conn.cursor()
                # print([(data[1],),(str(date),)])
                cur.execute(f"SELECT code, date, get_price  FROM add_hold_brand WHERE code = {data[1]}")            #追加購入の履歴
                recode_list = cur.fetchall()
                #print(recode_list)

                for recode in recode_list:
                    if recode[1] == str(date):
                        return 0

                cur = conn.cursor()
                cur.execute("SELECT date,code, get_price, quantity  FROM hold_brand WHERE code = ?",
                            (data[1],))
                item_list = cur.fetchall()

                sumq = int(data_list[3]) + int(item_list[0][3])     #holdbrandに入れる持株数と平均約締単価の計算
                price = (int(data_list[2]) * int(data_list[3]) + int(item_list[0][2]) * int(item_list[0][3])) / sumq

                cur = conn.cursor()
                cur.execute('DELETE FROM hold_brand  WHERE code = ?', (data[1],))

                ans = list(item_list[0][:2]) + [price] + [sumq]      #追加購入を考慮したデータに変更
                with conn:
                    sql = 'INSERT INTO hold_brand (date, code, get_price, quantity) VALUES(?,?,?,?)'
                    conn.executemany(sql,[tuple(ans)])

                a = [data_list[1]] + [data_list[0]] + [data_list[2]]
                with conn:
                    sql = 'INSERT INTO add_hold_brand (code, date, get_price) VALUES(?,?,?)'
                    conn.executemany(sql,[tuple(a)])










        except IndexError:
            pass

