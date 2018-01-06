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
        self.lhb = OrderedDict()
        
        self.__limit_order = OrderedDict() # 委托单队列
        self.__long_volumes = OrderedDict() # 多头持仓情况


        self.__history_limit_order =  OrderedDict() # 历史委托单
        self.__history_limit_volumes = OrderedDict() # 历史成交记录

        self.__working_limit_order = limit_order

        self.__trader_record = OrderedDict() # 交易记录存储

        self.__account = Account()
        self.__account.set_account_id(self.__account_id)
        self.__account.set_init_cash(DEFAULT_CASH)

        self.__init_lhb_chg()


    def __init_lhb_chg(self):
        self.lhb[u'01'] = 1
        self.lhb[u'02'] = -1
        self.lhb[u'03'] = 0
        self.lhb[u'04'] = 0
        self.lhb[u'05'] = 1
        self.lhb[u'06'] = -1
        self.lhb[u'07'] = 1
        self.lhb[u'08'] = -1
        self.lhb[u'09'] = 0
        self.lhb[u'11'] = 0
        self.lhb[u'24'] = 1
        self.lhb[u'25'] = -1
        self.lhb[u'28'] = 1
        self.lhb[u'29'] = -1
        self.lhb[u'33'] = -1

    
    def __lhb_pair(self, lhb_dict, bize_ob, daily_price_ob, symbol, date, direction):
        for ob in bize_ob:
            bize_lhb = BizeLHB()
            bize_lhb.xq_parser(ob)
            bize_lhb.set_symbol(symbol)
            # bize_lhb.dump()
            # 查看对应类型是否在
            if lhb_dict.has_key(bize_lhb.chg_type()):
                lhb_pair = lhb_dict[bize_lhb.chg_type()]
            else:
                lhb_pair = LHBPair()
                if daily_price_ob is not None:
                    lhb_pair.xq_parser(daily_price_ob,symbol)
                lhb_pair.set_chg_type(bize_lhb.chg_type())
                lhb_pair.set_symbol(symbol)
                lhb_pair.set_date(date)
            if direction == 0:
                lhb_pair.set_bize_buy(bize_lhb)
            else:
                lhb_pair.set_bize_sale(bize_lhb)

            lhb_dict[lhb_pair.chg_type()] = lhb_pair

    def __lhb_parser(self, lhb, date):
        lhb_dict = OrderedDict()
        daily_price_ob = None
        buy_bize_ob = None
        sale_bize_ob = None
        symbol = lhb.get('symbol')
        if lhb.has_key('tqQtSkdailyprice'):
            daily_price_ob = lhb.get('tqQtSkdailyprice')
        if lhb.has_key('tqQtBizunittrdinfoBuyList'):
            buy_bize_ob = lhb.get('tqQtBizunittrdinfoBuyList')
        if lhb.has_key('tqQtBizunittrdinfoSaleList'):
            sale_bize_ob = lhb.get('tqQtBizunittrdinfoSaleList')
        self.__lhb_pair(lhb_dict, buy_bize_ob, daily_price_ob, symbol, date, 0)
        self.__lhb_pair(lhb_dict, sale_bize_ob, daily_price_ob, symbol,date, 1)
        return lhb_dict



    def __lhb_buy_price(self, bize_buy_one, bize_buy_two,lhb_pair,  date, symbol):
        if bize_buy_two is None and bize_buy_one is not None: # 只有买一方， 防止一家独大
            print('%d: %s 只有买一方，存在一家独大危险'%(date, symbol))
            return False
        if bize_buy_one.amount() / bize_buy_two.amount() > 1.5: # 买一方和买二方相差太大
            print('%d: %s 买一方和买二方相差太大'%(date, symbol))
            return False


        bize_sale_opp = lhb_pair.bize_sale_from_code(bize_buy_one.bize_code())
        if bize_sale_opp is not None:
            print('%d: %s 买一方非单纯买方'%(date, symbol))
            return False
        return True

    def __lhb_price_strategy(self, lhb_pair):
        daily_price = lhb_pair.daily_price()
        symbol = lhb_pair.symbol()
        date = lhb_pair.date()
        if self.lhb[lhb_pair.chg_type()] == -1: # 负面上榜不下单
            print('%d: %s 负面上榜不下单'%(date, symbol))
            return False
        
        bize_buy_one = lhb_pair.bize_buy_from_pos(0)
        bize_buy_two = lhb_pair.bize_buy_from_pos(1)
        bize_sale_one = lhb_pair.bize_sale_from_pos(0)

        if bize_sale_one is not None and bize_buy_two is None: # 只有卖方
            print('%d: %s 只有卖方'%(date, symbol))
            return False

        if bize_sale_one is None and bize_buy_one is not None: # 只有买方
            r = self.__lhb_buy_price(bize_buy_one, bize_buy_two,lhb_pair, date, symbol)
            if r == False:
                return False
            else:
                print('%d: %s 单方博弈可以下单'%(date, symbol))
                return True

        # 存在买卖双方
        if lhb_pair.buy_amount() < lhb_pair.sale_amount(): # 卖方小于买方不下单
            print('%d: %s 卖方总额大于买方总额'%(date, symbol))
            return False

        r = self.__lhb_buy_price(bize_buy_one, bize_buy_two, lhb_pair, date, symbol)
        if r == False:
            return False
        else:
            print('%d: %s 双方博弈可以下单'%(date, symbol))
            return True

    def __lhb_price_strategy_v1(self, lhb_pair):
        daily_price = lhb_pair.daily_price()
        symbol = lhb_pair.symbol()
        date = lhb_pair.date()
        if self.lhb[lhb_pair.chg_type()] == -1: # 负面上榜不下单
            return False

        if lhb_pair.buy_amount() < lhb_pair.sale_amount(): # 卖方小于买方不下单
            print('%d: %s 卖方总额大于买方总额'%(date, symbol))
            return False

        bize_buy_one = lhb_pair.bize_buy_from_pos(0)
        bize_buy_two = lhb_pair.bize_buy_from_pos(1)
        bize_sale_one = lhb_pair.bize_sale_from_pos(0)
        
        if bize_sale_one is None: #卖方不存在
            print('%d: %s 卖方不存在 可以下单' %(date, symbol))
            return True

        if bize_buy_one is None: # 买方不存在
            print('%d: %s 买方不存在' %(date, symbol))
            return False

        if bize_buy_two is None: # 买2不存在，存在一家独大
            print('%d: %s 只有买一方，存在一家独大危险'%(date, symbol))
            return False

        if bize_buy_one.amount() < bize_sale_one.amount(): # 买一金额小于卖一金额
            print('%d: %s 买一金额小于卖一金额'%(date, symbol))
            return False

        if bize_buy_one.amount() / bize_buy_two.amount() > 1.5:
            print('%d: %s 买一方和买二方相差太大'%(date, symbol))
            return False

        bize_sale_opp = lhb_pair.bize_sale_from_code(bize_buy_one.bize_code())
        if bize_sale_opp is not None:
            print('%d: %s 买一方非单纯买方'%(date, symbol))
            return False

        print('%d: %s 可以下单'%(date, symbol))
        return True


    def __lhb_strategy(self, lhb_dict):
        for key,lhb_pair in lhb_dict.items():
            signal = self.__lhb_price_strategy(lhb_pair)

    def on_lhb_event(self, ob, date):
        lhb_dict = self.__lhb_parser(ob, date)
        self.__lhb_strategy(lhb_dict)

