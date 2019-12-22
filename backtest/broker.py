# -*- coding: utf-8 -*-


class Broker:
    def __init__(self, commission, slippage):
        self.commission = commission
        self.slippage = slippage
        self.ret = []                 # 按bar更新
        self.order_position = []      # 按信号更新
        self.total_position = []      # 按bar更新
        self.open_date = []
        self.close_date = []
        self.open_price = []
        self.close_price = []
        self.market_value = []  # 按bar更新

    def order_open(self, exercise_price):
        """开仓买入或者卖出"""

        if len(self.total_position) == 0:  # 判断回测起始日
            self.order_position.append(self.ctx.bar.signal)
            self.total_position.append(self.ctx.bar.signal)
            self.ret.append((self.ctx.bar.close - exercise_price)*self.ctx.bar.signal - self.commision - self.slippage)
            self.market_value.append(self.ctx.bar.close * abs(self.ctx.bar.signal))
            self.open_date.append(self.ctx.time)
            self.open_price.append(exercise_price)
        else:      # 非回测起始日
            if self.total_position[-1] == 0:  # 上个交易日没有持仓头寸
                order_num = max(1, int(sum(self.ret) / exercise_price)) * self.ctx.bar.signal
                self.ret.append(order_num * (self.ctx.bar.close - exercise_price - self.commission - self.slippage))
                self.total_position.append(order_num)
                self.order_position.append(order_num)
                self.open_date.append(self.ctx.time)
                self.open_price.append(exercise_price)
                self.market_value.append(abs(order_num) * self.ctx.bar.close)
            else:   # 上个交易日有持仓头寸
                order_num = int(sum(self.ret) / exercise_price) - abs(self.total_position[-1])
                if order_num > 0:  # 增仓
                    self.ret.append(order_num * (self.ctx.bar.signal * (self.ctx.bar.close - exercise_price) -
                                                 self.commission - self.slippage) + \
                                    self.total_position[-1]*(self.ctx.bar.close - self.ctx.bar.lastclose))
                    self.open_date.append(self.ctx.time)
                    self.open_price.append(exercise_price)
                    self.order_position.append(order_num * self.ctx.bar.signal)
                    self.total_position.append(order_num * self.ctx.bar.signal + self.total_position[-1])
                    self.market_value.append(abs(self.total_position[-1]) * self.ctx.bar.close)

                else:  # 累计盈利达不到增仓条件
                    self.total_position.append(self.total_position[-1])
                    self.ret.append(self.total_position[-1] * (self.ctx.bar.close - self.ctx.bar.lastclose))
                    self.market_value.append(abs(self.total_position[-1]) * self.ctx.bar.close)

    def order_close(self, exercise_price):
        """平仓或者空仓"""

        if len(self.total_position) == 0:  # 回测起始日
            self.total_position.append(self.ctx.bar.signal)
            self.ret.append(0)
            self.market_value(0)

        else:      # 非回测起始日
            if self.total_position[-1] == 0:  # 上个交易日没有持仓头寸
                self.total_position.append(self.ctx.bar.signal)  # 0
                self.ret.append(0)
                self.market_value.append(0)
            else:   # 上个交易日有持仓头寸

                self.ret.append(self.total_position[-1] * (exercise_price - self.ctx.bar.lastclose))
                self.total_position.append(0)
                self.market_value.append(0)
                self.close_date.extend([self.ctx.time] * (len(self.open_date) - len(self.close_date)))










