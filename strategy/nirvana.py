#!/usr/bin/env python
# coding=utf-8
import sys
from collections import OrderedDict
sys.path.append("..")
from td_base.order import Order, CombOffset, OrderPrice, Direction, OrderStatus
from td_base.account import Account
from td_base.daily_record import DailyRecord, SummaryRecord
from td_base.daily_price import DailyPrice
from lhb.bize_lhb import BizeLHB, LHBPair, Bize, LHBChg
from db.sqlite_manage_model import SQLLiteStorage
import config as Config
from mlog import MLog

DEFAULT_CASH = 100000


class Nirvana(object):

    """Summary of class here.
        龙虎榜策略类

        印花税:千分之一
        交易佣金:千分之一点五
        过户费:千分之一
    Attributes:
        limit_order: 委托单队列
    """

    __strategy_id = 1002
    __account_id = 10001

    def __init__(self, limit_order, lb = 1):

        self._lb = lb
        self.__sl = 0.03  # 止损
        self.__tp = 0.06  # 止盈

        self.__commission_ratio = 0.0015  # 交易佣金
        self.__stamp_ratio = 0.001  # 印花税率
        self.__transfer_ratio = 0.001  # 过户费率

        self.lhb = OrderedDict()

        self.__limit_order = OrderedDict()  # 委托单队列

        self.__history_limit_order = OrderedDict()  # 历史委托单
        self.history_limit_volumes = OrderedDict()  # 历史成交记录

        self.__working_limit_order = limit_order

        self.__trader_record = OrderedDict()  # 交易记录存储

        self.account = Account()
        self.account.set_account_id(self.__account_id)
        self.account.set_init_cash(400000)

        self.long_volumes = OrderedDict()  # 持有多头仓
        self.short_volumes = OrderedDict()  # 持有空头仓
        
        self.bize_dict = OrderedDict()  # 营业部，机构基本信息
        self.__init_lhb_chg()
        self.__init_bize()

    def __reset(self):
        """Performs operation __reset blah.
            重置当日统计的信息

        Attributes:
        """
        self.__limit_order.clear()
        self.history_limit_volumes.clear()
        self.__history_limit_order.clear()

    def __init_bize(self):
        """Performs operation __init_bize blah.
            从bize.db读取营业厅信息
        Attributes:
        """
        db_engine = SQLLiteStorage(Config.BIZE_DB_FILE, 0)
        result_list = db_engine.get_data('select xid,name,jianpin,identity,identity_name from bize')
        for bize_rl in result_list:
            bize = Bize()
            bize.set_xid(bize_rl[0])
            bize.set_name(bize_rl[1])
            bize.set_jianpin(bize_rl[2])
            if bize.xid() / 10 == 1999999:
                bize.set_identity(100)
                bize.set_identity_name(u'机构专用')
            else:
                bize.set_identity(bize_rl[3])
                bize.set_identity_name(bize_rl[4])
            self.bize_dict[bize.xid()] = bize

    def __get_bize(self, xid):
        """Performs operation __get_bize blah.
            获取营业厅信息
        Attributes:
            xid:营业厅id
        """
        if self.bize_dict.has_key(xid):
            return self.bize_dict[xid]
        return None

    def __init_lhb_chg(self):
        """Performs operation __init_lhb_chg blah.
            从bize.db读取龙虎榜涨跌分类
        Attributes:
        """
        db_engine = SQLLiteStorage(Config.BIZE_DB_FILE, 0)
        result_list = db_engine.get_data('select xid,chg_type,direction,name,chg_desc from class')
        for cls_rl in result_list:
            lhb_chg = LHBChg()
            lhb_chg.set_xid(cls_rl[0])
            lhb_chg.set_chg_type(cls_rl[1])
            lhb_chg.set_direction(cls_rl[2])
            lhb_chg.set_name(cls_rl[3])
            lhb_chg.set_chg_desc(cls_rl[4])
            self.lhb[lhb_chg.chg_type()] = lhb_chg

    def __lhb_pair(self, lhb_dict, bize_ob, daily_price_ob, symbol, date, direction):
        """Performs operation __lhb_pair blah.
            存储龙虎榜买卖方信息
        Attributes:
            lhb_dict:存储龙虎榜字典
            bize_ob:雪球龙虎榜信息
            daily_price_ob:雪球龙虎榜日行情
            symbol:交易标的
            date:交易日期
            direction:买卖方向, 1:买  -1:卖
        """
        for ob in bize_ob:
            bize_lhb = BizeLHB()
            bize_lhb.xq_parser(ob)
            bize_lhb.set_symbol(symbol)
            bize = self.__get_bize(int(bize_lhb.bize_code()))
            if bize is not None:
                bize_lhb.set_bize(bize)
            # bize_lhb.dump()
            # 查看对应类型是否在
            if lhb_dict.has_key(bize_lhb.chg_type()):
                lhb_pair = lhb_dict[bize_lhb.chg_type()]
            else:
                lhb_pair = LHBPair()
                if daily_price_ob is not None:
                    lhb_pair.xq_parser(daily_price_ob, symbol)
                lhb_pair.set_chg_type(bize_lhb.chg_type())
                lhb_pair.set_symbol(symbol)
                lhb_pair.set_date(date)
            if direction == 0:
                lhb_pair.set_bize_buy(bize_lhb)
            else:
                lhb_pair.set_bize_sale(bize_lhb)

            lhb_dict[lhb_pair.chg_type()] = lhb_pair

    def __lhb_parser(self, lhb, date):
        """Performs operation __lhb_parser blah.
            解析龙虎榜买卖方信息
        Attributes:
            lhb:雪球龙虎榜信息
            date:交易日期
        """
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
        self.__lhb_pair(lhb_dict, sale_bize_ob, daily_price_ob, symbol, date, 1)
        return lhb_dict

    def __lhb_buy_price(self, bize_buy_one, bize_buy_two, lhb_pair, date, symbol):
        """Performs operation __lhb_buy_price blah.
            龙虎榜买方席位交易量判断
        Attributes:
            bize_buy_one:买一席位身份
            bize_buy_two:买二席位身份
            lhb_pair:龙虎榜买卖双方
            date:交易日期
            symbol:交易标的
        """
        
        if bize_buy_two is None and bize_buy_one is not None:  # 只有买一方， 防止一家独大
            # MLog.write().debug('%d: %s 只有买一方，存在一家独大危险'%(date, symbol))
            return False

        if bize_buy_one.amount() / bize_buy_two.amount() > 1.5:  # 买一方和买二方相差太大
            # MLog.write().debug('%d: %s 买一方和买二方相差太大'%(date, symbol))
            return False

        bize_sale_opp = lhb_pair.bize_sale_from_code(bize_buy_one.bize_code())
        if bize_sale_opp is not None:
            # MLog.write().debug('%d: %s 买一方非单纯买方'%(date, symbol))
            return False
        
        return True


    def __lhb_identity_sale(self, bize_sale, date, symbol):
        """Performs operation __lhb_identity_sale blah.
            龙虎榜卖方身份信息判断
        Attributes:
            bize_sale:龙虎榜卖方信息
            date:交易日期
            symbol:交易标的
        """
        for k,bize_lhb in bize_sale.items():
            if bize_lhb.bize().identity() == 100 or bize_lhb.bize().identity() == 1 or bize_lhb.bize().identity() == 1 or bize_lhb.bize().identity() == 3:
                MLog.write().info('%d %s 卖方席位中有%s, 不能下单'%(date,symbol,  bize_lhb.bize().identity_name()))
                return False
        return True

    def __lhb_identity_buy(self, lhb_pair, date, symbol):
        """Performs operation __lhb_identity_buy blah.
            龙虎榜买方方身份信息判断
        Attributes:
            lhb_pair:龙虎榜买卖方信息
            date:交易日期
            symbol:交易标的

        买方席位中有重要身份，只要买方总量大于卖方总量则可以下单
        """

        is_identity = 0
        latest_bize = None
        for k, bize_lhb in lhb_pair.code_bize_buy().items():
            if bize_lhb.bize().identity() == 100 or bize_lhb.bize().identity() == 1 or bize_lhb.bize().identity() == 2 or bize_lhb.bize().identity() == 3:
                is_identity = 1
                latest_bize = bize_lhb.bize()
                break
        if is_identity == 0:
            return False

        # 含有重要席位,买方总额大于卖方总额
        if lhb_pair.buy_amount() <= lhb_pair.sale_amount():
            MLog.write().info('%d %s 卖方没有特殊席位，买方中有%s, 但买总额(%d)小于等于卖方总额(%d)不能下单'%(date, 
                                symbol, latest_bize.identity_name(), lhb_pair.buy_amount(), lhb_pair.sale_amount()))
            return False

        MLog.write().info('%d %s 卖方没有特殊席位，买方中有%s, 买总额(%d)大于卖方总额(%d)，可以下单'%(
            date, symbol, latest_bize.identity_name(), lhb_pair.buy_amount(), lhb_pair.sale_amount()))
        return True

    def __lhb_identity_strategy(self, lhb_pair):
        """Performs operation __lhb_identity_strategy blah.
            判断龙虎榜买卖方身份
        Attributes:
            lhb_pair:龙虎榜买卖方信息
        """

        symbol = lhb_pair.symbol()
        date = lhb_pair.date()
        lhb_chg = self.lhb[lhb_pair.chg_type()]
        if lhb_chg.direction() == -1:  # 负面上榜不下单
            MLog.write().info('%d: %d %s %s 负面上榜不下单'%(date, lhb_chg.direction(),  symbol,lhb_chg.name()))
            return False

        # 检测卖方中是否含有机构，知名游资，一线游资,敢死队
        if self.__lhb_identity_sale(lhb_pair.code_bize_sale(), date, symbol) == False:
            return -1

        buy_singal = self.__lhb_identity_buy(lhb_pair, date, symbol)

        if buy_singal:
            return 1

        MLog.write().info('%d %s 买卖双方没有特殊席位' %(date, symbol))
        return 0

    def __lhb_price_strategy(self, lhb_pair):
        """Performs operation __lhb_price_strategy blah.
            判断龙虎榜买卖方交易量
        Attributes:
            lhb_pair:龙虎榜买卖方信息
        """
        daily_price = lhb_pair.daily_price()
        symbol = lhb_pair.symbol()
        date = lhb_pair.date()
        lhb_chg = self.lhb[lhb_pair.chg_type()]
        if lhb_chg.direction() == -1:  # 负面上榜不下单
            MLog.write().info('%d %d %s %s 负面上榜不下单'%(date, lhb_chg.direction(), symbol, lhb_chg.name()))
            return False

        MLog.write().info('%d %s %s 正面上榜'%(date, symbol, lhb_chg.name()))
        bize_buy_one = lhb_pair.bize_buy_from_pos(0)
        bize_buy_two = lhb_pair.bize_buy_from_pos(1)
        bize_sale_one = lhb_pair.bize_sale_from_pos(0)


        if bize_sale_one is not None and bize_buy_two is None:  # 只有卖方
            MLog.write().info('%d: %s 只有卖方 不能下单 '%(date, symbol))
            return False

        if bize_sale_one is None and bize_buy_one is not None:  # 只有买方
            r = self.__lhb_buy_price(bize_buy_one, bize_buy_two, lhb_pair, date, symbol)
            if r == False:
                return False
            else:
                MLog.write().info('%d: %s 买方单方博弈可以下单'%(date, symbol))
                return True

        # 存在买卖双方
        if lhb_pair.buy_amount() < lhb_pair.sale_amount():  # 卖方小于买方不下单
            MLog.write().info('%d: %s 卖方总额大于买方总额 不能下单'%(date, symbol))
            return False

        r = self.__lhb_buy_price(bize_buy_one, bize_buy_two, lhb_pair, date, symbol)
        if r == False:
            return False
        else:
            MLog.write().info('%d: %s 双方博弈可以下单'%(date, symbol))
            return True

    def order_close(self, symbol, stop_price, hold_volume_id, amount, create_time):
        """Performs operation order_close blah.
            下平仓单
        Attributes:
            symbol:交易标的
            stop_price:平仓价
            hold_volume_id:持仓的ID
            amount:平仓手数
            create_time:创建时间
        """
        order = self.__create_order_price(symbol, stop_price, amount, hold_volume_id, CombOffset.close,
                                          Direction.sell_direction, OrderPrice.limit_price,
                                          create_time)
        # order.dump()
        self.__working_limit_order[order.order_id()] = order

    def order_open(self, symbol, avg_price, amount, create_time):
        """Performs operation order_open blah.
            下开仓单
        Attributes:
            symbol:交易标的
            avg_price:开仓价
            amount:平仓手数
            create_time:创建时间
        """
        order = self.__create_order_price(symbol, avg_price, amount, 0, CombOffset.open,
                                          Direction.buy_direction, OrderPrice.avg_price,
                                          create_time)

        # order.dump()
        self.__working_limit_order[order.order_id()] = order

    def __create_order_price(self, symbol, avg_price, amount, hold_volume_id,
                             off_flag, direction, price_type, create_time):

        """Performs operation order_open blah.
            下开仓单
        Attributes:
            symbol:交易标的
            avg_price:开仓价
            amount:平仓手数
            hold_volume_id:持仓的ID,若是开仓则为0
            off_flag:交易类别
            direction:交易方向
            price_type:交易单类型
            create_time:创建时间
        先以当前行情均价创建，成交以当天行情均价成交
        """
        order = Order()
        order.create_order_id()
        order.set_create_time(create_time)
        order.set_account_id(self.__account_id)
        order.set_symbol(symbol)
        order.set_comb_offset_flag(off_flag)
        order.set_order_price_type(OrderPrice.avg_price)
        order.set_limit_price(avg_price)
        order.set_direction(direction)
        order.set_amount(amount)
        order.set_hold_volume_id(hold_volume_id)
        order.set_strategy_id(self.__strategy_id)
        order.set_min_volume(100)
        order.set_commission(self.__commission_ratio)  # 佣金率
        if direction == Direction.sell_direction:  # 平仓才收印花税
            order.set_stamp(self.__stamp_ratio)
        else:
            order.set_stamp(0)

        if symbol.find('SH'):  # 沪市才收过户费
            order.set_transfer(self.__transfer_ratio)
        else:
            order.set_transfer(0)

        return order

    def __strategy_commit(self, lhb_pair, date):

        """Performs operation __strategy_commit blah.
            龙虎榜单个交易标的策略判断
        Attributes:
            lhb_pair:龙虎榜买卖方信息
            date:交易日
        """
        daily_price = lhb_pair.daily_price()
        symbol = lhb_pair.symbol()
        
        # identity_signal = self.__lhb_identity_strategy(lhb_pair)
        # if identity_signal == -1:
        #    signal = False
        # elif identity_signal == 1:
        #    signal = True
        # else:
        signal = self.__lhb_price_strategy(lhb_pair)
        return signal, symbol, daily_price
        # if signal:
        #    self.order_open(symbol, daily_price.avg_price(), 1, date)

    def __lhb_strategy(self, lhb_dict, date):
        """Performs operation __lhb_strategy blah.
            龙虎榜策略判断
        Attributes:
            lhb_dict:当天所有龙虎榜信息
            date:交易日
        """
        for key, lhb_pair in lhb_dict.items():
            signal, symbol, daily_price = self.__strategy_commit(lhb_pair, date)
            if not signal:
                if self._lb:
                    return signal, symbol
                else:
                    return signal, symbol
        if self._lb:
            self.order_open(symbol, daily_price.avg_price(), 1, date)
        return signal, symbol

    def __position_trade(self, date, daily_price, position):

        """Performs operation __position_trade blah.
            持仓判断,是否达到止盈止损
        Attributes:
            date:交易日
            daily_price:当天日行情
            position:标的的持仓信息
        """
        
        if date <= position.create_time():  # 防止當天購買又當天賣出情況
            return

        sl_price = position.limit_price() * (1 - self.__sl)  # 止损价
        tp_price = position.limit_price() * (1 + self.__tp)  # 止盈价

        high_price = daily_price.today_high()
        low_price = daily_price.today_low()

        # 判断是否达到止盈
        if tp_price <= high_price:
            MLog.write().debug('日期:%d 股票:%s 达到止盈价，可以平仓 止盈价:%f, 最高价:%f'%(date, position.symbol(), tp_price, high_price))
            self.order_close(position.symbol(), tp_price, position.trader_id(), 1, date)
        if sl_price >= low_price:
            MLog.write().debug('日期:%d 股票:%s 达到止损价，可以平仓 止损价:%f, 最低价:%f'%(date, position.symbol(), sl_price, low_price))
            self.order_close(position.symbol(), sl_price, position.trader_id(), 1, date)

            # MLog.write().debug('date:%d,symbol:%s,limit_price:%f,sl_price:%f,tp_price:%f,high_price:%f,low_price:%f'%(
            #    date, position.symbol(), position.limit_price(),sl_price,tp_price,high_price,low_price))

    def on_market_data(self, date, daily_price_list):
        """Performs operation on_market_data blah.
            接收行情数据
        Attributes:
            date:交易日
            daily_price_list:当天日行情列表
        """
        for k, value in self.long_volumes.items():
            if daily_price_list.has_key(value.symbol()[2:]):
                daily_price = daily_price_list[value.symbol()[2:]]
                # MLog.write().debug('date:%d, symbol:%s, use:%d'%(date, daily_price.symbol(), daily_price.is_use()))
                if daily_price.is_use() == 1 or daily_price.is_use() == -1:
                    self.__position_trade(date, daily_price, value)

    def on_order(self, order):
        """Performs operation on_order blah.
            接收委托单
        Attributes:
            order:委托单
        """
        if order.status() == OrderStatus.entrust_traded:  # 委托成功锁住费用
            if order.comb_offset_flag() == CombOffset.open:
                self.account.insert_order_cash(order.cost(), order.fee())
            else:
                self.account.insert_order_cash(0, order.fee())
            self.__limit_order[order.order_id()] = order
        elif order.status() == OrderStatus.all_traded:  # 交易成功 改变状态
            self.__limit_order[order.order_id()] = order

    def on_volume(self, vol, order):
        """Performs operation on_volume blah.
            接收成交量单
        Attributes:
            vol:成交量单
            order:成交量单对应的委托单
        """
        # 从委托中删除
        del self.__limit_order[vol.order_id()]
        self.history_limit_volumes[vol.trader_id()] = vol
        self.__history_limit_order[order.order_id()] = order

        if vol.comb_offset_flag() == CombOffset.open:  # 开仓
            self.account.open_cash(order.cost(), vol.cost(), order.fee(), vol.fee())
            self.long_volumes[vol.trader_id()] = vol
        else:
            if self.long_volumes.has_key(order.hold_volume_id()):
                v = self.long_volumes[order.hold_volume_id()]
                profit = self.account.close_cash(v, vol, order.fee())
                MLog.write().debug('%s 平仓盈利:%f'%(vol.symbol(), profit))
                del self.long_volumes[order.hold_volume_id()]

    def on_lhb_event(self, ob, date):
        """Performs operation on_lhb_event blah.
            接收每日龙虎榜信息
        Attributes:
            ob:雪球龙虎榜信息
            date:交易日
        """
        lhb_dict = self.__lhb_parser(ob, date)
        signal, symbol = self.__lhb_strategy(lhb_dict, date)
        if not self._lb:
            return signal, symbol

    def calc_settle(self, date, daily_price_list):
        """Performs operation calc_settle blah.
            收盘后对当日进行结算
        Attributes:
            daily_price_list:当日行情列表
            date:交易日
        """
        daily_profit = 0.0
        daily_cost = 0.0
        MLog.write().debug('calc_settle trade_date:%d' % date)
        for vid, value in self.long_volumes.items():
            if not daily_price_list.has_key(value.symbol()[2:]):
                continue
            daily_price = daily_price_list[value.symbol()[2:]]

            # 若停牌则以最近收盘价为结算价
            if daily_price.is_use() == 0 :
                settle_price = daily_price.latest_price()

            else:
                settle_price = daily_price.today_close() 
            
            value.set_settle_price(date,settle_price)

            daily_profit += value.daily_profit()

            daily_cost += value.cost()
            # MLog.write().debug('symbol:%s, settle_price %f, limit_pricee:%f, daily_profit:%f profit:%f' % (
            #    value.symbol(), settle_price, value.limit_price(), value.daily_profit(), value.profit()))
            
            self.long_volumes[vid] = value
            
            if self.history_limit_volumes.has_key(vid):
                self.history_limit_volumes[vid] = value

        # MLog.write().debug('date:%d, position daily_profit:%f' % (date, daily_profit))
        
        daily_fee = 0.0
        for vid,vvol in self.history_limit_volumes.items():
            daily_fee += vvol.fee()

        self.account.set_position_profit(daily_profit)
        record = DailyRecord()
        record.set_position_cost(daily_cost) # 当日持仓成本 
        record.set_close_profit(self.account.close_profit()) # 当日平仓盈亏
        record.set_position_profit(self.account.position_profit()) # 当日持仓盈亏
        record.set_limit_volume(self.history_limit_volumes) # 当日交易记录
        record.set_limit_order(self.__history_limit_order) # 当日下单记录 
        record.set_long_volume(self.long_volumes) # 当日持仓记录
        record.set_fee(daily_fee) # 当日手续费消耗
        record.set_mktime(date)

        self.__trader_record[record.mktime()] = record
        self.account.reset()
        self.__reset()

    def calc_result(self):
        """Performs operation calc_result blah.
            计算当日的权益,净值,涨跌幅,回撤等
        Attributes:
        """

        max_profit = 0.0
        total_profit = 0.0
        for key, value in self.__trader_record.items():
            total_profit += value.all_profit()

        starting_cash = self.account.starting_cash()
        base_value = (int(abs(total_profit) / starting_cash) + 1) * self.account.starting_cash()
        MLog.write().debug('all:%f, base_value:%f' % (total_profit, base_value))
        total_profit = 0.0

        summary_record = SummaryRecord()
        # 计算每日权益，每日净值, 涨跌幅，回撤，日对数收益
        last_value = 1.0
        last_available_cash = base_value
        for mktime, daily_record in self.__trader_record.items():
            daily_record.set_base_value(base_value)
            daily_record.set_last_value(last_value)
            daily_record.set_max_profit(max_profit)
            daily_record.set_last_profit(total_profit)
            daily_record.set_last_available_cash(last_available_cash)
            daily_record.calc_result()
            daily_record.dump()
            summary_record.record_volume(daily_record.mktime(), daily_record.volume_tocsv(),
                                         daily_record.position_tocsv())
            summary_record.record_order(daily_record.mktime(), daily_record.order_tocsv())

            summary_record.record_daily(daily_record.to_csv(),daily_record.to_dataframe())

            total_profit += daily_record.all_profit()
            if max_profit < total_profit:
                max_profit = total_profit
            last_value = daily_record.value()
            last_available_cash = daily_record.last_available_cash() 

        summary_record.calc_record()
        summary_record.summary_record()
