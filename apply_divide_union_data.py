import datetime
import sqlite3

class change_data:

    def apply_divide_union_data(self,db_file_name,date_of_right_allotment):
        conn = sqlite3.connect(db_file_name)

        # date_of_right_allotment 以前の分割・併合データで未適用のものを取得する
        sql = """
        SELECT 
            d.code, d.date_of_right_allotment, d.before, d.after
        FROM 
            divide_union_data1 AS d
        WHERE
            d.date_of_right_allotment < ?
            AND NOT EXISTS (
                SELECT 
                    * 
                FROM 
                    applied_divide_union_data1  AS a
                WHERE 
                    d.code = a.code
                    AND d.date_of_right_allotment = a.date_of_right_allotment
                ) 
        ORDER BY 
            d.date_of_right_allotment
        """


        cur = conn.execute(sql, (date_of_right_allotment,))
        divide_union_data = cur.fetchall()

        with conn:
            conn.execute('BEGIN TRANSACTION')
            for code, date_of_right_allotment, before, after in divide_union_data:
                print(code, date_of_right_allotment, before, after)
                rate = before / after
                inv_rate = 1 / rate

                conn.execute(
                    'UPDATE prices1 SET '
                    ' open = open * :rate, '
                    ' high = high * :rate, '
                    ' low = low  * :rate, '
                    ' close = close * :rate, '
                    ' volume = volume * :inv_rate '
                    'WHERE code = :code '
                    '  AND date <= :date_of_right_allotment',
                    {'code': code,
                     'date_of_right_allotment': date_of_right_allotment,
                     'rate': rate,
                     'inv_rate': inv_rate})

                conn.execute(
                    'INSERT INTO '
                    'applied_divide_union_data1(code, date_of_right_allotment) '
                    'VALUES(?,?)',
                    (code, date_of_right_allotment))

if __name__ == '__main__':
    date = datetime.date(2022,4,7)  #この日より後の分割統合を確かめれる
    changedata = change_data()
    changedata.apply_divide_union_data('/Users/tatsumiryou/sqlite.db',date)
