#!/usr/bin/env python
# coding=utf-8
from mlog import MLog
from daily_price import DailyPrice
from collections import OrderedDict
'''
龙虎榜数据
'''


class LHBPair(object):
    def __init__(self):
        self.__daily_price = DailyPrice()
        self.code_bize_buy = OrderedDict() # 买方席位 key为id
        self.seq_bize_buy = OrderedDict() # key 为顺序
        self.code_bize_sale = OrderedDict()
        self.seq_bize_sale = OrderedDict()
        self.buy_amount = 0
        self.sale_amount = 0
        self.__chg_type = ''


    def chg_type(self):
        return self.__chg_type

    def set_chg_type(self, chg_type):
        self.__chg_type = chg_type

    def xq_parser(self, ob, symbol):
        self.__daily_price.xq_parser(ob)
        self.__daily_price.set_symbol(symbol)

    def daily_price(self):
        return self.__daily_price

    def buy_amount(self):
        return self.buy_amount

    def sale_amount(self):
        return self.sale_amount

    def bize_sale_from_pos(self, index):
        if self.seq_bize_sale.has_key(index):
            return self.seq_bize_sale[index]
        else:
            return None

    def bize_sale_from_code(self, code_id):
        if self.code_bize_sale.has_key(code_id):
            return self.code_bize_sale[code_id]
        else:
            return None
    
    def bize_buy_from_pos(self, index):
        if self.seq_bize_buy.has_key(index):
            return self.seq_bize_buy[index]
        else:
            return None

    def bize_buy_from_code(self, code_id):
        if self.code_bize_buy.has_key(code_id):
            return self.code_bize_buy[code_id]
        else:
            return None

    def set_bize_buy(self, bize_buy):
        self.code_bize_buy[bize_buy.bize_code()] = bize_buy
        self.seq_bize_buy[len(self.seq_bize_buy)] = bize_buy
        self.buy_amount += bize_buy.amount()

    def set_bize_sale(self, bize_sale):
        self.code_bize_sale[bize_sale.bize_code()] = bize_sale
        self.seq_bize_sale[len(self.seq_bize_sale)] = bize_sale
        self.sale_amount += bize_sale.amount()

class BizeLHB(object):

    def __init__(self):
        self.__trade_date = 0 # 交易日
        self.__symbol = '' # 归属股票编码
        self.__chg_type = '' # 涨跌类别
        self.__bize_code = '' # 编号
        self.__bize_name = '' # 名称
        self.__amount = 0.0 #  成交额
        self.__buy_vol = 0.0 # 买入量
        self.__buy_amount = 0.0 # 买入额
        self.__sale_vol = 0.0 # 卖出量
        self.__sale_amount = 0.0 # 卖出额
        self.__desc = '' # 上榜原因

    
    def xq_parser(self, ob):
        self.__trade_date = int(ob.get('tradedate'))
        self.__chg_type = ob.get('chgtype')
        self.__bize_code = ob.get('bizsunitcode')
        self.__bize_name = ob.get('bizsunitname')
        self.__amount = ob.get('amount')
        if ob.get('buyvol') is not None:
            self.__buy_vol = ob.get('buyvol')
        if ob.get('buyamt') is not None:
            self.__buy_amount = ob.get('buyamt')
        if ob.get('salevol') is not None:
            self.__sale_vol = ob.get('salevol')
        if ob.get('saleamt') is not None:
            self.__sale_amount = ob.get('saleamt')
        self.__desc = ob.get('typedesc')

    def dump(self):
        print('symbol:%s,trade_date:%d,chg_type:%s,bize_code:%s,bize_name:%s,amount:%f,buy_vol:%f,buy_amount:%f,sale_vol:%f,sale_amount:%f,desc:%s'%(
                            self.__symbol,
                           self.__trade_date,self.__chg_type,
                          self.__bize_code,self.__bize_name,self.__amount,
                          self.__buy_vol,self.__buy_amount,self.__sale_vol,
                          self.__sale_amount,self.__desc))


    def set_symbol(self, symbol):
        self.__symbol = symbol

    def trade_date(self):
        return self.__trade_date

    def symbol(self):
        return self.__symbol

    def name(self):
        return self.__name

    def chg_type(self):
        return self.__chg_type

    def bize_code(self):
        return self.__bize_code

    def bize_name(self):
        return self.__bize_name

    def amount(self):
        return self.__amount

    def buy_vol(self):
        return self.__buy_vol

    def buy_amount(self):
        return self.__buy_amount

    def sale_vol(self):
        return self.__sale_vol

    def sale_amount(self):
        return self.__sale_amount

    def desc(self):
        return self.__desc

