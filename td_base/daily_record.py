#!/usr/bin/env python
# coding=utf-8

from collections import OrderedDict
import pandas as pd
import copy
import math
import numpy as np
import time
import datetime
import csv
import os
import sys
sys.path.append("..")
from mlog import MLog
import config as Config
TDAYS_PER_YEAR = 250


class SummaryRecord(object):
    """Summary of class here.
        总记录类
    Attributes:
        output:输出目录
    """

    def __init__(self, output='./record/'):
        """Inits LookBack with blah."""
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

        daily_fieldnames = ['mktime', 'interests', 'profit', 'value', 'daily_value', 'all_profit', 'close_profit',
                            'prosition_profit', 'settle_available_cash', 'position_cost', 'fee', 'retrace', 'value_chg',
                            'log_chg', 'last_profit', 'max_profit']
        summary_fieldnames = ['chg_mean', 'chg_std', 'volatility', 'sharp', 'annualized', 'trade_count',
                              'daily_win_rate', 'final_value', 'max_retr']
        record_colums = ['mktime', 'interests', 'value', 'profit', 'available_cash', 'retrace', 'chg', 'log_chg']

        time_now_flag = time.strftime('%Y-%m-%d_%H:%M:%S',
                                      time.localtime(time.time()))
        dir = Config.RECORD_BASE_DIR + output + '/' + str(time_now_flag.split('_')[0]) + '/' + str(str(time.time()).split('.')[0])

        self.dir = dir
        if not os.path.exists(dir):
            os.makedirs(dir)

        self.__sub_dir = {}
        self.__sub_dir['vol'] = self.dir + '/volume/'  # 交易记录输出目录
        self.__sub_dir['order'] = self.dir + '/order/'  # 委托单记录输出目录
        self.__sub_dir['position'] = self.dir + '/position/'  # 持仓记录输出目录
        self.__sub_dir['close'] = self.dir + '/close/'  # 平仓记录输出目录

        for k, value in self.__sub_dir.items():
            if not os.path.exists(str(value)):
                os.makedirs(str(value))

        daily_filename = dir + '/' + 'summary_daily_record' + '.csv'
        summary_filename = dir + '/' + 'summary_record' + '.csv'
        self.__summary_df_filename = dir + '/' + 'result' + '.csv'

        self.df = pd.DataFrame(columns=record_colums)

        self.__daily_writer_hanle = open(daily_filename, 'w')
        self.__summary_writer_hanle = open(summary_filename, 'w')

        self.__daily_writer = csv.DictWriter(self.__daily_writer_hanle, fieldnames=daily_fieldnames)
        self.__daily_writer.writeheader()

        self.__summary_writer = csv.DictWriter(self.__summary_writer_hanle, fieldnames=summary_fieldnames)
        self.__summary_writer.writeheader()

    def __del__(self):
        self.__daily_writer_hanle.close()
        self.__summary_writer_hanle.close()
        MLog.write().info(self.dir)

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

    def calc_record(self):
        """Performs operation calc_record blah.
            计算净值,回撤等累计值

        Attributes:
        """
        self.__chg_mean = np.mean(self.df['log_chg'])
        self.__chg_std = np.std(self.df['log_chg'])
        self.trade_count = self.df.shape[0]
        self.final_value = self.df['value'].values[-1]
        self.__max_retr = np.min(self.df['retrace'])

        self.__volatility = self.__chg_std * np.sqrt(TDAYS_PER_YEAR)
        self.__sharp = self.__chg_mean / self.__chg_std * np.sqrt(TDAYS_PER_YEAR)
        self.__annualized_returns = (self.final_value - 1) / self.trade_count * TDAYS_PER_YEAR * 100
        self.__daily_win_rate = (self.df[self.df['chg'] > 0.00].shape[0]) * 100 / self.trade_count

    def __record_file(self, date, filename, v_fieldnames, vol_list):

        """Performs operation __record_file blah.
        存储交易持仓信息在CSV文件中

        Attributes:
            date:交易日期
            filename:文件路径及文件名
            v_fieldnames:csv文件目录
            vol_list:记录信息列表
        """
        with open(filename, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=v_fieldnames)
            writer.writeheader()
            for volume in vol_list:
                writer.writerow(volume)

    def record_volume(self, date, volume_list, position_list):
        """Performs operation record_volume blah.
        存储交易持仓信息在CSV文件中

        Attributes:
            date:交易日期
            volume_list:交易记录信息列表
            position_list:持仓记录信息列表
        """

        volume_fieldnames = ['symbol', 'trader_id', 'order_id', 'direction',
                             'price', 'comb_offset', 'cost', 'fee', 'commission',
                             'stamp', 'transfer', 'daily_profit', 'settle_price',
                             'amount', 'min_volume', 'create_time']

        vol_filename = str(self.__sub_dir['vol']) + str(date) + '_vol.csv'
        position_filename = str(self.__sub_dir['position']) + str(date) + '_position.csv'
        self.__record_file(date, vol_filename, volume_fieldnames, volume_list)
        self.__record_file(date, position_filename, volume_fieldnames, position_list)

    def record_order(self, date, order_list):
        """Performs operation record_order blah.
        存储委托单信息在CSV文件中

        Attributes:
            date:交易日期
            order_list:委托记录信息列表
        """

        if order_list is None:
            return

        order_fieldnames = ['symbol', 'order_id', 'comb_offset', 'direction',
                            'order_type', 'price', 'fee', 'commission', 'stamp',
                            'transfer', 'cost', 'hold_vol_id', 'status', 'amount',
                            'create_time', 'min_volume']

        filename = str(self.__sub_dir['order']) + str(date) + '_order.csv'
        with open(filename, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=order_fieldnames)
            writer.writeheader()
            for order in order_list:
                writer.writerow(order)

    def record_daily(self, dict, df):
        """Performs operation record_daily blah.
        存储每个交易日DailyRecord相关信息

        Attributes:
            dict:csv文件标题
            df:交易日DailyRecord相关信息
        """
        self.__daily_writer.writerow(dict)
        self.df = self.df.append(df, ignore_index=True)

    def dump(self):
        MLog.write().debug('日对数收益:%f,日对数收益方差:%f,波动率:%f,夏普比率:%f,年化收益:%f,交易天数:%d,日胜率:%f,最终盈利:%f,最大回测:%f'
                           % (
                           self.__chg_mean, self.__chg_std, self.__volatility, self.__sharp, self.__annualized_returns,
                           self.trade_count,
                           self.__daily_win_rate, self.final_value, self.__max_retr))

    def summary_record(self):
        self.__summary_writer.writerow({'chg_mean': round(self.__chg_mean, 4), 'chg_std': round(self.__chg_std, 4),
                                        'volatility': round(self.__volatility, 4),
                                        'sharp': round(self.__sharp, 4),
                                        'annualized': round(self.__annualized_returns, 2),
                                        'trade_count': self.trade_count,
                                        'daily_win_rate': round(self.__daily_win_rate, 4),
                                        'final_value': round(self.final_value, 2),
                                        'max_retr': round(self.__max_retr, 2)})

        self.df.to_csv(self.__summary_df_filename, encoding='utf-8')


