#!/usr/bin/env python
# coding=utf-8
import sys
from mlog import MLog
from collections import OrderedDict
sys.path.append("..")
from td_base.daily_price import DailyPrice

class Bize(object):
    """Summary of class here.
        龙虎榜营业厅信息
        1,一线游资，
        2,知名游资
        3,敢死队
        4,跟风高手
        5,毒瘤
        6,新股专家
        100, 机构
    Attributes:
    """

    def __init__(self):
        self.__xid = 0  # 营业厅id
        self.__name = ''  # 营业厅名称
        self.__jianpin = ''  # 营业厅拼音
        self.__identity = 0  # 身份标识
        self.__identity_name = '' #身份名称

    def set_xid(self, xid):
        self.__xid = xid

    def set_name(self, name):
        self.__name = name

    def set_jianpin(self, jianpin):
        self.__jianpin = jianpin

    def set_identity(self, identity):
        self.__identity = identity

    def set_identity_name(self, identity_name):
        self.__identity_name = identity_name

    def xid(self):
        return self.__xid

    def name(self):
        return self.__name

    def jianpin(self):
        return self.__jianpin

    def identity(self):
        return self.__identity

    def identity_name(self):
        return self.__identity_name


class LHBPair(object):
    """Summary of class here.
       龙虎榜信息类

    Attributes:
    """

    def __init__(self):
        self.__daily_price = DailyPrice()  # 当日行情信息
        self.__code_bize_buy = OrderedDict()  # 买方席位 key为营业厅编码
        self.__seq_bize_buy = OrderedDict()  # key为顺序席位顺序
        self.__code_bize_sale = OrderedDict()  # 卖方席位 key为营业厅编码
        self.__seq_bize_sale = OrderedDict()  # key为顺序席位顺序
        self.__buy_amount = 0  # 买方总量
        self.__sale_amount = 0  # 卖方总量
        self.__chg_type = ''  # 上榜原因类别

        self.__date = 0  # 交易日
        self.__symbol = ''  # 交易标的

    def date(self):
        return self.__date

    def symbol(self):
        return self.__symbol

    def chg_type(self):
        return self.__chg_type


    def code_bize_buy(self):
        return self.__code_bize_buy

    def seq_bize_buy(self):
        return self.__seq_bize_buy

    def code_bize_sale(self):
        return self.__code_bize_sale

    def seq_bize_sale(self):
        return self.__seq_bize_sale

    def set_date(self, date):
        self.__date = date

    def set_symbol(self, symbol):
        self.__symbol = symbol

    def set_chg_type(self, chg_type):
        self.__chg_type = chg_type

    def xq_parser(self, ob, symbol):
        """Performs operation xq_parser blah.
            解析雪球龙虎榜json信息


        Attributes:
            ob: json信息
            symbol: 对应标的代码
        """
        self.__daily_price.xq_parser(ob)
        self.__daily_price.set_symbol(symbol)

    def daily_price(self):
        return self.__daily_price

    def buy_amount(self):
        return self.__buy_amount

    def sale_amount(self):
        return self.__sale_amount

    def bize_sale_from_pos(self, index):

        """Performs operation bize_sale_from_pos blah.
            通过位置获取营业厅信息


        Attributes:
            index: 位置
        """

        if self.__seq_bize_sale.has_key(index):
            return self.__seq_bize_sale[index]
        else:
            return None

    def bize_sale_from_code(self, code_id):

        """Performs operation bize_sale_from_pos blah.
            通过营业厅代码获取营业厅信息


        Attributes:
            code_id: 营业厅代码
        """
        if self.__code_bize_sale.has_key(code_id):
            return self.__code_bize_sale[code_id]
        else:
            return None

    def bize_buy_from_pos(self, index):

        """Performs operation bize_buy_from_pos blah.
            通过位置获取营业厅信息


        Attributes:
            index: 位置
        """

        if self.__seq_bize_buy.has_key(index):
            return self.__seq_bize_buy[index]
        else:
            return None

    def bize_buy_from_code(self, code_id):
        """Performs operation bize_buy_from_code blah.
            通过营业厅代码获取营业厅信息


        Attributes:
            code_id: 营业厅代码
        """
        if self.__code_bize_buy.has_key(code_id):
            return self.__code_bize_buy[code_id]
        else:
            return None

    def set_bize_buy(self, bize_buy):
        """Performs operation set_bize_buy blah.
            存储买方席位信息

        Attributes:
            bize_buy: 买方信息信息
        """
        self.__code_bize_buy[bize_buy.bize_code()] = bize_buy
        self.__seq_bize_buy[len(self.__seq_bize_buy)] = bize_buy
        self.__buy_amount += bize_buy.amount()

    def set_bize_sale(self, bize_sale):
        """Performs operation set_bize_sale blah.
            存储卖方席位信息

        Attributes:
            bize_buy: 卖方信息信息
        """

        self.__code_bize_sale[bize_sale.bize_code()] = bize_sale
        self.__seq_bize_sale[len(self.__seq_bize_sale)] = bize_sale
        self.__sale_amount += bize_sale.amount()


