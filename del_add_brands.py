# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import datetime
import sqlite3
import requests
import time
import numpy as np

class getbrands:
    def __init__(self,db_file_name,code_range):
        self.db_file_name = db_file_name
        self.code_range = code_range


    def get_brand(self,code):
        res = requests.get(f"https://finance.yahoo.co.jp/quote/{code}")
        soup = BeautifulSoup(res.text, 'html.parser')
        try:
            name = soup.find( class_='_6uDhA-ZV').text
            num = soup.find( class_='_2wsoPtI7').text
            short_name = name[:7]
            market = soup.find( class_='_3sg2Atie').text
            sector = soup.find( class_='_1unyWCX0 _2jbOvvHc').text
            unit = soup.find( class_='_3rXWJKZF _11kV6f2G').text
            print(code,name ,num ,short_name,market,sector,unit)
        except AttributeError:
            return None

        return name ,num ,short_name,market,sector,unit


    def brands_generator(self,code_range):
      for code in code_range:
        #print(code)
        brand = self.get_brand(code)
        if brand:
          yield brand
        time.sleep(0.1)

    def insert_brands_to_db(self):
      conn = sqlite3.connect(self.db_file_name)
      with conn:
        sql = 'INSERT INTO brand(name,code,market,short_name,unit,sector) ' \
              'VALUES(?,?,?,?,?,?)'
        conn.executemany(sql, self.brands_generator(self.code_range))


class add_brand:

    def new_brands_generator(self):
        res = requests.get("http://www.jpx.co.jp/listing/stocks/new/index.html")
        soup = BeautifulSoup(res.text, 'html.parser')
        judge = True
        t = 0
        for i in range(12):
            aaa = i % 2 + 1
            date = soup.find_all(class_=f'a-center tb-color00{aaa} w-space')
            oneday = date[i//2].text[:10]
            oneday = oneday.replace('/','-')
            today = str(datetime.date.today())
            #today = str(datetime.date(2021, 4, 22))
            print(today,oneday)
            if oneday == today:

                code = soup.find_all(class_=f'a-center tb-color00{aaa}')
                code = code[7*(i//2)].text
                code = code[2:6]
                t += 1
                #print(code,today)
                yield (code,today)

    def insert_new_brands_to_db(self,db_file_name):
      conn = sqlite3.connect(db_file_name)
      with conn:
        sql = 'INSERT INTO new_brands(code,date) VALUES(?,?)'
        conn.executemany(sql, self.new_brands_generator())

    #insert_new_brands_to_db('/Users/tatsumiryou/sqlite.db')

    def get4data(self):
        code = list(self.new_brands_generator())
        print(code)
        ncode = []
        for i in range(len(code)):
            ncode.append (int(code[i][0]))

        a = getbrands('/Users/tatsumiryou/sqlite.db', ncode)
        a.insert_brands_to_db()

class del_brand:
    def new_brands_generator(self):
        res = requests.get("https://www.jpx.co.jp/listing/stocks/delisted/index.html")
        soup = BeautifulSoup(res.text, 'html.parser')
        judge = True
        t = 0
        for i in range(12):
            aaa = i % 2 + 1
            date = soup.find_all(class_=f'a-center w-space')
            oneday = date[i].text[:10]
            oneday = oneday.replace('/', '-')
            today = str(datetime.date.today())
            #today = str(datetime.date(2021, 4, 22))
            #print(today, oneday)
            if oneday == today:
                code = soup.find_all(class_=f'a-center')
                #print(3*i+1)
                code = code[3*(i+2)].text
                t += 1
                print(code,today)
                yield (code, today)

    def insert_new_brands_to_db(self,db_file_name):
      conn = sqlite3.connect(db_file_name)
      with conn:
        sql = 'INSERT INTO delete_brands(code,date) VALUES(?,?)'
        conn.executemany(sql, self.new_brands_generator())

    def get4data(self):
        code = list(self.new_brands_generator())
        #print(code)
        ncode = []
        for i in range(len(code)):
            ncode.append (int(code[i][0]))

        for j in ncode:
            conn = sqlite3.connect("/Users/tatsumiryou/sqlite.db")
            with conn:
                sql = f'DELETE FROM brand WHERE code = {j}'
                conn.execute(sql)