class DailyRecord(object):
    """Summary of class here.
        每日记录类

    Attributes:
    """
    def __init__(self):
        self.__mktime = 0  # 交易日
        self.__account_id = ''
        self._interests = 0.0  # 上日结存 + 平仓盈亏 + 浮动盈亏(持仓盈亏) + 出入金 - 手续费 
        self._profit = 0.0  # 当日盈亏
        self._value = 0.0  # 累计净值
        self._daily_value = 0.0  # 当日净值
        self._value_chg = 0.0  # 涨跌幅
        self._log_chg = 0.0  # 日对数收益
        self._retracement = 0.0  # 最大回撤
        self.__position_cost = 0.0  # 当日持仓成本
        self._base_value = 0.0  # 初始可用资金
        self.__settle_available_cash = 0.0  # 结算后可用资金
        self.__close_profit = 0.0  # 平仓收益
        self.__position_profit = 0.0  # 持仓收益
        self.__fee = 0.0  # 手续费
        self._max_profit = 0.0  # 历史中最大收益
        self.last_value = 0.0  # 上一个交易日的净值
        self._last_profit = 0.0  # 上一个交易日的累计盈亏
        self.__last_available_cash = 0.0  # 今天初始资金
        self.__history_limit_volume = OrderedDict()  # 交易记录
        self.__history_limit_order = OrderedDict()  # 委托订单
        self.__history_long_volume = OrderedDict()  # 持仓记录

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

    def set_long_volume(self, long_volume):
        self.__history_long_volume = copy.deepcopy(long_volume)

    def set_limit_volume(self, limit_volume):
        self.__history_limit_volume = copy.deepcopy(limit_volume)

    def set_limit_order(self, limit_order):
        self.__history_limit_order = copy.deepcopy(limit_order)

    def set_base_value(self, base_value):
        self._base_value = base_value

    def set_last_available_cash(self, last_available_cash):
        self.__last_available_cash = last_available_cash

    def set_position_cost(self, position_cost):
        self.__position_cost = position_cost

    def set_max_profit(self, max_profit):
        self._max_profit = max_profit

    def set_last_value(self, last_value):
        self.last_value = last_value

    def set_last_profit(self, last_profit):
        self._last_profit = last_profit

    def last_available_cash(self):
        return self.__last_available_cash

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
        """Performs operation calc_result blah.
            计算每日权益,净值等信息

        Attributes:
        """
        self._interests = self._base_value + self._last_profit + self._profit  # 当日收益
        self.__settle_available_cash = self.__last_available_cash + self.__close_profit - self.__fee  # 开始之前可用资金 加上平仓收益 减去手续费
        self._value = self._interests / self._base_value  # 累计净值
        self._daily_value = self._interests / (self._base_value + self._last_profit)  # 当日净值
        self._retracement = ((self._profit + self._last_profit) - self._max_profit) / (
        self._max_profit + self._base_value) * 100
        self._value_chg = (self._value - self.last_value) / self.last_value  # 净值涨跌幅
        self._log_chg = math.log(1 + self._value_chg)

    def position_tocsv(self):
        to_csv_list = []
        for v, value in self.__history_long_volume.items():
            to_csv_list.append(value.to_csv())
        return to_csv_list

    def volume_tocsv(self):
        # MLog.write().debug('交易情况:')
        to_csv_list = []
        for v, value in self.__history_limit_volume.items():
            value.dump()
            to_csv_list.append(value.to_csv())
        return to_csv_list

    def order_tocsv(self):
        to_csv_list = []
        for o, value in self.__history_limit_order.items():
            value.dump()
            to_csv_list.append(value.to_csv())
        return to_csv_list

    def log(self):
        return (
        '交易日:%d,今日权益:%f,今日盈亏:%f,平仓盈亏:%f,持仓盈亏:%f,持仓成本:%f,手续费:%f,昨日累计盈亏:%f,最大盈亏:%f,今日净值:%f,最大回撤:%f,今日初始资金:%f,今日结算后资金:%f,涨跌幅:%f,对数收益:%f'
        % (self.__mktime, self._interests, self.all_profit(), self.__close_profit, self.__position_profit,
           self.__position_cost, self.__fee,
           self._last_profit, self._max_profit,
           self._value, self._retracement, self._base_value, self.__settle_available_cash,
           self._value_chg, self._log_chg))

    def to_csv(self):
        dict = {'mktime': self.__mktime, 'interests': round(self._interests, 2), 'profit': round(self._profit, 2),
                'value': round(self._value, 2),
                'daily_value': round(self._daily_value, 2),
                'all_profit': round(self._last_profit + self.all_profit(), 2),
                'close_profit': round(self.__close_profit, 2), 'prosition_profit': round(self.__position_profit, 2),
                'settle_available_cash': round(self.__settle_available_cash, 2),
                'position_cost': round(self.__position_cost, 2), 'fee': round(self.__fee, 2),
                'retrace': round(self._retracement, 2), 'value_chg': round(self._value_chg, 4),
                'log_chg': round(self._log_chg, 4), 'last_profit': round(self._last_profit, 2),
                'max_profit': round(self._max_profit, 2)}
        return dict

    def to_dataframe(self):
        return pd.DataFrame({'mktime': self.__mktime, 'interests': round(self.interests(), 2),
                             'value': round(self.value(), 4), 'profit': round(self._last_profit + self.all_profit(), 2),
                             'available_cash': round(self.__settle_available_cash, 2),
                             'retrace': round(self.retrace(), 4), 'chg': round(self.chg(), 4),
                             'log_chg': round(self.log_chg(), 4)},
                            index=['mktime'])

    def dump(self):
        MLog.write().debug(self.log())
        # self.volume_log()
        MLog.write().debug('\n\n')
