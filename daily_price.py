#!/usr/bin/env python
# coding=utf-8

'''
日行情数据
'''
from mlog import MLog
class DailyPrice(object):
    
    def __init__(self):
        self.__trade_date = 0  # 交易日
        self.__symbol = '' # 标的
        self.__latest_price = 0.0 # 前一个收盘
        self.__today_open = 0.0 # 今日开盘
        self.__today_close = 0.0 # 今日收盘
        self.__today_high = 0.0 # 今日最高价
        self.__today_low = 0.0 # 今日最低价
        self.__vol = 0.0 # 成交量
        self.__amount = 0.0 #  成交额
        self.__change = 0.0 # 涨跌额
        self.__pchg = 0.0 # 涨跌幅
        self.__amplitude = 0.0 # 振幅
        self.__deals = 0.0 # 成交笔数
        self.__avg_price = 0.0 # 当日均价
        self.__avg_vol = 0.0 # 平均每笔成交量
        self.__avgtramt = 0.0 # 平均每笔成交金额
        self.__turnrate = 0.0 # 换手率
        self.__totmktcap = 0.0 # 总市值
        self.__negotiablemv = 0.0 # 流通市值


    def xq_parser(self, ob):
        self.__trade_date = int(ob.get('tradedate'))
        self.__latest_price = ob.get('lclose')
        self.__today_open = ob.get('topen')
        self.__today_close = ob.get('tclose')
        self.__today_high = ob.get('thigh')
        self.__today_low = ob.get('tlow')
        self.__vol = ob.get('vol')
        self.__amount = ob.get('amount')
        self.__change = ob.get('change')
        self.__pchg = ob.get('pchg')
        self.__amplitude = ob.get('amplitude')
        self.__deals = ob.get('deals')
        self.__avg_price = ob.get('avgprice')
        self.__avg_vol = ob.get('avgvol')
        self.__avgtramt = ob.get('avgtramt')
        self.__turnrate = ob.get('turnrate')
        self.__totmktcap = ob.get('totmktcap')
        self.__negotiablemv = ob.get('negotiablemv')


    def dump(self):
        MLog.write().debug('trade_date:%d,symbol:%s,latest_price:%f,today_open:%f,today_close:%f,today_high:%f,today_low:%f,vol:%f,amount:%f,change:%f,pchg:%f,amplitude:%f,deals:%f,avg_price:%f,avg_vol:%f,avgtramt:%f,turnrate:%f,totmktcap:%f,negotiablemv:%f',
                           self.__trade_date,self.__symbol,self.__latest_price,
                          self.__today_open,self.__today_close,self.__today_high,self.__today_low,
                          self.__vol,self.__amount,self.__change,self.__pchg,self.__amplitude,
                          self.__deals,self.__avg_price,self.__avg_vol,self.__avgtramt,
                          self.__turnrate,self.__totmktcap,self.__negotiablemv)

    def set_symbol(self, symbol):
        self.__symbol = symbol

    def trade_date(self):
        return self.__trade_date

    def symbol(self):
        return self.__symbol

    def latest_price(self):
        return self.__latest_price

    def today_open(self):
        return self.__today_open

    def today_close(self):
        return self.__today_close

    def today_high(self):
        return self.__today_high

    def today_low(self):
        return self.__today_low

    def vol(self):
        return self.__vol

    def amount(self):
        return self.__amount

    def change(self):
        return self.__change

    def pchg(self):
        return self.__pchg

    def amplitude(self):
        return self.__amplitude

    def deals(self):
        return self.__deals

    def avg_price(self):
        return self.__avg_price

    def avg_vol(self):
        return self.__avg_vol

    def avgtramt(self):
        return self.__avgtramt

    def turnrate(self):
        return self.__turnrate

    def totmktcap(self):
        return self.__totmktcap

    def negotiablev(self):
        return self.__negotiablemv
