#!/usr/bin/env python
# coding=utf-8

'''
订单数据
'''
import datetime
import time
from mlog import MLog
from enum import Enum, unique

GLOBAL_ORDER_ID = 100


@unique
class CombOffset(Enum):
    open = 0 # 开仓
    close = 1 # 平仓
    force_close = 2 # 强平
    close_today = 3 # 平今
    close_yesterday = 4 # 平昨
    local_force_close = 5 # 强减

@unique
class OrderPrice(Enum):
    any_price = 1 # 任意价
    limit_price = 2 # 限价
    best_price = 3 # 最优价
    last_price = 4 # 最新价
    avg_price = 5 # 均价单

@unique
class Direction(Enum):
    buy_direction = 1 # 买入
    sell_direction = -1 # 卖出

@unique
class OrderStatus(Enum):
    unknown = -1 # 未知
    not_traded = 0 # 未成交
    entrust_traded = 1 # 委托成功
    part_traded = 2 # 部分成交
    all_traded = 3 # 全部成交
    cacelled = 4 # 已撤销
    rejected = 5 # 拒单

class Order(object):
    def __init__(self):
        self.__account_id = ''
        self.__symbol = ''
        self.__order_id = 0
        self.__comb_offset_flag = 0 # 0 开仓 1 平仓 2 强平 3 平今 4 平昨 5 强减
        self.__direction = 0  # 1 买入 -1 卖出
        self.__order_price_type = 0 # 1.任意价 2.限价 3.最优价 4.最新价
        self.__limit_price = 0.0
        self.__amount = 0 # 正数为持有多头仓，负数为持有空头仓
        self.__strategy_id = 0 # 所属哪个策略
        self.__create_time = 0  # 报单时间
        self.__min_volume = 0 # 最小成交量
        self.__fee = 0.0 # 手续费
        self.__commission = 0.0 # 佣金
        self.__commission_ratio = 0.0 # 佣金率
        self.__stamp = 0.0 # 印花税
        self.__stamp_ratio = 0.0 # 印花税率
        self.__transfer = 0.0 # 过户费
        self.__transfer_ratio = 0.0 # 过户费率
        self.__margin = 0.0 # 保证金
        self.__margin_ratio = 0.0 # 保证金率
        self.__cost = 0.0 # 持仓费用(不包含手续费)
        self.__status = OrderStatus.not_traded #初始化为未知
        self.__hold_volume_id = 0 # 下平仓单时候记录持仓的ID，用于平仓盈亏计算

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

        MLog.write().debug('[%s]--->Order:symbol:%s,order_id:%d,hold_vol_id:%d,amount:%d,status:%d,comb_offset_flag:%d,direction:%d,limit_price:%f,amount:%d,cost:%f,fee:%f,commission:%f,stamp:%f,transfer:%f,strategy_id:%d,create_time:%d,min_volume:%d,margin:%f'%(
            str, self.__symbol, self.__order_id, self.__hold_volume_id, self.__amount, self.__status.value, self.__comb_offset_flag.value,
            self.__direction.value, self.__limit_price, self.__amount, self.cost(), self.fee(), self.__commission, self.__stamp, self.__transfer,
            self.__strategy_id,self.__create_time,self.__min_volume, self.__margin))

    def order_id(self):
        return self.__order_id

    def direction(self):
        return self.__direction

    def symbol(self):
        return self.__symbol

    def vol(self):
        return self.__amount * self.__min_volume

    def cost(self):
        return self.__limit_price * self.__amount * self.__min_volume

    def margin(self):
        if self.__comb_offset_flag == CombOffset.open:
            return self.__margin
        else:
            return 0.0

    def margin_ratio(self):
        return self.__margin_ratio

    def stamp(self):
        return self.__stamp

    def stamp_ratio(self):
        return self.__stamp_ratio

    def transfer(self):
        return self.__transfer

    def transfer_ratio(self):
        return self.__transfer_ratio

    def commission(self):
        return self.__commission

    def commission_ratio(self):
        return self.__commission_ratio

    def fee(self):
        # 开仓 佣金 + 过户费(上证)
        # 平仓 佣金 + 印花税 + 过户费(上证)
        if self.__comb_offset_flag == CombOffset.open:
            return self.__commission + self.__transfer
        elif self.__comb_offset_flag == CombOffset.close:
            return self.__commission + self.__stamp + self.__transfer

    def hold_volume_id(self):
        return self.__hold_volume_id

    def status(self):
        return self.__status

    def limit_price(self):
        return self.__limit_price

    def comb_offset_flag(self):
        return self.__comb_offset_flag

    def amount(self):
        return self.__amount

    def min_volume(self):
        return self.__min_volume

    def order_price_type(self):
        return self.__order_price_type

    def set_account_id(self, account_id):
        self.__account_id = account_id

    def set_symbol(self, symbol):
        self.__symbol = symbol

    def create_order_id(self):
        second_time = time.time()
        # self.__order_id = second_time * 1000000 + datetime.datetime.now().microsecond
        global GLOBAL_ORDER_ID
        GLOBAL_ORDER_ID += 1
        self.__order_id = GLOBAL_ORDER_ID
        self.__create_time = second_time

    def set_hold_volume_id(self,hold_volume_id):
        self.__hold_volume_id = hold_volume_id

    def set_create_time(self, create_time):
        self.__create_time = create_time

    def set_direction(self, direction):
        self.__direction = direction

    def set_comb_offset_flag(self, comb_offset_flag):
        self.__comb_offset_flag = comb_offset_flag

    def set_order_price_type(self, order_price_type):
        self.__order_price_type = order_price_type

    def set_limit_price(self, limit_price):
        #需要处理，满足最小倍数价格
        self.__limit_price = limit_price

    def set_amount(self, amount):
        self.__amount = amount

    def set_strategy_id(self, strategy_id):
        self.__strategy_id = strategy_id

    def set_min_volume(self, min_volume):
        self.__min_volume = min_volume

    def set_status(self, status):
        self.__status = status

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
    
    def set_margin(self, margin_ratio):
        self.__margin = self.__limit_price * self.__min_volume * margin_ratio
        self.__margin_ratio = margin_ratio
