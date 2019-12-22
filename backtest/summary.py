# -*- coding: utf-8 -*-


import numpy as np
import pandas as pd


class Summary:
    def __init__(self):
        pass

    @property
    def data(self):
        """返回策略每日持仓头寸，持仓市值、基点收益、策略净值、基准指数净值等数据"""
        cum_ret = np.cumsum(np.array(self.ctx.broker.ret) + self.ctx.benchmark.iloc[0])
        df = pd.DataFrame({"Position": self.ctx.broker.total_position,
                           "MarketValue": self.ctx.broker.market_value,
                           "BasisRet": self.ctx.broker.ret,
                           "CumRet": cum_ret,
                           "BenchMark": self.ctx.benchmark}, index=self.ctx.trade_calc)
        df.index.name = "Date"
        return df

    @property
    def order_list(self):
        """返回订单信息：包括每笔交易开仓日期、开仓价格、平仓日期、平仓价格、期间收益以及持仓时间"""
        holding_days = []
        for i in range(len(self.ctx.broker.open_date)):
            delta = self.ctx.trade_calc.index(self.ctx.broker.close_date[i]) - \
                    self.ctx.trade_calc.index(self.ctx.broker.open_date[i])
            holding_days.append(delta)
        holding_ret = (np.array(self.ctx.broker.close_price) - np.array(self.ctx.broker.open_price)) * \
                      np.array(self.ctx.broker.order_position)
        df = pd.DataFrame({"position": self.ctx.broker.order_position,
                           "start_date": self.ctx.broker.open_date,
                           "end_date": self.ctx.broker.close_date,
                           "open_price": self.ctx.broker.open_price,
                           "close_price": self.ctx.broker.close_price,
                           "holding_ret": holding_ret,
                           "holding_days": holding_days})
        df.index.name = "No."
        return df

    @property
    def order_num(self):
        """返回总交易次数"""
        return len(self.order_list)

    @property
    def gain_num(self):
        """返回交易盈利次数"""
        return len(self.order_list[self.order_list.holding_ret >= 0])

    @property
    def loss_num(self):
        """返回交易亏损次数"""
        return len(self.order_list[self.order_list.holding_ret < 0])

    @property
    def win_rate(self):
        """返回策略胜率"""
        return self.gain_num / self.order_num

    @property
    def max_holding_days(self):
        """返回最大持仓周期"""
        return max(self.order_list.holding_days)

    @property
    def max_empty_days(self):
        """返回最长空仓周期"""
        length = len(self.order_list)
        delta_days = []
        for i in range(1, length):
            ipx1 = self.ctx.trade_calc.index(self.order_list.iloc[i,"start_date"])
            ipx2 = self.ctx.trade_calc.index(self.order_list.iloc[i-1,"end_date"])
            delta_days.append(ipx1-ipx2)
        return max(delta_days)

    @property
    def max_gain(self):
        """返回单笔交易最大盈利"""
        return max(self.order_list.holding_ret)

    @property
    def max_loss(self):
        """返回单笔交易最大亏损"""
        return min(self.order_list.holding_ret)

    @property
    def gain_avg(self):
        """平均每笔盈利"""
        return sum(self.order_list.loc[self.order_list.holding_ret >= 0, "holding_ret"]) / self.gain_num

    @property
    def loss_avg(self):
        """平均每笔亏损"""
        return sum(self.order_list.loc[self.order_list.holding_ret < 0, "holding_ret"]) / self.loss_num

    @property
    def win_loss_ratio(self):
        """返回盈亏比"""
        return self.gain_avg / abs(self.loss_avg)

    @property
    def total_return(self):
        """返回总收益率"""
        return self.data.CumRet[-1] / self.data.CumRet[0] - 1.

    @property
    def long_num(self):
        """返回多头交易次数"""
        return len(self.order_list[self.order_list.position>0])

    @property
    def long_max_gain(self):
        """返回多头单笔最大盈利"""
        return max(self.order_list[self.order_list.position>0]["holding_ret"])

    @property
    def long_max_loss(self):
        """返回多头单笔最大亏损"""
        return min(self.order_list[self.order_list.position>0]["holding_ret"])

    @property
    def long_gain_avg(self):
        """返回多头平均盈利"""
        return np.mean(self.order_list[self.order_list.position>0&self.order_list.holding_ret>=0]["holding_ret"])

    @property
    def long_loss_avg(self):
        """返回多头平均亏损"""
        return np.mean(self.order_list[self.order_list.position>0&self.order_list.holding_ret<0]["holding_ret"])

    @property
    def long_win_rate(self):
        """返回多头胜率"""
        return len(self.order_list[self.order_list.position>0&self.order_list.holding_ret>=0])/self.long_num

    @property
    def long_win_loss_ratio(self):
        """返回多头盈亏比"""
        return abs(self.long_gain_avg / self.long_loss_avg)

    @property
    def short_num(self):
        """返回空头交易次数"""
        return len(self.order_list[self.order_list.position<0])

    @property
    def short_max_gain(self):
        """返回空头单笔最大盈利"""
        return max(self.order_list[self.order_list.position<0]["holding_ret"])

    @property
    def short_max_loss(self):
        """返回空头单笔最大损失"""
        return min(self.order_list[self.order_list.position<0]["holding_ret"])

    @property
    def short_gain_avg(self):
        """返回空头平均盈利"""
        return np.mean(self.order_list[self.order_list.position<0&self.order_list.holding_ret>=0]["holding_ret"])

    @property
    def short_loss_avg(self):
        """返回空头平均亏损"""
        return np.mean(self.order_list[self.order_list.position<0&self.order_list.holding_ret<0]["holding_ret"])

    @property
    def short_win_rate(self):
        """返回空头胜率"""
        return len(self.order_list[self.order_list.position<0&self.order_list.holding_ret>=0])/self.short_num

    @property
    def short_win_loss_ratio(self):
        """返回多头盈亏比"""
        return abs(self.short_gain_avg / self.short_loss_avg)

    @property
    def trade_stat_sheet(self):
        dicts = {
            "总交易次数": self.order_num,
            "盈利次数": self.gain_num,
            "亏损次数": self.loss_num,
            "胜率": self.win_rate,
            "最大持仓周期": self.max_holding_days,
            "最大空仓周期": self.max_empty_days,
            "单笔最大盈利": self.max_gain,
            "单笔最大亏损": self.max_loss,
            "平均每笔盈利": self.gain_avg,
            "平均每笔亏损": self.loss_avg,
            "盈亏比": self.win_loss_ratio,
            "多头交易次数": self.long_num,
            "多头单笔最大盈利": self.long_max_gain,
            "多头单笔最大亏损": self.long_max_loss,
            "多头平均每笔盈利": self.long_gain_avg,
            "多头平均每笔亏损": self.long_loss_avg,
            "多头胜率": self.long_win_rate,
            "多头盈亏比": self.long_win_loss_ratio,
            "空头交易次数": self.short_num,
            "空头单笔最大盈利": self.short_max_gain,
            "空头单笔最大亏损": self.short_max_loss,
            "空头平均每笔盈利": self.short_gain_avg,
            "空头平均每笔亏损": self.short_loss_avg,
            "空头胜率": self.short_win_rate,
            "空头盈亏比": self.short_win_loss_ratio
        }
        return dicts



