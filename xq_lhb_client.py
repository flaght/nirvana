# -*- coding: utf-8 -*-
import tushare as ts
from client import Client
import json
import os

class XQLHBClient(object):
    
    def __init__(self, start_date, end_date):
        self.__base_list = 'https://xueqiu.com/stock/f10/bizunittrdinfo.json'
        self.__base_detail = 'https://xueqiu.com/stock/f10/bizunittrdinfo.json' 
        self.__trade_date = []
        self.__init_trade(start_date, end_date)
        self.__client = Client()

    def __init_trade(self,start_date, end_date):
        trade_date = ts.trade_cal()
        for indexs in trade_date.index:
            date_u = int(trade_date.loc[indexs].values[0].replace('-',''))
            if start_date <=  date_u and end_date >= date_u:
                self.__trade_date.append(date_u)

    def __crawler_lhb_detail(self, symbol, trade_date):
        url = self.__base_detail + '?symbol=' + symbol + '&date=' + str(trade_date)
        print url
        lhb_detail_obj = json.loads(self.__client.request(url))
        if lhb_detail_obj is None:
            return
        lhb_detail = lhb_detail_obj.get('detail')
        if lhb_detail is None:
            return

        sub_path = '/kywk/strategy/nirvana/output/' + str(trade_date) + '/'
        filename = sub_path + symbol + '.json'
        
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        file_object = open(filename, 'w')
        file_object.write(json.dumps(lhb_detail))
        file_object.close()
        # skdaily_price = lhb_detail.get('tqQtSkdailyprice')
        # biz_buy = lhb_detail.get('tqQtBizunittrdinfoBuyList')
        # biz_sale = lhb_detail.get('tqQtBizunittrdinfoSaleList')


    def __crawler_lhb_list(self, trade_date):
        url = self.__base_list + '?date=' + str(trade_date)
        lhb_obj = json.loads(self.__client.request(url))
        lhb_list = lhb_obj.get('list')
        if lhb_list is None:
            return
        for lhb in lhb_list:
            symbol = lhb.get('symbol')
            self.__crawler_lhb_detail(symbol, trade_date)


    def crawler_lhb(self):
        for td in self.__trade_date:
            self.__crawler_lhb_list(td)

if __name__ == "__main__":
    client = XQLHBClient(20160102,20180102)
    client.crawler_lhb()
