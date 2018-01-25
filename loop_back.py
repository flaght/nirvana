#!/usr/bin/env python
# coding=utf-8

from collections import OrderedDict
import os
import sys
import pandas as pd
import tushare as ts
import json
from mlog import MLog
from db.data_source import GetDataEngine
from td_base.daily_price import DailyPrice
from td_base.order import OrderStatus, CombOffset, OrderPrice
from td_base.volume import Volume
from strategy.nirvana import Nirvana
import time


class LookBack(object):
    """Summary of class here.
        回测类

    Attributes:
        start_date: 回测开始时间
        end_date:回测结束时间
    """

    __strategy_id = 1002
    __account_id = 10001

    def __init__(self, start_date, end_date):
        """Inits LookBack with blah."""

        self.history_file = OrderedDict()  # 龙虎榜历史交易信息文件
        self.__trade_date = []  # 交易日

        self.__init_trade(start_date, end_date)

        self.__limit_order = OrderedDict()  # 限价单
        self.__cancel_order = OrderedDict()  # 撤销单
        self.__volume_order = OrderedDict()  # 成交单

        self.__working_limit_order = OrderedDict()  # 正在委托订单
        self.working_limit_volume = OrderedDict()  # 持有持仓

        self.__strategy = Nirvana(self.__working_limit_order)

        self.st_stock = OrderedDict()  # 存储ST,*ST,S股票
        
        self.__data_engine = GetDataEngine('DNDS')  # 数据库连接

    def __set_st_stock(self, date, symbol, name):
        """Performs operation __set_st_stock blah.
            存储ST,*ST, S股票信息


        Attributes:
            date: 时间
            symbol: 标的
            name: 标的名称
        """
        re_date = int(date.replace('-', ''))
        if self.st_stock.has_key(re_date):
            stock_dict = self.st_stock[re_date]
        else:
            stock_dict = OrderedDict()

        stock_dict[symbol] = name

        self.st_stock[re_date] = stock_dict

    def init_st_stock(self, filename):
        """Performs operation init_st_stock blah.
            从文件中读取ST,*ST,S 股票

        Attributes:
            filename:存储ST,*ST,S股票文件
        """
        st_stock = pd.read_csv(filename)

        for index in st_stock.index:
            df_data = st_stock.loc[index].values
            date = df_data[1]
            symbol = str(df_data[2].split('.')[0])
            name = str(df_data[5])
            self.__set_st_stock(date, symbol, name)

    def is_st_stock(self, date, symbol):
        """Performs operation is_st_stock blah.
            判断当前日期时候该股票是否为ST,*ST,S股票

        Attributes:
            date:交易日期
            symbol:交易标的
        """

        if self.st_stock.has_key(date):
            stock_dict = self.st_stock[date]
            if stock_dict.has_key(symbol):
                return True
        return False

    def init_read_lhb(self, dir):
        """Performs operation init_read_lhb blah.
            初始化读取龙虎榜数据文件。

        Attributes:
            dir:存储龙虎榜数据文件的目录
        """
        for path, dirs, fs, in os.walk(dir):
            if len(fs) > 0:
                symbol_list = []
                for f in fs:
                    symbol_list.append(os.path.join(path, f))
                self.history_file[int(os.path.split(path)[-1])] = symbol_list

        # 排序
        self.history_file = OrderedDict(sorted(self.history_file.items(), key=lambda t: t[0]))

    def __init_trade(self, start_date, end_date):
        """Performs operation init_read_lhb blah.
            初始化回测时间段内的交易日,从tushare获取交易日
        Attributes:
            start_date: 回测开始时间
            end_date: 回测结束时间
        """
        trade_date = ts.trade_cal()
        for index in trade_date.index:
            date_u = int(trade_date.loc[index].values[0].replace('-', ''))
            f_u = int(trade_date.loc[index].values[1])
            if (start_date <= date_u <= end_date) and (f_u == 1):
                self.__trade_date.append(date_u)

    def __loop_back(self, date, lhb_set):
        """Performs operation __loop_back blah.
            读取龙虎榜文件的JSON内容
        Attributes:
            date: 指定交易日
            lhb_set:指定交易日的龙虎榜信息集合
        """
        for lhb in lhb_set:
            file_object = open(lhb)
            json_ob = json.loads(file_object.read())
            self.__strategy.on_lhb_event(json_ob, date)
            file_object.close()

    def __is_new_shares(self, today, list_date):
        """Performs operation __is_new_shares blah.
            判断是否是次新股
        Attributes:
            today:指定交易日
            list_date:股票上市日期
        """

        min_time = 30 * 60 * 60 * 24
        max_time = 345 * 60 * 60 * 24
        diff_time = time.mktime(time.strptime(str(today), '%Y%m%d')) - time.mktime(time.strptime(str(list_date),'%Y%m%d'))
        if diff_time > min_time:
            return True
        if min_time <= diff_time <= max_time:
            return True
        return False

    def get_data_daily_price(self, symbols, date):
        """Performs operation get_data_daily_price blah.
            读取当日指定股票的日行情数据

        Attributes:
            symbols:交易标的代码集
            date:指定交易日
        """
        sql_daily_price = 'select S.ID, B.SYMBOL, S.TRADEDATE,S.LCLOSE,S.TOPEN, S.TCLOSE,S.THIGH,S.TLOW,S.AVGPRICE,S.VOL,S.AMOUNT,B.LISTDATE from dnds.dbo.TQ_QT_SKDAILYPRICE AS S JOIN dnds.dbo.TQ_SK_BASICINFO as B on S.SECODE = B.SECODE and B.symbol IN(' + symbols + ') and S.TRADEDATE = ' + str(
            date)
        daily_price_list = {}
        df = pd.read_sql(sql_daily_price, self.__data_engine)
        for index in df.index:
            data = df.loc[index].values
            daily_price = DailyPrice()
            daily_price.df_parser(data)
            # if self.__is_new_shares(date, daily_price.list_date()):
            daily_price_list[daily_price.symbol()] = daily_price
        return daily_price_list

    def on_get_daily_price(self, date):
        """Performs operation on_get_daily_price blah.
            根据委托单和持有单读取行情

        Attributes:
            date:指定交易日
        """
        symbols = ''
        for v, value in self.__working_limit_order.items():
            # 检测是否是st 股票
            # if self.is_st_stock(date, value.symbol()[2:]):
            #    MLog.write().debug('symbol:%s is ST STOCK on %d'%(str(value.symbol()[2:]),date))
            #    continue

            symbols += '\''
            symbols += value.symbol()[2:]
            symbols += '\''
            symbols += ','

        for key, value in self.working_limit_volume.items():
            symbols += '\''
            symbols += value.symbol()[2:]
            symbols += '\''
            symbols += ','

        if len(symbols) == 0:
            return

        return self.get_data_daily_price(symbols[0:-1], date)

    def cross_limit_order(self, date, daily_price_list):
        """Performs operation on_get_daily_price blah.
            遍历所有的限价单,根据当日行情数据进行成交撮合

        Attributes:
            date:指定交易日
            daily_price_list:行情数据列表
        """

        for order_id, order in self.__working_limit_order.items():
            if order.status() == OrderStatus.not_traded:
                # 行情不存在
                if not daily_price_list.has_key(order.symbol()[2:]):
                    continue

                daily_price = daily_price_list[order.symbol()[2:]]
                # 停盘
                is_used = daily_price.is_use
                if is_used == 0:  # 停盘
                    continue

                # 一字跌停不能买入， 一字跌停不能卖出
                if order.comb_offset_flag() == CombOffset.open and is_used == -1:  # 开仓
                    continue

                if order.comb_offset_flag() == CombOffset.close and is_used == -2:  # 平仓
                    continue

                # 今天未有成交
                if daily_price.vol() == 0.00:
                    continue

                if daily_price.vol() < order.vol():  # 交易量不满足
                    continue

                if not daily_price.is_use:  # 停牌或涨跌停
                    continue

                if self.is_st_stock(date, order.symbol()):  # ST股票不参与交易
                    continue

                if order_id in self.__working_limit_order:
                    del self.__working_limit_order[order_id]

                order.set_status(OrderStatus.entrust_traded)

                order.dump()

                # 委托成功信息推送到策略
                self.__strategy.on_order(order)

                order.set_status(OrderStatus.all_traded)
                self.__strategy.on_order(order)

                vol = Volume()
                vol.create_trader_id()
                vol.set_symbol(order.symbol())
                vol.set_direction(order.direction())
                vol.set_comb_offset_flag(order.comb_offset_flag())
                if order.order_price_type() == OrderPrice.avg_price:  # 建仓以均价进行撮合
                    vol.set_limit_price(daily_price.avg_price())
                else:
                    vol.set_limit_price(order.limit_price())
                vol.set_amount(order.amount())
                vol.set_min_volume(order.min_volume())
                vol.set_create_time(date)

                vol.set_stamp(order.stamp_ratio())
                vol.set_commission(order.commission_ratio())
                vol.set_transfer(order.transfer_ratio())

                vol.set_order_id(order.order_id())
                self.__volume_order[vol.trader_id()] = vol

                if order.comb_offset_flag() == CombOffset.open:  # 开仓
                    self.working_limit_volume[vol.trader_id()] = vol
                else:
                    if self.working_limit_volume.has_key(order.hold_volume_id()):
                        del self.working_limit_volume[order.hold_volume_id()]
                self.__strategy.on_volume(vol, order)

    def start(self):
        """Performs operation start blah.
            启动回测
        Attributes:
        """

        for date in self.__trade_date:
            MLog.write().info('trader starting date：%d========>' % (date))
            MLog.write().debug('get %d daily_price========>' %(date))

            # 根据委托单和持有单读取行情
            daily_price_list = self.on_get_daily_price(date)
           
            if daily_price_list is not None and len(daily_price_list) > 0:

                # 推送给策略，对持仓做操作,A股市场T+1，可当天卖当天买，不能当天买再当天卖
                MLog.write().debug('push daily_price strategy========>')
                self.__strategy.on_market_data(date, daily_price_list)
                # 读取行情，撮合成交
                MLog.write().debug('cross_limit_order ========>')
                self.cross_limit_order(date, daily_price_list)
                # self.__working_limit_order.clear() # 是否清理掉当天的委托单
                # 当天结算
                MLog.write().debug('today calc settle=========>')
                self.__strategy.calc_settle(date, daily_price_list)
            # 计算当日龙虎榜
            MLog.write().debug('cal today lhb =========>')
            if self.history_file.has_key(date):
                lhb_set = self.history_file[date]
                self.__loop_back(date, lhb_set)
            MLog.write().debug('\n')

    def calc_result(self):
        self.__strategy.calc_result()


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    MLog.config(name='nirvana')
    lb = LookBack(20170104,20180105)
    # lb.init_st_stock('./file/market_st.csv')
    lb.init_read_lhb('../../data/nirvana/xq/')
    lb.start()
    lb.calc_result()
