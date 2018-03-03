#!/usr/bin/env python
# coding=utf-8

import datetime
import json
import sys
from mlog import MLog
from crawler.xq_lhb_client import XQLHBClient
from strategy.nirvana import Nirvana

class NirvanaRun(object):

    def __init__(self):
        # self.__end_date = int(datetime.datetime.now().strftime("%Y%m%d"))
        self.__end_date = 20180302
        self.clinet = XQLHBClient(0, 0, 1)
        self.__strategy = Nirvana(None,0)
    
    def start(self):
        stock_sets = []
        lhb_sets = self.clinet.run_crawler_lhb(self.__end_date)
        for lhb in lhb_sets:
            signal, symbol = self.__strategy.on_lhb_event(lhb_sets[lhb], self.__end_date)
            if signal:
                stock_sets.append(symbol)

        print stock_sets

if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf8')
    MLog.config(name='nirvana_run')
    nirvana_run = NirvanaRun()
    nirvana_run.start()
