#!/usr/bin/env python
# coding=utf-8

from collections import OrderedDict
import os
import sys
import pandas as pd
import tushare as ts
import json
from nirvana import Nirvana

class LookBack(object):

    __strategy_id = 1002
    __account_id = 10001
    def __init__(self, start_date, end_date):

        self.history_file = OrderedDict() 
        self.__trade_date = []

        self.__init_trade(start_date, end_date)

        self.__working_limit_order = OrderedDict()

        self.__strategy = Nirvana(self.__working_limit_order)

    def init_read_lhb(self, dir):
        for path, dirs, fs, in os.walk(dir):
            if len(fs) > 0:
                symbol_list = []
                for f in fs:
                    symbol_list.append(os.path.join(path, f))
                # self.history_file[os.path.split()[-1]] = 
                self.history_file[int(os.path.split(path)[-1])] = symbol_list

        # 排序
        self.history_file = OrderedDict(sorted(self.history_file.items(), key=lambda t: t[0]))


    def __init_trade(self,start_date, end_date):
        trade_date = ts.trade_cal()
        for indexs in trade_date.index:
            date_u = int(trade_date.loc[indexs].values[0].replace('-',''))
            if start_date <=  date_u and end_date >= date_u:
                self.__trade_date.append(date_u)
                
    def __loop_back(self, date, lhb_set):
        for lhb in lhb_set:
            file_object = open(lhb)
            json_ob = json.loads(file_object.read())
            self.__strategy.on_lhb_event(json_ob, date)
            file_object.close()


    def start(self):
        for date in self.__trade_date:
            # 读取行情，撮合价格成交
            if self.history_file.has_key(date):
                lhb_set = self.history_file[date]
                self.__loop_back(date, lhb_set)

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    lb = LookBack(20160102,20180102)
    lb.init_read_lhb('./output/')
    lb.start()
