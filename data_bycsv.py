
import time
import sqlite3
import requests
import datetime
import re
import csv
import glob
import datetime
import os
import sqlite3



from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

class Write4data:
    def __init__(self,db_dir,csv_file_name):
        self.db_dir = db_dir
        self.csv_file_name= csv_file_name

    def generate_price_from_csv_file(self,option = False):
        with open(self.csv_file_name) as f:
            reader = csv.reader(f)
            #print(f.read())
            for row in reader: #１行づつcsvからデータをとってる
                code = int(row[0])
                d = row[1] #日付
                o = float(row[2])  # 初値
                h = float(row[3])  # 高値
                l = float(row[4])  # 安値
                c = float(row[5])  # 終値
                v = int(row[6])    # 出来高
                be = float(row[7])
                af = float(row[8])
                yes = row[9]
                print(code, d, o, h, l, c, v)
                #if str(d[5:7]) == "01": #10月には01,1月には10にし、それ以外では消しておく
                    #continue

                if option:
                    yield code, d, o, h, l, c, v, be, af, yes
                else:
                    yield code, d, o, h, l, c, v


    def raw_prices_to_db(self):
        #print((price_generator,[0]))


        conn = sqlite3.connect(self.db_dir) #１行づつ返されるからそれを書き込む

        price_generator = self.generate_price_from_csv_file()
        print(price_generator)
        print(price_generator)

        with conn:
            sql = 'INSERT INTO raw_prices(code,date,open,high,low,close,volume) ' \
                  'VALUES(?,?,?,?,?,?,?)'
            conn.executemany(sql, price_generator)

    def prices1_to_db(self):
        price_generator = self.generate_price_from_csv_file()

        conn = sqlite3.connect(self.db_dir)
        with conn:
            sql = 'INSERT INTO prices1(code,date,open,high,low,close,volume) ' \
                  'VALUES(?,?,?,?,?,?,?)'
            conn.executemany(sql, price_generator)

    def dvide_to_db(self):
        conn = sqlite3.connect(self.db_dir)

        datas = list(self.generate_price_from_csv_file(option=True))
        #print(datas)

        for data in datas:
            data = list(data)
            # print(data)
            brandata = data[0:1]
            brandata.extend(data[9:])
            brandata.extend(data[7:9])
            brandata = (tuple(brandata),)

            if brandata[0][2] != 0 and brandata[0][3] != 0:
                print(brandata)
                with conn:
                    sql = """
                                INSERT INTO 
                                divide_union_data1 (code, date_of_right_allotment,before, after)
                                VALUES(?,?,?,?)
                                """
                    conn.executemany(sql, brandata)


class get_todata:
    def __init__(self,db_dir,date):
        self.db_dir = db_dir #dbのパス
        self.date = date #とりたい日付

    def getcsv(self):
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()

        drive = GoogleDrive(gauth)

        ID = "1kg8popgHlSkiOZu7Hv0dAj7QXWM1Ud42"

        file_name = str(self.date) + "-4data.csv"

        file_id = drive.ListFile({'q': f'title = "{file_name}"'}).GetList()[0]['id'] #ファイル名からid取得

        f = drive.CreateFile({'id': file_id})
        f.GetContentFile(f'/Users/tatsumiryou/PycharmProjects/youtube/{file_name}.csv')


        #conn = sqlite3.connect(self.db_dir)

        writ = Write4data(self.db_dir,f'/Users/tatsumiryou/PycharmProjects/youtube/{file_name}.csv')
        writ.raw_prices_to_db()
        writ.prices1_to_db()
        writ.dvide_to_db()

        datas = list(writ.generate_price_from_csv_file(option=True))
        #print(list(datas))

