#!/usr/bin/env python
# coding=utf-8

from collections import OrderedDict
import os
import sys
import pandas as pd
import tushare as ts
import json
from mlog import  MLog
from data_source import GetDataEngine
from daily_price import DailyPrice
from order import Direction, OrderStatus, CombOffset, OrderPrice
from volume import Volume
from nirvana import Nirvana
import config

class LookBack(object):
    __strategy_id = 1002
    __account_id = 10001

    def __init__(self, start_date, end_date):

        self.history_file = OrderedDict()
        self.__trade_date = []

        self.__init_trade(start_date, end_date)

        self.__limit_order = OrderedDict()  # 限价单
        self.__cancel_order = OrderedDict()  # 撤销单
        self.__volume_order = OrderedDict()  # 成交单

        self.__working_limit_order = OrderedDict()  # 正在委托订单
        self.working_limit_volume = OrderedDict()  # 持有持仓

        self.__strategy = Nirvana(self.__working_limit_order)

        self.__data_engine = GetDataEngine('DNDS')

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

    def __init_trade(self, start_date, end_date):
        trade_date = ts.trade_cal()
        for indexs in trade_date.index:
            date_u = int(trade_date.loc[indexs].values[0].replace('-', ''))
            if start_date <= date_u <= end_date:
                self.__trade_date.append(date_u)

    def __loop_back(self, date, lhb_set):
        for lhb in lhb_set:
            file_object = open(lhb)
            json_ob = json.loads(file_object.read())
            self.__strategy.on_lhb_event(json_ob, date)
            file_object.close()

    def get_data_daily_price(self, symbols, date):
        sql_daily_price = 'select S.ID, B.SYMBOL, S.TRADEDATE,S.LCLOSE,S.TOPEN, S.TCLOSE,S.THIGH,S.TLOW,S.AVGPRICE,S.VOL,S.AMOUNT from dnds.dbo.TQ_QT_SKDAILYPRICE AS S JOIN dnds.dbo.TQ_SK_BASICINFO as B on S.SECODE = B.SECODE and B.symbol IN(' + symbols + ') and S.TRADEDATE = ' + str(
            date)
        daily_price_list = {}
        df = pd.read_sql(sql_daily_price, self.__data_engine)
        for indexs in df.index:
            data = df.loc[indexs].values
            daily_price = DailyPrice()
            daily_price.df_parser(data)
            daily_price_list[daily_price.symbol()] = daily_price
        return daily_price_list

    # 根据委托单和持有单读取行情
    def on_get_daily_price(self, date):
        symbols = ''
        for v, value in self.__working_limit_order.items():
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
        # 遍历所有的限价单
        for order_id, order in self.__working_limit_order.items():
            if order.status() == OrderStatus.not_traded:
                # 以均价进行撮合
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
                    continue;

                if order.comb_offset_flag() == CombOffset.close and is_used == -2:  # 平仓
                    continue

                # 今天未有成交
                if daily_price.vol() == 0.00:
                    continue

                if daily_price.vol() < order.vol():  # 交易量不满足
                    continue

                if not daily_price.is_use:  # 停牌或涨跌停
                    continue

                if order_id in self.__working_limit_order:
                    del self.__working_limit_order[order_id]
                # 委托成功推送到策略
                order.set_status(OrderStatus.entrust_traded)

                order.dump()
                self.__strategy.on_order(order)
                
                
                order.set_status(OrderStatus.all_traded)
                self.__strategy.on_order(order)

                vol = Volume()
                vol.create_trader_id()
                vol.set_symbol(order.symbol())
                vol.set_direction(order.direction())
                vol.set_comb_offset_flag(order.comb_offset_flag())
                if order.order_price_type() == OrderPrice.avg_price:
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
        for date in self.__trade_date:
            MLog.write().debug('trader starting date：%d========>' % (date))
            # 根据委托单和持有单读取行情
            MLog.write().debug('get %d daily_price========>' %(date))
            daily_price_list = self.on_get_daily_price(date)
           
            if daily_price_list is not None and len(daily_price_list) > 0:
                # 送给策略，对持仓做操作
                MLog.write().debug('push daily_price strategy========>')
                self.__strategy.on_market_data(date, daily_price_list)
                # 读取行情，撮合价格成交
                MLog.write().debug('cross_limit_order ========>')
                self.cross_limit_order(date, daily_price_list)
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
    lb = LookBack(20160104, 20180105)
    lb.init_read_lhb('../../data/nirvana/xq/')
    lb.start()
    lb.calc_result()