class BizeLHB(object):

    """Summary of class here.
       买/卖单方信息,营业厅上榜原因,参与标的及营业厅基本信息

    Attributes:
    """

    def __init__(self):
        self.__trade_date = 0  # 交易日
        self.__symbol = ''  # 归属股票编码
        self.__chg_type = ''  # 涨跌类别
        self.__bize_code = ''  # 编号
        self.__bize_name = ''  # 名称
        self.__amount = 0.0  # 成交额
        self.__buy_vol = 0.0  # 买入量
        self.__buy_amount = 0.0  # 买入额
        self.__sale_vol = 0.0  # 卖出量
        self.__sale_amount = 0.0  # 卖出额
        self.__desc = ''  # 上榜原因
        self.__bize = Bize()  # 营业部信息

    def xq_parser(self, ob):
        """Performs operation set_bize_sale blah.
            解析雪球json信息

        Attributes:
            ob: json格式信息
        """
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
        MLog.write().debug(
        'symbol:%s,trade_date:%d,chg_type:%s,bize_code:%s,bize_name:%s,amount:%f,buy_vol:%f,buy_amount:%f,sale_vol:%f,sale_amount:%f,desc:%s' % (
            self.__symbol,
            self.__trade_date, self.__chg_type,
            self.__bize_code, self.__bize_name, self.__amount,
            self.__buy_vol, self.__buy_amount, self.__sale_vol,
            self.__sale_amount, self.__desc))

    def set_bize(self, bize):

        """Performs operation set_bize blah.
            设置营业厅信息
        Attributes:
            bize: 营业厅信息
        """

        self.__bize.set_xid(bize.xid())
        self.__bize.set_name(bize.name())
        self.__bize.set_jianpin(bize.jianpin())
        self.__bize.set_identity(bize.identity())
        self.__bize.set_identity_name(bize.identity_name())

    def set_symbol(self, symbol):
        self.__symbol = symbol


    def bize(self):
        return self.__bize

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


class LHBChg(object):
    """Summary of class here.
        龙虎榜上榜信息类

    Attributes:
    """

    def __init__(self):
        self.__xid = 0  # 类别id
        self.__chg_type = u''  # 类别标识 主要用于雪球区分
        self.__name = ''  # 类别名称
        self.__direction = 0  # 类别方向(负中正)
        self.__chg_desc = ''  # 类别描述

    def set_xid(self, xid):
        self.__xid = xid

    def set_chg_type(self, chg_type):
        self.__chg_type = chg_type

    def set_name(self, name):
        self.__name = name

    def set_direction(self, direction):
        self.__direction = direction

    def set_chg_desc(self, chg_desc):
        self.__chg_desc = chg_desc

    def xid(self):
        return self.__xid

    def chg_type(self):
        return self.__chg_type

    def name(self):
        return self.__name

    def direction(self):
        return self.__direction

    def chg_desc(self):
        return self.__chg_desc
