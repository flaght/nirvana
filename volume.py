#!/usr/bin/env python
# coding=utf-8

'''
成交数据
'''

import datetime
import time
from mlog import MLog
from order import CombOffset,Direction

GLOBAL_VOLUME_ID = 100
class Volume(object):
    def __init__(self):
        self.__symbol = '' # 交易标的
        self.__trader_id = 0 # 成交订单号
        self.__order_id = 0 # 报单号
        self.__direction = 0 # 1 买入 -1 卖出
        self.__limit_price = 0.0
        self.__comb_offset_flag = 0 # 0 开仓 1 平仓 2 强平 3 平今 4 平昨 5 强减
        self.__amount = 0 # 成交份额
        self.__create_time = 0 # 成交时间
        self.__strategy_id = 0 # 所属策略id
        self.__min_volume = 0 # 最小成交量
        self.__cost = 0.0 # 实际的全部消耗，不包含了手续费
        self.__fee = 0.0 # 手续费
        
        self.__commission = 0.0 # 佣金
        self.__commission_ratio = 0.0 # 佣金率
        self.__stamp = 0.0 # 印花税
        self.__stamp_ratio = 0.0 # 印花税率
        self.__transfer = 0.0 # 过户费
        self.__transfer_ratio = 0.0 #过户费率


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
        
        # print('[%s]--->Volume:trader_id:%d, order_id:%d, direction:%d, limit_price:%f, cost:%f, commission:%f, transfer:%f, stamp:%f, fee:%f, comb_offset_flag:%d, amount:%d, create_time:%d, strategy_id:%d, min_volume:%d'%(
        #                str, self.__trader_id, self.__order_id, self.__direction.value, self.__limit_price, self.cost(), self.__commission, self.__transfer, self.__stamp,
        #                self.fee(), self.__comb_offset_flag.value,self.__amount,self.__create_time,
        #                self.__strategy_id,self.__min_volume))


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
        return self.__limit_price * self.__min_volume * self.__amount


    def fee(self):
        # 开仓 佣金 + 过户费(上证)
        # 平仓 佣金 + 印花税 + 过户费(上证)
        if self.__comb_offset_flag == CombOffset.open:
            return self.__commission + self.__transfer
        elif self.__comb_offset_flag == CombOffset.close:
            return self.__commission + self.__stamp + self.__transfer
    
    def min_volume(self):
        return self.__min_volume
    
    def order_id(self):
        return self.__order_id

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
        self.__transfer_ratio = transfer_ratio
        # self.__transfer = int((self.__amount * self.__min_volume) / 1000 + 1) * transfer_ratio
        self.__transfer = int((self.__amount * self.__min_volume) * transfer_ratio) + 1
