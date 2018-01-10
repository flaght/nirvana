#!/usr/bin/env python
# coding=utf-8

from collections import OrderedDict
from order import Order, CombOffset, OrderPrice, Direction, OrderStatus
from account import Account
from daily_record import DailyRecord, SummaryRecord
from daily_price import DailyPrice
from bize_lhb import BizeLHB, LHBPair
import pandas as pd
import numpy as np
import time

DEFAULT_CASH = 2000000


class Nirvana(object):
    __strategy_id = 1002
    __account_id = 10001

    # 印花税:千分之一  交易佣金:千分之一点五  过户费:千分之一
    def __init__(self, limit_order):

        self.__sl = 0.03  # 止损
        self.__tp = 0.08  # 止盈

        self.__commission_ratio = 0.0015  # 交易佣金
        self.__stamp_ratio = 0.001  # 印花税率
        self.__transfer_ratio = 0.001  # 过户费率

        self.lhb = OrderedDict()

        self.__limit_order = OrderedDict()  # 委托单队列

        self.__history_limit_order = OrderedDict()  # 历史委托单
        self.__history_limit_volumes = OrderedDict()  # 历史成交记录

        self.__working_limit_order = limit_order

        self.__trader_record = OrderedDict()  # 交易记录存储

        self.__account = Account()
        self.__account.set_account_id(self.__account_id)
        self.__account.set_init_cash(DEFAULT_CASH)

        self.long_volumes = OrderedDict()  # 持有多头仓
        self.short_volumes = OrderedDict()  # 持有空头仓
        self.__init_lhb_chg()

    def __reset(self):
        self.__limit_order.clear()
        self.__history_limit_volumes.clear()
        self.__history_limit_order.clear()

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
        if bize_buy_two is None and bize_buy_one is not None:  # 只有买一方， 防止一家独大
            # print('%d: %s 只有买一方，存在一家独大危险'%(date, symbol))
            return False
        if bize_buy_one.amount() / bize_buy_two.amount() > 1.5:  # 买一方和买二方相差太大
            # print('%d: %s 买一方和买二方相差太大'%(date, symbol))
            return False

        bize_sale_opp = lhb_pair.bize_sale_from_code(bize_buy_one.bize_code())
        if bize_sale_opp is not None:
            # print('%d: %s 买一方非单纯买方'%(date, symbol))
            return False
        return True

    def __lhb_price_strategy(self, lhb_pair):
        daily_price = lhb_pair.daily_price()
        symbol = lhb_pair.symbol()
        date = lhb_pair.date()
        if self.lhb[lhb_pair.chg_type()] == -1:  # 负面上榜不下单
            # print('%d: %s 负面上榜不下单'%(date, symbol))
            return False

        bize_buy_one = lhb_pair.bize_buy_from_pos(0)
        bize_buy_two = lhb_pair.bize_buy_from_pos(1)
        bize_sale_one = lhb_pair.bize_sale_from_pos(0)

        if bize_sale_one is not None and bize_buy_two is None:  # 只有卖方
            # print('%d: %s 只有卖方'%(date, symbol))
            return False

        if bize_sale_one is None and bize_buy_one is not None:  # 只有买方
            r = self.__lhb_buy_price(bize_buy_one, bize_buy_two, lhb_pair, date, symbol)
            if r == False:
                return False
            else:
                # print('%d: %s 单方博弈可以下单'%(date, symbol))
                return True

        # 存在买卖双方
        if lhb_pair.buy_amount() < lhb_pair.sale_amount():  # 卖方小于买方不下单
            # print('%d: %s 卖方总额大于买方总额'%(date, symbol))
            return False

        r = self.__lhb_buy_price(bize_buy_one, bize_buy_two, lhb_pair, date, symbol)
        if r == False:
            return False
        else:
            # print('%d: %s 双方博弈可以下单'%(date, symbol))
            return True

    def order_close(self, symbol, stop_price, hold_volume_id, amount, create_time):
        order = self.__create_order_price(symbol, stop_price, amount, hold_volume_id, CombOffset.close,
                                          Direction.sell_direction, OrderPrice.limit_price,
                                          create_time)
        order.dump()
        self.__working_limit_order[order.order_id()] = order

    def order_open(self, symbol, avg_price, amount, create_time):
        order = self.__create_order_price(symbol, avg_price, amount, 0, CombOffset.open,
                                          Direction.buy_direction, OrderPrice.avg_price,
                                          create_time)

        order.dump()
        self.__working_limit_order[order.order_id()] = order

    # 先以当前行情均价创建，成交以当天行情均价成交
    def __create_order_price(self, symbol, avg_price, amount, hold_volume_id,
                             off_flag, direction, price_type, create_time):
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
        daily_price = lhb_pair.daily_price()
        symbol = lhb_pair.symbol()
        signal = self.__lhb_price_strategy(lhb_pair)
        return signal, symbol, daily_price
        # if signal:
        #    self.order_open(symbol, daily_price.avg_price(), 1, date)

    def __lhb_strategy(self, lhb_dict, date):
        for key, lhb_pair in lhb_dict.items():
            signal, symbol, daily_price = self.__strategy_commit(lhb_pair, date)
            if not signal:
                return
        self.order_open(symbol, daily_price.avg_price(), 1, date)

    def __position_trade(self, date, daily_price, position):
        sl_price = position.limit_price() * (1 - self.__sl)  # 止损价
        tp_price = position.limit_price() * (1 + self.__tp)  # 止盈价

        high_price = daily_price.today_high()
        low_price = daily_price.today_low()

        # 判断是否达到止盈
        if tp_price <= high_price:
            # print('日期:%d 股票:%s 达到止盈价，可以平仓 止盈价:%f, 最高价:%f'%(date, position.symbol(), tp_price, high_price))
            self.order_close(position.symbol(), tp_price, position.trader_id(), 1, date)
        if sl_price >= low_price:
            # print('日期:%d 股票:%s 达到止损价，可以平仓 止损价:%f, 最低价:%f'%(date, position.symbol(), sl_price, low_price))
            self.order_close(position.symbol(), sl_price, position.trader_id(), 1, date)

            # print('date:%d,symbol:%s,limit_price:%f,sl_price:%f,tp_price:%f,high_price:%f,low_price:%f'%(
            #    date, position.symbol(), position.limit_price(),sl_price,tp_price,high_price,low_price))

    def on_market_data(self, date, daily_price_list):
        for k, value in self.long_volumes.items():
            if daily_price_list.has_key(value.symbol()[2:]):
                daily_price = daily_price_list[value.symbol()[2:]]
                if daily_price.is_use == 1 or daily_price.is_use == -1:
                    self.__position_trade(date, daily_price, value)

    def on_order(self, order):
        if order.status() == OrderStatus.entrust_traded:  # 委托成功锁住费用
            self.__account.insert_order_cash(order.cost(), order.fee())
            self.__limit_order[order.order_id()] = order
        elif order.status() == OrderStatus.all_traded:  # 交易成功 改变状态
            self.__limit_order[order.order_id()] = order

    def on_volume(self, vol, order):
        # 从委托中删除
        del self.__limit_order[vol.order_id()]
        self.__history_limit_volumes[vol.trader_id()] = vol
        self.__history_limit_order[order.order_id()] = order
        vol.dump()

        if vol.comb_offset_flag() == CombOffset.open:  # 开仓
            self.__account.open_cash(order.cost(), vol.cost(), order.fee(), vol.fee())
            self.long_volumes[vol.trader_id()] = vol
        else:
            if self.long_volumes.has_key(order.hold_volume_id()):
                v = self.long_volumes[order.hold_volume_id()]
                del self.long_volumes[order.hold_volume_id()]
                profit = self.__account.close_cash(v, vol, order.fee())
                print('%s 平仓盈利:%f'%(vol.symbol(), profit))
                self.__account.dump()

    def on_lhb_event(self, ob, date):
        lhb_dict = self.__lhb_parser(ob, date)
        self.__lhb_strategy(lhb_dict, date)

    def calc_settle(self, date, daily_price_list):  # 计算当日结算
        daily_profit = 0.0
        print('calc_settle trade_date:%d' % date)
        for vid, value in self.long_volumes.items():
            if not daily_price_list.has_key(value.symbol()[2:]):
                continue
            daily_price = daily_price_list[value.symbol()[2:]]
            if not daily_price.is_use:
                latest_price = daily_price.latest_price()
            else:
                latest_price = daily_price.today_close()
            profit = (latest_price - value.limit_price()) * value.min_volume() * value.amount()
            daily_profit += profit
            print('symbol:%s, close_price %f, limit_price:%f, profit:%f' % [
                value.symbol(), daily_price.today_close(), value.limit_price(), profit])

        print('date:%d, position daily_profit:%f' % [date, daily_profit])
        self.__account.set_position_profit(daily_profit)
        self.__account.dump()
        record = DailyRecord()
        record.set_close_profit(self.__account.close_profit())
        record.set_position_profit(self.__account.position_profit())
        record.set_limit_volume(self.__history_limit_volumes)
        record.set_limit_order(self.__history_limit_order)
        record.set_fee(self.__account.fee())
        record.set_mktime(date)
        print('mkdate:%d, available_cash:%f, profit:%f' % (record.mktime(),
                                                           self.__account.available_cash(),
                                                           record.all_profit()))
        self.__trader_record[record.mktime()] = record
        self.__account.reset()
        self.__reset()

    def calc_result(self):
        max_profit = 0.0
        total_profit = 0.0
        for key, value in self.__trader_record.items():
            total_profit += value.all_profit()

        starting_cash = self.__account.starting_cash()
        base_value = (int(abs(total_profit) / starting_cash) + 1) * self.__account.starting_cash()
        print('all:%f, base_value:%f' % (total_profit, base_value))
        total_profit = 0.0

        df = pd.DataFrame(columns=['mktime', 'interests', 'value', 'retrace', 'chg', 'log_chg', 'profit'])
        # 计算每日权益，每日净值, 涨跌幅，回撤，日对数收益
        last_value = 0.0
        for mktime, daily_record in self.__trader_record.items():
            daily_record.set_base_value(base_value)
            daily_record.set_last_value(last_value)
            daily_record.set_max_profit(max_profit)
            daily_record.set_last_profit(total_profit)
            daily_record.calc_result()
            daily_record.dump()
            df = df.append(pd.DataFrame({'mktime': mktime, 'interests': daily_record.interests(),
                                         'value': daily_record.value(), 'retrace': daily_record.retrace(),
                                         'chg': daily_record.chg(), 'log_chg': daily_record.log_chg(),
                                         'profit': daily_record.all_profit()}, index=['mktime']), ignore_index=True)

            total_profit += daily_record.all_profit()
            if max_profit < total_profit:
                max_profit = total_profit
            last_value = daily_record.value()
            base_value += daily_record.all_profit()

        chg_mean = np.mean(df['log_chg'])
        chg_std = np.std(df['log_chg'])

        summary_record = SummaryRecord()
        summary_record.set_chg_mean(chg_mean)
        summary_record.set_chg_std(chg_std)
        summary_record.set_trade_count(df.shape[0])
        summary_record.set_final_value(df['value'].values[-1])
        summary_record.set_max_retr(np.min(df['retrace']))

        summary_record.calc_record(df[df['chg'] > 0.00].shape[0])
        summary_record.dump()
        df.to_csv(str(time.time()) + 'result_strange.csv', encoding='utf-8')
