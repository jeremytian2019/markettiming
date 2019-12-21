# -*- coding: utf-8 -*-


import numpy as np
import pandas as pd


class Summary:
    def __init__(self):
        pass

    @property
    def data(self):
        cum_ret = np.cumsum(self.ctx.broker.ret)
        draw_down = cum_ret - np.array(pd.Series(cum_ret).cummax())
        df = pd.DataFrame({"Position": self.ctx.broker.total_position,
                           "MarketValue": self.ctx.broker.market_value,
                           "DailyRet": self.ctx.broker.ret,
                           "CumRet": cum_ret,
                           "DrawDown": draw_down}, index=self.ctx.trade_calc)
        df.index.name = "Date"
        return df

    @property
    def order_list(self):
        holding_days = []
        for i in range(len(self.ctx.broker.open_date)):
            delta = self.ctx.trade_calc.index(self.ctx.broker.close_date[i] - self.ctx.broker.open_date[i])
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
    def order_num(self):      # 总交易次数
        return len(self.order_list)

    @property
    def long_num(self):       # 多头交易次数
        return len(self.order_list.loc[self.order_list.position > 0])

    @property
    def short_num(self):     # 空头交易次数
        return len(self.order_list.loc[self.order_list.position < 0])

    @property
    def win_num(self):       # 总盈利次数
        return sum(self.order_list.holding_ret[self.order_list.holding_ret >= 0])

    @property
    def loss_num(self):      # 总亏损次数
        return sum(self.order_list.holding_ret[self.order_list.holding_ret < 0])

    @property
    def win_rate(self):      # 总胜率
        return self.win_num / self.order_num

    @property
    def max_holding_days(self):  # 最长持仓交易日
        return max(self.order_list.holding_days)

    @property
    def max_empty_days(self):    # 最长空仓交易日
        return

    @property
    def max_profit(self):        # 单次最大盈利
        return max(self.order_list.holding_ret)

    @property
    def max_loss(self):          # 单次最大亏损
        return min(self.order_list.holding_ret)

    @property
    def profit_avg(self):        # 平均每次盈利
        return sum(self.order_list.loc[self.order_list.holding_ret >= 0, "holding_ret"]) / self.win_num

    @property
    def loss_avg(self):          # 平均每次亏损
        return sum(self.order_list.loc[self.order_list.holding_ret > 0, "holding_ret"]) / self.loss_num

    @property
    def win_loss_ratio(self):     # 盈亏比
        return self.profit_avg / abs(self.loss_avg)

    @property
    def total_return(self):       # 总收益
        return self.data.CumRet[-1]

    @property
    def annual_return(self):      # 年均收益
        return self.total_return * 245 / len(self.data)

    @property
    def max_drawdown(self):       # 历史最大回撤
        return min(self.data.DrawDown)

    @property
    def calmar_ratio(self):       # 收益回撤比
        return self.annual_return / abs(self.max_drawdown)

    @property
    def stat_result(self):
        result = {"总交易次数": self.order_num,
                  "最大持仓周期": self.max_holding_days,
                  "最大空仓周期": self.max_empty_days,
                  "总盈利次数": self.win_num,
                  "总亏损次数": self.loss_num}
        return result





