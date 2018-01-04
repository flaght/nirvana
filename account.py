#!/usr/bin/env python
# coding=utf-8

'''
账户资金
'''
from order import Direction, CombOffset
from mlog import MLog
class Account(object):
    def __init__(self):
        self.__account_id = '' #账户id
        self.__available_cash = 0.0 # 可用资金
        self.__locked_cash = 0.0 # 挂单锁住资金
        self.__margin = 0.0 # 正在使用保证金
        # self.__total_value = 0.0 # 总权益
        self.__starting_cash = 0.0 # 初始资金
        # self.__positions_value = 0.0 # 持仓价值
        # self.__pre_balance = 0.0 # 昨日账户结算净值
        self.__commission = 0.0 # 手续费
        self.__close_profit = 0.0 # 平仓盈亏
        self.__position_profit = 0.0 # 持仓盈亏
        self.__deposit = 0 # 累计入金金额
        self.__withdraw = 0 # 累计出金金额


    def reset(self):
        self.__locked_cash = 0.0
        self.__margin = 0.0
        self.__commission = 0.0
        self.__close_profit = 0.0
        self.__position_profit = 0.0

    def close_profit(self):
        return self.__close_profit

    def position_profit(self):
        return self.__position_profit

    def commission(self):
        return self.__commission

    def available_cash(self):
        return self.__available_cash

    def starting_cash(self):
        return self.__starting_cash

    def set_init_cash(self, init_cash):
        self.__available_cash +=  init_cash
        self.__deposit += init_cash
        self.__starting_cash += init_cash

    def set_account_id(self, account_id):
        self.__account_id = account_id

    def set_close_profit(self, h_vol, c_vol):
        self.__close_profit += (h_vol.limit_price() - c_vol.limit_price()) * (c_vol.amount() * c_vol.min_volume())

    #挂单资金操作, 保证金 手续费, 平仓挂单保证金设为0
    def insert_order_cash(self,margin, fee):
        if self.__available_cash < (margin + fee): # 可用资金不够时，补充资金
           self.set_init_cash(100000) 
        self.__available_cash -= (margin + fee) # 消耗的可用资金数
        self.__locked_cash += (margin + fee) # 挂单时被锁定的资金
        self.__commission += fee # 消耗的手续费
        self.__margin += margin # 消耗掉的保证金
        self.__withdraw += (margin + fee) # 出去的资金

    #撤单成功后资金操作, 保证金和手续费解封  平仓保证金设为0
    def canncel_order_cash(self, margin, fee):
        self.__available_cash += (margin + fee) # 保证金和手续费回到可用资金中
        self.__locked_cash -= (margin + fee) # 解锁保证金和可用资金
        self.__commission -= fee # 归还手续费
        
        self.__margin -= margin # 归还保证金
        
        self.__deposit += (margin + fee) # 进入的资金

    #建仓成功后，资金操作
    def open_cash(self, order_margin,volume_margin,order_fee, volume_fee):
        
        # 处理报单
        self.__locked_cash -= (order_margin + order_fee) #解锁锁住资金
        self.__available_cash += (order_margin + order_fee) # 归还订单保证金手续费
        
        self.__margin -= order_margin 

        self.__commission -= order_fee
        self.__deposit += (order_margin + order_fee)
        
        # 处理成交
        self.__available_cash -= (volume_margin + volume_fee) #扣除实际成交量的保证金和手续费
        self.__commission += volume_fee
        
        self.__margin += volume_margin

        self.__withdraw += (volume_margin + volume_fee)

    #平仓成功后，资金操作
    def close_cash(self, hold_v, cur_v, order_fee):
        #平仓后，建仓时候保证金退还，外加收益
        if hold_v.comb_offset_flag() == CombOffset.open and hold_v.direction() == Direction.buy_direction: # 多头开仓
            profit = (cur_v.limit_price() - hold_v.limit_price()) *  cur_v.amount() * cur_v.min_volume()
        elif hold_v.comb_offset_flag() == CombOffset.open and hold_v.direction() == Direction.sell_direction: # 空头开仓
            profit = (hold_v.limit_price() - cur_v.limit_price()) * cur_v.amount() * cur_v.min_volume()


        self.__locked_cash -= order_fee # 解锁手续费，平仓建仓没有保证金
        self.__available_cash += order_fee # 退还下单时候手续费
        self.__available_cash -= cur_v.fee() # 扣除成交的手续费
        
        self.__available_cash += (profit + hold_v.margin()) # 平仓后退回手续费和保证金 
        
        self.__commission -= order_fee
        self.__commission += cur_v.fee()

        self.__deposit += (order_fee + profit + hold_v.margin())
        self.__withdraw -= (cur_v.fee())

        self.__close_profit += profit

        self.__margin -= hold_v.margin() #归还使用保证金


    def log(self):
        return ("account:%d,available_cash:%f,locked_cash:%f,margin:%f,colse_profit:%f,commission:%f,starting_cash:%f,deoposit:%f,withdraw:%f"%(self.__account_id,
                        self.__available_cash,self.__locked_cash,self.__margin,self.__close_profit, self.__commission,self.__starting_cash, self.__deposit,self.__withdraw))
    def dump(self):
        MLog.write().debug(self.log())
