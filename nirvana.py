#!/usr/bin/env python
# coding=utf-8

from collections import OrderedDict
from order import Order, CombOffset, OrderPrice, Direction, OrderStatus
from account import Account
from daily_record import DailyRecord, SummaryRecord
from daily_price import DailyPrice
from bize_lhb import BizeLHB, LHBPair

DEFAULT_CASH = 1000000

class Nirvana(object):
    
    __strategy_id = 1002
    __account_id = 10001
    
    def __init__(self, limit_order):
        self.__lhb_chg = OrderedDict()
        
        self.__limit_order = OrderedDict() # 委托单队列
        self.__long_volumes = OrderedDict() # 多头持仓情况


        self.__history_limit_order =  OrderedDict() # 历史委托单
        self.__history_limit_volumes = OrderedDict() # 历史成交记录

        self.__working_limit_order = limit_order

        self.__trader_record = OrderedDict() # 交易记录存储

        self.__account = Account()
        self.__account.set_account_id(self.__account_id)
        self.__account.set_init_cash(DEFAULT_CASH)

        self.__lhb_chg()


    def __lhb_chg(self):
        self.__lhb_chg['1'] = 1
        self.__lhb_chg['2'] = -1
        self.__lhb_chg['3'] = 0
        self.__lhb_chg['4'] = 0
        self.__lhb_chg['5'] = 1
        self.__lhb_chg['6'] = -1
        self.__lhb_chg['7'] = 1
        self.__lhb_chg['8'] = -1
        self.__lhb_chg['9'] = 0
        self.__lhb_chg['11'] = 0
        self.__lhb_chg['24'] = 1
        self.__lhb_chg['25'] = -1
        self.__lhb_chg['28'] = 1
        self.__lhb_chg['29'] = -1
        self.__lhb_chg['33'] = -1

    
    def __lhb_pair(self, lhb_dict, bize_ob, daily_price_ob, symbol, direction):
        for ob in bize_ob:
            bize_lhb = BizeLHB()
            bize_lhb.xq_parser(ob)
            bize_lhb.set_symbol(symbol)
            bize_lhb.dump()
            # 查看对应类型是否在
            if lhb_dict.has_key(bize_lhb.chg_type()):
                lhb_pair = lhb_dict[bize_lhb.chg_type()]
            else:
                lhb_pair = LHBPair()
                lhb_pair.xq_parser(daily_price_ob,symbol)
                lhb_pair.set_chg_type(bize_lhb.chg_type())
            if direction == 0:
                lhb_pair.set_bize_buy(bize_lhb)
            else:
                lhb_pair.set_bize_sale(bize_lhb)

            lhb_dict[lhb_pair.chg_type()] = lhb_pair

    def __lhb_parser(self, lhb):
        lhb_dict = OrderedDict()
        symbol = lhb.get('symbol')
        daily_price_ob = lhb.get('tqQtSkdailyprice')
        buy_bize_ob = lhb.get('tqQtBizunittrdinfoBuyList')
        sale_bize_ob = lhb.get('tqQtBizunittrdinfoSaleList')
        self.__lhb_pair(lhb_dict, buy_bize_ob, daily_price_ob, symbol, 0)
        self.__lhb_pair(lhb_dict, sale_bize_ob, daily_price_ob, symbol, 1)
        return lhb_dict
    
    def __lhb_price_strategy(self, lhb_pair):
        daily_price = lhb_pair.daily_price()
        if self.__lhb_chg[lhb_pair.chg_type()] == -1: # 负面上榜不下单
            return False

        if lhb_pair.buy_amount() < lhb_pair.sale_amount(): # 卖方小于买方不下单
            return False

        bize_buy_one = lhb_pair.bize_buy_from_pos(0)
        bize_buy_two = lhb_pair.bize_buy_from_pos(1)
        bize_sale_one = lhb_pair.bize_sale_form_pos(0)
        
        if bize_sale_one is None: #卖方不存在
            return True

        if bize_buy_one is None: # 买方1不存在
            return False

        if bize_buy_two is None: # 买2不存在，存在一家独大
            return False

        if bize_buy_one.amount() < bize_sale_one.amount(): # 买一金额小于卖一金额
            return False

        if bize_buy_one.amount() / bize_buy_two.amount() > 1.5:
            return False

        bize_sale_opp = lhb_pair.bize_sale_form_code(bize_buy_one.code())
        if bize_sale_opp is None:
            return True


    def __lhb_strategy(self, lhb_dict):
        for lhb_pair in lhb_dict.item():
            signal = self.__lhb_price_strategy(lhb_pair)

    def on_lhb_event(self, ob):
        lhb_dict = self.__lhb_parser(ob)
        self.__lhb_strategy(lhb_dict)

