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
        self.__chg_mean = 0.0 # 日对数收益均值
        self.__chg_std = 0.0 # 日对数收益方差
        self.__volatility = 0.0 # 波动率
        self.__sharp = 0.0 # 夏普比率
        self.__annualized_returns = 0.0 # 年化收益
        self.trade_count = 0 # 交易天数
        self.__daily_win_rate = 0.0 # 日胜率
        self.__volume_count = 0 # 订单总数
        self.__volume_win_rate = 0 # 订单胜率
        self.final_value = 0.0 # 最终盈利
        self.__max_retr = 0.0 # 最大回撤

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

    def set_final_value(self,final_value):
        self.final_value = final_value

    def set_max_retr(self, max_retr):
        self.__max_retr = max_retr


    def calc_record(self, chg_win_day):
        self.__volatility = self.__chg_std * np.sqrt(TDAYS_PER_YEAR)
        self.__sharp = self.__chg_mean / self.__chg_std * np.sqrt(TDAYS_PER_YEAR)
        self.__annualized_returns = (self.final_value - 1) / self.trade_count * TDAYS_PER_YEAR * 100
        self.__daily_win_rate = chg_win_day * 100 / self.trade_count

    def dump(self):
        MLog.write().info('chg_mean:%f,chg_std:%f,volatility:%f,sharp:%f,annualized_returns:%f,trade_count:%d,daily_win_rate:%f,final_value:%f,max_retr:%f',
                    self.__chg_mean, self.__chg_std, self.__volatility, self.__sharp, self.__annualized_returns, self.trade_count,
                    self.__daily_win_rate, self.final_value, self.__max_retr)

class DailyRecord(object):
    def __init__(self):
        self.__mktime = 0 # 交易日
        self.__account_id = ''
        
        
        self.__interests = 0.0  # 上日结存 + 平仓盈亏 + 浮动盈亏(持仓盈亏) + 出入金 - 手续费 
        self.__profit = 0.0 # 当日盈亏
        self.__value = 0.0 # 当日净值 
        self.__value_chg = 0.0 # 涨跌幅
        self.__log_chg = 0.0 # 日对数收益
        self.__retracement = 0.0 # 最大回撤

        self.__base_value = 0.0 # 当日初始可用资金
        self.__close_profit = 0.0  # 平仓收益
        self.__position_profit = 0.0 # 持仓收益
        self.__commission = 0.0 # 手续费
        self.__max_profit = 0.0 # 历史中最大收益
        self.__last_value = 0.0 # 上一个交易日的净值
        self.__last_profit = 0.0 # 上一个交易日的累计盈亏
        self.__history_limit_volume = OrderedDict() # 交易记录
        self.__history_limit_order = OrderedDict() # 委托订单



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

    def set_commssion(self, commssion):
        self.__commission = commssion

    def set_limit_volume(self, limit_volume):
        self.__history_limit_volume = copy.deepcopy(limit_volume)

    def set_limit_order(self,limit_order):
        self.__history_limit_order = copy.deepcopy(limit_order)


    def set_base_value(self,base_value):
        self.__base_value = base_value

    def set_max_profit(self, max_profit):
        self.__max_profit = max_profit

    def set_last_value(self, last_value):
        self.__last_value = last_value

    def set_last_profit(self, last_profit):
        self.__last_profit = last_profit

    def value(self):
        return self.__value

    def interests(self):
        return self.__interests
    
    def retrace(self):
        return self.__retracement

    def log_chg(self):
        return self.__log_chg

    def chg(self):
        return self.__value_chg

    def all_profit(self):
        self.__profit = self.__close_profit + self.__position_profit  - self.__commission # 当日盈亏
        return self.__profit

    def calc_result(self):
        self.__interests = self.__base_value + self.__profit #每日权益
        self.__value =  self.__interests / self.__base_value 
        self.__retracement = ((abs(self.__profit + self.__last_profit  - self.__max_profit)) / (self.__max_profit + self.__base_value)) * 100
        self.__value_chg = ((self.__value - self.__last_value)  / self.__last_value * 100) if self.__last_value != 0.0 else 0.0
        self.__log_chg = math.log(1 - self.__value_chg)

    def log(self):
        return ('mkdate:%d,interests:%f,profit:%f,total_profit:%f,max_profit:%f,value:%f,retracement:%f,base_value:%f,chg:%f,log_chg:%f'%(self.__mktime,
            self.__interests, self.all_profit(), self.__last_profit,
            self.__max_profit, self.__value, self.__retracement,
            self.__base_value,self.__value_chg,self.__log_chg))
    
    def dump(self):
        MLog.write().info(self.log())
