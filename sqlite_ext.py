# -.- coding:utf-8 -.-

"""
Created on 2016年11月6日

@author: kerry
"""

import sqlite3
import os


class SQLiteExt(object):
    def __init__(self, name, type, timeout=5):
        """

        Args:
            name: 文件完整路径名
            type: 0 创建在硬盘上 1.创建在内存里
        """

        self.name = name
        self.type = type
        self.timeout = timeout
        self.conn = None

        self.__conection_sql()

    def __conection_sql(self):
        try:
            self.conn = sqlite3.connect(self.name, self.timeout)
            if os.path.exists(self.name) and os.path.isfile(self.name):
                self.type = 0
            else:
                self.conn = sqlite3.connect(':memory:')
                self.type = 1

        except Exception, e:
            mlog.log().error('sqlite3 error:%s' % e)
            return

    def __get_cursor(self):
        """该方法是获取数据库的游标对象，参数为数据库的连接对象
        如果数据库的连接对象不为None，则返回数据库连接对象所创
        建的游标对象；否则返回一个游标对象，该对象是内存中数据
        库连接对象所创建的游标对象"""
        if self.conn is not None:
            return self.conn.cursor()
        else:
            return self.__get_conn('').cursor()

    def __get_conn(self, path):
        """获取到数据库的连接对象，参数为数据库文件的绝对路径
        如果传递的参数是存在，并且是文件，那么就返回硬盘上面改
        路径下的数据库文件的连接对象；否则，返回内存中的数据接
        连接对象"""
        conn = sqlite3.connect(path)
        if os.path.exists(path) and os.path.isfile(path):
            mlog.log().info('硬盘上面:[{}]'.format(path))
            return conn
        else:
            conn = None
            mlog.log().info('内存上面:[:memory:]')
            return sqlite3.connect(':memory:')

    def __close_all(self, cur):
        '''关闭数据库游标对象和数据库连接对象'''
        try:
            if cur is not None:
                cur.close()
        finally:
            if cur is not None:
                cur.close()

    def drop_table(self,table):
        """如果表存在,则删除表，如果表中存在数据的时候，使用该
        方法的时候要慎用！"""
        if table is not None and table != '':
            sql = 'DROP TABLE IF EXISTS ' + table
            cur = self.__get_cursor()
            cur.execute(sql)
            self.conn.commit()
            self.__close_all(cur)
        else:
            mlog.log().error('the [{}] is empty or equal None!'.format(table))

    def check_table(self, table):
        """检测此表是否存在"""
        if table is not None and table != '':
            sql = "select name from sqlite_master where type='table' and name = '" + table + "' order by name"
            #sql = "SELECT name FROM sqlite_master WHERE type='table' and name = 'crawl_info'"
            if  len(self.fetch(sql)) > 0:
                return True
        return False

    def create_table(self, sql):
        if sql is not None and sql != '':
            cur = self.__get_cursor()
            cur.execute(sql)
            self.conn.commit()
            self.__close_all(cur)
        else:
            mlog.log().error('the [{}] is empty or equal None!'.format(sql))


    def save(self, sql, data):
        '''插入数据'''
        if sql is not None and sql != '':
            if data is not None:
                cur = self.__get_cursor()
                for d in data:
                    cur.execute(sql, d)
                    self.conn.commit()
                self.__close_all(cur)
        else:
            mlog.log().error('the [{}] is empty or equal None!'.format(sql))

    def fetch(self,sql):
        queue = []
        if sql is not None and sql != '':
            cur = self.__get_cursor()
            cur.execute(sql)
            r = cur.fetchall()
            if len(r) > 0:
                for e in range(len(r)):
                    queue.append(r[e])
            return queue
        else:
            mlog.log().error('the [{}] is empty or equal None!'.format(sql))
            return None



def main():
    sqlmgr = SQLiteExt("./text.db",  0)

    try:
        create_table_sql = '''CREATE TABLE `search` (
                        `id` BIGINT NOT NULL,
                        `uid` BIGINT NULL,
                        `title` VARCHAR(128) NULL,
                        `text` VARCHAR(40960) NULL,
                        `created_at` INT NULL,
                        `retweet_count` INT NULL,
                        `reply_count` INT NULL,
                        `fav_count` INT NULL,
                        `retweet_id` INT NULL,
                        `type` INT NULL,
                        `source_link` VARCHAR(256),
                        `edited_at` INT NULL,
                        `pic` VARCHAR(256) NULL,
                        `target` VARCHAR(256) NULL,
                        `source` VARCHAR(256) NULL,
                        PRIMARY KEY (`id`));'''

        sqlmgr.create_table(create_table_sql)
    except Exception,e:
        mlog.log().error("Create table failed")


("\n"
 "    save_sql = '''INSERT INTO search values (?, ?, ?, ?, ?, ?)'''\n"
 "    data = [(11, 'Hongten', 's', 20, 'guangdong', '13423****62'),\n"
 "            (12, 'Tom', 's', 22, 'meiguo', '15423****63'),\n"
 "            (33, 'Jake', 't', 18, 'dong123', '18823****87'),\n"
 "            (14, 'Cate', 't', 21, 'zhou', '14323****32')]\n"
 "\n"
 "    sqlmgr.save(save_sql, data)\n"
 "    ")

if __name__ == '__main__':
    main()
