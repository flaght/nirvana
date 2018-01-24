#!/usr/bin/env python
# coding=utf-8
from sqlite_manage_model import SQLLiteStorage
import time
import json
import os

class DataSets(object):

    def __init__(self):
        self.__db_name = 'bize.db'


    def __create_class(self, db_engine):
        if not db_engine.check_table('class'):
            create_table_sql = '''CREATE TABLE `class` (
                        `xid` BIGINT NULL,
                        `name` VARCHAR(128) NULL,
                        `update_time` VARCHAR(128) NULL,
                        PRIMARY KEY (`xid`));'''
            db_engine.create_table(create_table_sql)

    def __create_bizs(self, db_engine):
        if not db_engine.check_table('bize') :
            create_table_sql = '''CREATE TABLE `bize` (
                        `xid` BIGINT NULL,
                        `name` VARCHAR(128) NULL,
                        `update_time` VARCHAR(128) NULL,
                        PRIMARY KEY (`xid`));'''
            db_engine.create_table(create_table_sql)

    def __save_bizs_data(self):
        table = 'bize'
        sql = '''INSERT OR REPLACE INTO `''' + table + '''` values (?, ?, ?)'''
        return sql
        # db_engine.save_data(sql, data)

    def __save_bizs_class(self):
        table = 'class'
        sql = '''INSERT OR REPLACE INTO `''' + table + '''` values (?, ?, ?)'''
        return sql

    def __bize_parser(self, all_text, data, tchg):
        ob = json.loads(all_text)
        dict = {}
        c_dict = {}

        bize_buy = ob.get('tqQtBizunittrdinfoBuyList')
        bize_sale = ob.get('tqQtBizunittrdinfoSaleList')
        for buy in bize_buy:
            bize_code = buy.get('bizsunitcode')
            bize_name = buy.get('bizsunitname')
            chg_code = buy.get('chgtype')
            chg_name = buy.get('typedesc')

            bize = (int(bize_code),bize_name,time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))) 
            chg = (int(chg_code),chg_name,time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))

            dict[bize_code] = bize
            c_dict[chg_code] = chg
            # data.append(bize)
        for sale in bize_sale:
            bize_code = sale.get('bizsunitcode')
            bize_name = sale.get('bizsunitname')
            chg_code = sale.get('chgtype')
            chg_name = sale.get('typedesc')
            bize = (int(bize_code), bize_name,time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
            chg = (int(chg_code),chg_name,time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))

            dict[bize_code] = bize
            c_dict[chg_code] = chg
            # data.append(bize)
        for k,v in dict.items():
            data.append(dict[k])

        for k,v in c_dict.items():
            tchg.append(c_dict[k])
            
    def calc_bizs_from(self, dir):
        db_engine = SQLLiteStorage(self.__db_name, 0)
        self.__create_bizs(db_engine)
        self.__create_class(db_engine)
        data = []
        tchg = []
        for path, dirs, fs in os.walk(dir):
            for f in fs:
                file_object = open(os.path.join(path, f))
                all_text = file_object.read()
                self.__bize_parser(all_text, data, tchg)

        db_engine.save_data(self.__save_bizs_data(), data)
        db_engine.save_data(self.__save_bizs_class(), tchg)

if __name__ == '__main__':
    data_set = DataSets()
    data_set.calc_bizs_from('../../data/nirvana/xq/')

