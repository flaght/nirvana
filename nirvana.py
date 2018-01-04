#!/usr/bin/env python
# coding=utf-8

from order import Order, CombOffset, OrderPrice, Direction, OrderStatus
from account import Account
from daily_record import DailyRecord,SummaryRecord
import numpy as np
from collections import OrderedDict
import os
import pandas as pd

DEFAULT_CASH = 1000000
class Nirvana(object):

    __strategy_id = 1002
    __account_id = 10001
    def __init__(self):

        self.__limit_order = OrderedDict() # 委托单队列
        self.__long_volumes = OrderedDict() # 多头持仓情况


        self.__history_limit_order =  OrderedDict() # 历史委托单
        self.__history_limit_volumes = OrderedDict() # 历史成交记录

        self.__trader_record = OrderedDict() # 交易记录存储

        self.__account = Account()
        self.__account.set_account_id(self.__account_id)
        self.__account.set_init_cash(DEFAULT_CASH)

        self.__history_file = OrderedDict() 


    def init_read_lhb(self, dir):
        for path, dirs, fs, in os.walk(dir):
            symbol_list = []
            for f in fs:
                symbol_list.append(os.path.join(path, f))
                # self.__history_file[os.path.split()[-1]] = 
            self.__history_file[os.path.split(path)[-1]] = symbol_list


if __name__ == '__main__':
    nirvana = Nirvana()
    nirvana.init_read_lhb('./output/')
