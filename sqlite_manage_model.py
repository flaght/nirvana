# -.- coding:utf-8 -.-
"""
Created on 2016年11月6日

@author: kerry
"""

from sqlite_ext import SQLiteExt
import threading
import os

class SQLLiteStorage():

    def __init__(self,name,type,timeout = 5):
        # self.detector = icu.CharsetDetector()
        self.engine = SQLiteExt(name,type,timeout)
        self.name = name
        self.wait_queue = []

    def create_table(self,crate_table_sql, type = 1):
        """

        Args:
            crate_table_sql: 创建表的SQL语句
            type: 0 删除原有的 1.保留原有的

        Returns:

        """
        if type == 0:
            drop_table_sql =  'DROP TABLE IF EXISTS ' + self.table
            self.engine.drop_table(drop_table_sql)
        try:
            self.engine.create_table(crate_table_sql)
        except Exception, e:
            print('create_table error:%s' % e)


    def check_table(self, table_name):
        return self.engine.check_table(table_name)


    def save_data(self,sql,data):
        self.wait_queue.append({'db': sql,
                                'data': data})
        self.run()

    def run(self):
        try:
            if len(self.wait_queue):
                item = self.wait_queue.pop(0)
                self.engine.save(item['db'],
                                 item['data'])
        except Exception, e:
            print('save error:%s' % e)
            pass


