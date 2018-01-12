#!/usr/bin/env python
# coding=utf-8

from collections import OrderedDict
from mlog import MLog
import copy
import math
import numpy as np

TDAYS_PER_YEAR = 250


class SummaryRecord(object):
    def __init__(self):
        self.__chg_mean = 0.0  # 日对数收益均值
        self.__chg_std = 0.0  # 日对数收益方差
        self.__volatility = 0.0  # 波动率
        self.__sharp = 0.0  # 夏普比率
        self.__annualized_returns = 0.0  # 年化收益
        self.trade_count = 0  # 交易天数
        self.__daily_win_rate = 0.0  # 日胜率
        self.__volume_count = 0  # 订单总数
        self.__volume_win_rate = 0  # 订单胜率
        self.final_value = 0.0  # 最终盈利
        self.__max_retr = 0.0  # 最大回撤

    def set_chg_mean(self, chg_mean):
        self.__chg_mean = chg_mean

    def set_chg_std(self, chg_std):
        self.__chg_std = chg_std

    def set_trade_count(self, trade_count):
        self.trade_count = trade_count

    def set_volume_count(self, volume_count):
        self.__volume_count = volume_count

    def set_volume_win_rate(self, volume_win_rate):
        self.__volume_win_rate = volume_win_rate

    def set_final_value(self, final_value):
        self.final_value = final_value

    def set_max_retr(self, max_retr):
        self.__max_retr = max_retr

    def calc_record(self, chg_win_day):
        self.__volatility = self.__chg_std * np.sqrt(TDAYS_PER_YEAR)
        self.__sharp = self.__chg_mean / self.__chg_std * np.sqrt(TDAYS_PER_YEAR)
        self.__annualized_returns = (self.final_value - 1) / self.trade_count * TDAYS_PER_YEAR * 100
        self.__daily_win_rate = chg_win_day * 100 / self.trade_count

    def dump(self):
        print('日对数收益:%f,日对数收益方差:%f,波动率:%f,夏普比率:%f,年化收益:%f,交易天数:%d,日胜率:%f,最终盈利:%f,最大回测:%f'
              % (self.__chg_mean, self.__chg_std, self.__volatility, self.__sharp, self.__annualized_returns,
                 self.trade_count,
                 self.__daily_win_rate, self.final_value, self.__max_retr))


class DailyRecord(object):
    def __init__(self):
        self.__mktime = 0  # 交易日
        self.__account_id = ''

        self._interests = 0.0  # 上日结存 + 平仓盈亏 + 浮动盈亏(持仓盈亏) + 出入金 - 手续费 
        self._profit = 0.0  # 当日盈亏
        self._value = 0.0  # 累计净值
        self._daily_value = 0.0 # 当日净值
        self._value_chg = 0.0  # 涨跌幅
        self._log_chg = 0.0  # 日对数收益
        self._retracement = 0.0  # 最大回撤

        self.__position_cost = 0.0 # 当日持仓成本
        self._base_value = 0.0  # 初始可用资金
        self.__settle_available_cash = 0.0 # 结算后可用资金
        self.__close_profit = 0.0  # 平仓收益
        self.__position_profit = 0.0  # 持仓收益
        self.__fee = 0.0  # 手续费
        self._max_profit = 0.0  # 历史中最大收益
        self.last_value = 0.0  # 上一个交易日的净值
        self._last_profit = 0.0  # 上一个交易日的累计盈亏
        self.__history_limit_volume = OrderedDict()  # 交易记录
        self.__history_limit_order = OrderedDict()  # 委托订单

    def mktime(self):
        return self.__mktime

    def set_mktime(self, mktime):
        self.__mktime = mktime

    def set_account_id(self, account_id):
        self.__account_id = account_id

    def set_close_profit(self, close_profit):
        self.__close_profit = close_profit

    def set_position_profit(self, position_profit):
        self.__position_profit = position_profit

    def set_fee(self, fee):
        self.__fee = fee

    def set_limit_volume(self, limit_volume):
        self.__history_limit_volume = copy.deepcopy(limit_volume)

    def set_limit_order(self, limit_order):
        self.__history_limit_order = copy.deepcopy(limit_order)

    def set_base_value(self, base_value):
        self._base_value = base_value

    def set_settle_available_cash(self, settle_available_cash):
        self.__settle_available_cash = settle_available_cash

    def set_position_cost(self, position_cost):
        self.__position_cost = position_cost

    def set_max_profit(self, max_profit):
        self._max_profit = max_profit

    def set_last_value(self, last_value):
        self.last_value = last_value

    def set_last_profit(self, last_profit):
        self._last_profit = last_profit

    def value(self):
        return self._value

    def interests(self):
        return self._interests

    def retrace(self):
        return self._retracement

    def log_chg(self):
        return self._log_chg

    def chg(self):
        return self._value_chg

    def all_profit(self):
        self._profit = self.__close_profit + self.__position_profit - self.__fee  # 当日盈亏
        return self._profit

    def close_profit(self):
        return self.__close_profit - self.__fee

   
    def calc_result(self):
        self._interests = self._base_value + self._last_profit + self._profit # 当日收益
        self._value = self._interests / self._base_value # 累计净值
        self._daily_value = self._interests / (self._base_value + self._last_profit) # 当日净值
        self._max_profit = self._max_profit + self._profit if self._profit > 0 else self._max_profit
        self._retracement = (self._profit - self._max_profit) / (self._max_profit + self._base_value) * 100
        self._value_chg = (self._value - self.last_value) / self.last_value # 净值涨跌幅
        self._log_chg = math.log(1 - self._value_chg)
    
    def volume_log(self):
        print('交易情况:')
        for v, value in self.__history_limit_volume.items():
            value.dump()

    def log(self):
        return ('交易日:%d,今日权益:%f,今日盈亏:%f,平仓盈亏:%f,持仓盈亏:%f,持仓成本:%f,手续费:%f,昨日累计盈亏:%f,最大盈亏:%f,今日净值:%f,最大回撤:%f,今日初始资金:%f,今日结算后资金:%f,涨跌幅:%f,对数收益:%f'
                % (self.__mktime, self._interests, self.all_profit(), self.__close_profit, self.__position_profit,self.__position_cost,self.__fee, 
                   self._last_profit, self._max_profit,
                    self._value, self._retracement, self._base_value,self.__settle_available_cash,
                   self._value_chg, self._log_chg))

    def dump(self):
        print(self.log())
        # self.volume_log()
        print('\n\n')
