import datetime
from get_dataa.data_bycsv import get_todata
from get_dataa.del_add_brands import add_brand,del_brand
from get_dataa.apply_divide_union_data import change_data
from get_dataa.split_mix import dive_union
from decide_Brand.look_data import look_sales
from slack.today_trade_his import check_message
from Today_trade.today_stra import get_ready


def operate():
    today = datetime.date.today()
    getoday = get_todata('/Users/tatsumiryou/sqlite.db',today)
    try:                    #平日
        getoday.getcsv()     #今日の株価を取る
    except:                  #土日祝はここにくる
        a = look_sales("/Users/tatsumiryou/sqlite.db", 300000, 120, 120, 125, 10, 57)
        a.check_it_out()       #決算情報を取ってlookbrandを更新する

    addbrand = add_brand()
    addbrand.get4data()
    delbrand = del_brand()
    delbrand.get4data()
    changedata = change_data()
    changedata.apply_divide_union_data('/Users/tatsumiryou/sqlite.db',today)

    check_message()     #今日の売り買いの記録をslackで受信

    stra = get_ready('/Users/tatsumiryou/sqlite.db',today)
    stra.make_stra()     #戦略のパラメーターはtoday_stra.pyで変更する。



if __name__ == '__main__':
    operate()