#!/usr/bin/env python
# coding=utf-8
from client import Client
import icu
import base64
import zlib
import time
import os
import json
import datetime
import pandas as pd
from sqlite_manage_model import SQLLiteStorage

class THSLHBClient(object):
    def __init__(self, type=1):
        self.__sbcs_url = 'http://data.10jqka.com.cn/ifmarket/lhbyyb/type/1/tab/sbcs/field/sbcs/sort/desc/page/'
        self.__sbcs_list = []

        self.__zjsl_url = 'http://data.10jqka.com.cn/ifmarket/lhbyyb/type/1/tab/zjsl/field/zgczje/sort/desc/page/'
        self.__zjsl_list = []

        self.__btcz_url = 'http://data.10jqka.com.cn/ifmarket/lhbyyb/type/1/tab/btcz/field/xsjs/sort/desc/page/'
        self.__btcz_list = []

        self.__orgcode_url = 'http://data.10jqka.com.cn/ifmarket/xtyyb/orgcode/'
        self.__orgcode_list = []

        self.__market_lhb_url = 'http://data.10jqka.com.cn/market/lhbyyb/orgcode/'
        self.__market_lhb_list = []

        if type == 1 or type == 0:
            self.__init_lhburl()
        elif type == 2:
            self.__init_detailurl()
        elif type == 3:
            self.__init_marketurl()

        self.__client = Client('data.10jqka.com.cn')
        self.__detector = icu.CharsetDetector()

    def get_bize_info(self, table):
        sql = '''select xid,name,jianpin from `''' + table + '''`'''
        return sql

    def __init_marketurl(self):
        db_engine = SQLLiteStorage('bize.db', 0)
        sql = self.get_bize_info('bize')
        self.__market_lhb_list = db_engine.get_data(sql)

    def __init_detailurl(self):
        filename = './ths_lhb.csv'
        df = pd.read_csv(filename)
        for indexs in df.index:
            bize_code = df.loc[indexs].values[0]
            for i in range(50):
                orgcode_url = self.__orgcode_url + str(bize_code) + '/field/zmgp/sort/desc/page/' + str(i+1)
                self.__orgcode_list.append(orgcode_url)

    def __init_lhburl(self):
        for i in range(15):
            sbcs_url = self.__sbcs_url + str(i+1)
            zjsl_url = self.__zjsl_url + str(i+1)
            self.__sbcs_list.append(sbcs_url)
            self.__zjsl_list.append(zjsl_url)

        for i in range(14):
            btcz_url = self.__btcz_url + str(i+1)
            self.__btcz_list.append(btcz_url)
    
    def __crawler_lhb(self, url, szt, xid = 0,code=''):
        print url
        html = self.__client.request(url)
        self.__detector.setText(html)
        match = self.__detector.detect()
        charset_name = match.getName()
        obj = {'charset': charset_name,
               'xid':xid,
               'content': base64.b32encode(zlib.compress(html))}

        dir = '../../data/nirvana/ths/' + szt
        if not os.path.exists(dir):
            os.makedirs(dir)
        uqiue_name = str(time.time()).split('.')
        uqiue_sub_name = str(datetime.datetime.now().microsecond)
        filename = dir + '/' + str(uqiue_name[0]) + str(uqiue_name[1]) + uqiue_sub_name +'.json'
        print (filename)
        with open(filename, 'wb') as f:
            f.write(json.dumps(obj))

    def start(self):
        for sbcs_url in self.__sbcs_list:
            self.__crawler_lhb(sbcs_url, 'sbcs')

        for zjsl_url in self.__zjsl_list:
            self.__crawler_lhb(zjsl_url, 'zjsl')

        for btcz_url in self.__btcz_list:
            self.__crawler_lhb(btcz_url, 'btcz')

        for orgcode_url in self.__orgcode_list:
            self.__crawler_lhb(orgcode_url, 'orgcode')
 
        for bize in self.__market_lhb_list:
            url = self.__market_lhb_url + str(bize[2])
            self.__crawler_lhb(url,'market',bize[0], bize[2])

    def dump(self):
        for sbcs_url in self.__sbcs_list:
            print (sbcs_url)

        for zjsl_url in self.__zjsl_list:
            print (zjsl_url)

        for btcz_url in self.__btcz_list:
            print (btcz_url)

    
    
if __name__ == "__main__":
    ths_client = THSLHBClient(3)
    ths_client.start()

