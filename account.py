#!/usr/bin/env python
# coding=utf-8

from order import Direction, CombOffset
from mlog import MLog


class Account(object):

    """Summary of class here.
        账户资金类

    Attributes:
    """

    def __init__(self):
        """Inits Account with blah."""

        self.__account_id = ''  # 账户id
        self.__available_cash = 0.0  # 可用资金
        self.__locked_cash = 0.0  # 挂单锁住资金
        self.__cost = 0.0  # 消耗成本(不包含手续费)
        self.__positions_cost = 0.0  # 持仓成本】
        self.__starting_cash = 0.0  # 初始资金
        self.__positions_value = 0.0  # 持仓价值
        self.__fee = 0.0  # 总手续费
        self.__close_profit = 0.0  # 平仓盈亏
        self.__position_profit = 0.0  # 持仓盈亏
        self.__deposit = 0  # 累计入金金额
        self.__withdraw = 0  # 累计出金金额

    def reset(self):
        """Performs operation reset blah.
            重置每天统计参数
        """
        self.__locked_cash = 0.0
        self.__fee = 0.0
        self.__position_profit = 0.0
        self.__close_profit = 0.0

    def close_profit(self):
        return self.__close_profit

    def position_profit(self):
        return self.__position_profit

    def fee(self):
        return self.__fee

    def cost(self):
        return self.__cost

    def available_cash(self):
        return self.__available_cash

    def starting_cash(self):
        return self.__starting_cash

    def set_init_cash(self, init_cash):
        self.__available_cash += init_cash
        self.__deposit += init_cash
        self.__starting_cash += init_cash

    def set_account_id(self, account_id):
        self.__account_id = account_id

    def set_position_profit(self, position_profit):
        self.__position_profit = position_profit

    def set_close_profit(self, h_vol, c_vol):
        """Performs operation set_close_profit blah.
            挂单资金操作, 本身消耗，手续费, 平仓挂单只有手续费消耗
        Attributes:
            h_vol: 平仓信息对应的持仓信息
            c_vol: 平仓信息
        """

        self.__close_profit += (h_vol.limit_price() - c_vol.limit_price()) * (c_vol.amount() * c_vol.min_volume())

    def insert_order_cash(self, cost, fee):
        """Performs operation insert_order_cash blah.
            挂单资金操作, 本身消耗，手续费, 平仓挂单只有手续费消耗
        Attributes:
            cost: 开仓成本(不包含手续费)
            fee: 相关手续费
        """
        if self.__available_cash < cost:  # 可用资金不够时，补充资金
            MLog.write().debug('新增资金 100000')
            self.set_init_cash(100000)
        self.__available_cash -= (cost + fee)  # 消耗的可用资金数
        self.__cost += (cost)
        self.__locked_cash += (cost + fee)  # 挂单时被锁定的资金
        self.__fee += fee  # 消耗的手续费
        self.__withdraw += (cost + fee)  # 出去的资金

    # 撤单成功后资金操作, 本身消耗和手续费解封  平仓保证金设为0
    def cancel_order_cash(self, cost, fee):
        """Performs operation cancel_order_cash blah.
            取消单资金操作, 本身消耗，手续费, 平仓挂单只有手续费消耗
        Attributes:
            cost: 开仓成本(不包含手续费)
            fee: 相关手续费
        """
        self.__available_cash += (cost + fee)  # 保证金和手续费回到可用资金中
        self.__locked_cash -= (cost + fee)  # 解锁保证金和可用资金
        self.__fee -= fee  # 归还手续费
        self.__deposit += (cost + fee)  # 进入的资金

    #
    def open_cash(self, order_cost, volume_cost, order_fee, volume_fee):
        """Performs operation open_cash blah.
            建仓成功后，资金操作
        Attributes:
            order_cost: 开仓挂单成本(不包含手续费)
            volume_cost: 开仓成交成本(不包含手续费)
            order_fee: 开仓挂单手续费
            volume_fee: 开仓成交手续费
        """
        # 处理报单
        self.__locked_cash -= (order_cost + order_fee)
        self.__available_cash += (order_cost + order_fee)
        self.__cost -= order_cost
        self.__fee -= order_fee
        self.__deposit += (order_cost + order_fee)
        self.__positions_cost += volume_cost
        # 处理成交
        self.__available_cash -= (volume_cost + volume_fee)
        self.__cost += volume_cost
        self.__positions_cost += (volume_cost + volume_fee)
        self.__fee += volume_fee
        self.__withdraw += (volume_cost + volume_fee)

    def close_cash(self, hold_v, cur_v, order_fee):
        """Performs operation close_cash blah.
            平仓成功后，资金操作, 本身消耗，手续费, 平仓挂单只有手续费消耗
        Attributes:
            hold_v: 平仓信息对应的持仓信息
            cur_v: 平仓信息
            order_fee: 平仓仓挂单手续费
        """

        self.__locked_cash -= order_fee  # 解锁手续费，平仓建仓没有保证金
        
        self.__available_cash += order_fee  # 退还下单时候手续费
        self.__available_cash -= cur_v.fee()  # 扣除成交的手续费

        self.__fee -= order_fee
        self.__fee += cur_v.fee()

        self.__available_cash += (cur_v.cost())  # 计算当前平仓时候价格 * 量

        self.__positions_cost -= (hold_v.cost())
        # 计算平仓盈利
        profit = (cur_v.limit_price() - hold_v.limit_price()) * cur_v.amount() * cur_v.min_volume()

        self.__close_profit += profit
        return profit

    def log(self):
        return (
        "account:%d,available_cash:%f,locked_cash:%f,position_cost:%f,close_profit:%f,position_profit:%f,fee:%f,cost:%f,starting_cash:%f,deoposit:%f,withdraw:%f" % (
            self.__account_id, self.__available_cash, self.__locked_cash,
            self.__positions_cost, self.__close_profit, self.__position_profit,
            self.__fee, self.__cost, self.__starting_cash, self.__deposit,
            self.__withdraw))

    def dump(self):
        MLog.write().debug(self.log())
