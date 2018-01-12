#!/usr/bin/env python
# coding=utf-8

'''
成交数据
'''

import datetime
import time
from mlog import MLog
from order import CombOffset,Direction
from collections import OrderedDict

GLOBAL_VOLUME_ID = 100


class Volume(object):
    def __init__(self):
        self.__symbol = '' # 交易标的
        self.__trader_id = 0 # 成交订单号
        self.__order_id = 0 # 报单号
        self.__direction = 0 # 1 买入 -1 卖出
        self.__limit_price = 0.0 # 持仓价 
        self.__comb_offset_flag = 0 # 0 开仓 1 平仓 2 强平 3 平今 4 平昨 5 强减
        self.__amount = 0 # 成交份额
        self.__create_time = 0 # 成交时间
        self.__strategy_id = 0 # 所属策略id
        self.__min_volume = 0 # 最小成交量
        self.__cost = 0.0 # 持仓成本，不包含了手续费
        self.__fee = 0.0 # 手续费

        self.__commission = 0.0 # 佣金
        self.__commission_ratio = 0.0 # 佣金率
        self.__stamp = 0.0 # 印花税
        self.__stamp_ratio = 0.0 # 印花税率
        self.__transfer = 0.0 # 过户费
        self.__transfer_ratio = 0.0 #过户费率

        self.__daily_profit  = 0.0 # 日持仓盈亏
        self.__daily_settle_price = 0.0 #当日结算价
        self.__profit = 0.0 # 累积盈利
        self.__profit_dict = OrderedDict() # 日持仓盈亏列表

        self.__order_list = [] # 订单列表


    def dump(self):
        str = '异常单'
        if self.__comb_offset_flag == CombOffset.open and self.__direction == Direction.buy_direction:
            str = '多头开仓'
        elif self.__comb_offset_flag == CombOffset.open and self.__direction == Direction.sell_direction:
            str = '空头开仓'
        elif self.__comb_offset_flag == CombOffset.close and self.__direction == Direction.buy_direction:
            str = '空头平仓'
        elif self.__comb_offset_flag == CombOffset.close and self.__direction == Direction.sell_direction:
            str = '多头平仓'

        print('[%s]--->%s Volume:订单ID:%d, 委托单ID:%d, 方向:%d, 成交价:%f, 成本(不含手续费):%f, 佣金:%f, 转让费:%f, 印花税:%f, 手续费:%f, 当日盈亏:%f, 累计盈亏:%f,今日结算价:%f 订单类型:%d, 手数:%d, 成交时间:%d, strategy_id:%d, 最小成交单位量:%d'%(
            str, self.__symbol, self.__trader_id, self.__order_id, self.__direction.value, self.__limit_price, self.cost(), self.__commission, self.__transfer, self.__stamp,
            self.fee(), self.__daily_profit, self.__profit, self.__daily_settle_price, self.__comb_offset_flag.value,self.__amount,self.__create_time,
            self.__strategy_id,self.__min_volume))


    def trader_id(self):
        return self.__trader_id

    def amount(self):
        return self.__amount

    def order_id(self):
        return self.__order_id

    def direction(self):
        return self.__direction

    def comb_offset_flag(self):
        return self.__comb_offset_flag

    def symbol(self):
        return self.__symbol

    def limit_price(self):
        return self.__limit_price

    def create_trader_id(self):
        second_time = time.time()
        # self.__trader_id = second_time * 1000000 + datetime.datetime.now().microsecond
        global GLOBAL_VOLUME_ID
        GLOBAL_VOLUME_ID += 1
        self.__trader_id = GLOBAL_VOLUME_ID
        self.__create_time = second_time

    def cost(self):
        return self.__limit_price * self.__amount * self.__min_volume
    
    def fee(self):
        # 开仓 佣金 + 过户费(上证)
        # 平仓 佣金 + 印花税 + 过户费(上证)
        if self.__comb_offset_flag == CombOffset.open:
            return self.__commission + self.__transfer
        elif self.__comb_offset_flag == CombOffset.close:
            return self.__commission + self.__stamp + self.__transfer

    def daily_profit(self):
        return self.__daily_profit

    def profit(self):
        return self.__profit

    def min_volume(self):
        return self.__min_volume

    def set_settle_price(self, date, settle_price):
        self.__daily_settle_price = settle_price
        self.__daily_profit = (settle_price - self.__limit_price) * self.__min_volume * self.__amount - self.fee()
        self.__profit += self.__daily_profit
        self.__profit_dict[date] = {'amount':self.__amount,'settle_price':settle_price,'fee':self.fee()}
 
    def set_order(self, order):
        self.__order_list[order.order_id()] = order

    def set_symbol(self, symbol):
        self.__symbol = symbol

    def set_order_id(self, order_id):
        self.__order_id = order_id

    def set_direction(self, direction):
        self.__direction = direction

    def set_limit_price(self, limit_price):
        self.__limit_price = limit_price

    def set_comb_offset_flag(self, comb_offset_flag):
        self.__comb_offset_flag = comb_offset_flag

    def set_amount(self, amount):
        self.__amount = amount

    def set_create_time(self, create_time):
        self.__create_time = create_time

    def set_strategy_id(self, strategy_id):
        self.__strategy_id = strategy_id

    def set_min_volume(self, min_volume):
        self.__min_volume = min_volume

    # 印花税
    def set_stamp(self, stamp_ratio):
        self.__stamp_ratio = stamp_ratio
        self.__stamp = self.__limit_price * self.__min_volume * self.__amount  * stamp_ratio

    # 佣金
    def set_commission(self, commission_ratio):
        self.__commission_ratio = commission_ratio
        commission = self.__limit_price * self.__amount * self.__min_volume * commission_ratio
        self.__commission = commission if commission > 5 else 5

    # 过户费
    def set_transfer(self, transfer_ratio):
        self.__transfer_ratio  = transfer_ratio if self.__symbol[0:2] == 'SH' else 0.0
        self.__transfer = int((self.__amount * self.__min_volume) * transfer_ratio) + 1 if self.__symbol[0:2]=='SH' else 0.0
