#!/usr/bin/env python
# coding=utf-8

import datetime
import json
import sys
import pandas as pd
from mlog import MLog
from crawler.xq_lhb_client import XQLHBClient
from strategy.nirvana import Nirvana
from db.data_source import GetDataEngine

class NirvanaRun(object):

    def __init__(self):
        self.__end_date = int(datetime.datetime.now().strftime("%Y%m%d"))
        # self.__end_date = 20180326
        self.clinet = XQLHBClient(0, 0, 1)
        self.__strategy = Nirvana(None,0)
    
    def start(self):
        # stock_sets = []
        symbols = ''
        lhb_sets = self.clinet.run_crawler_lhb(self.__end_date)
        for lhb in lhb_sets:
            signal, symbol = self.__strategy.on_lhb_event(lhb_sets[lhb], self.__end_date)
            print (signal, symbol)
            if signal:
                symbols += '\''
                symbols += symbol[2:len(symbol)]
                symbols += '\''
                symbols += ','
                # stock_sets.append(symbol)
        df = self.get_symbol_info(symbols[0:-1])
        df['TRADEDATE'] = self.__end_date
        df = df.rename(columns={'SYMBOL':'股票代码','KEYNAME':'板块','SESNAME':'股票名称','TRADEDATE':'交易日'})
        df.to_html(str(self.__end_date) + '.html') 

    def get_symbol_info(self, symbols):
        sql_pe = 'select B.SYMBOL,C.KEYNAME,B.SESNAME from TQ_SK_BASICINFO AS B JOIN TQ_COMP_BOARDMAP AS C ON  B.SECODE = C.SECODE where B.SYMBOL in (' + str(symbols) + ') and SETYPE = \'101\' AND (C.KEYCODE = \'GE002\' or C.KEYCODE = \'SZ002\' or C.KEYCODE = \'MB001\')'
        print sql_pe
        data_engine = GetDataEngine('DNDS')
        df = pd.read_sql(sql_pe, data_engine)
        return df


if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf8')
    MLog.config(name='nirvana_run')
    nirvana_run = NirvanaRun()
    nirvana_run.start()
