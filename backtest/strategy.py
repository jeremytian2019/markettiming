# -*- coding: utf-8 -*-


from abc import ABC, abstractmethod
from collections import UserDict
from itertools import chain
from .broker import Broker
from .utils import logger
from .summary import Summary


class Context(UserDict):
    def __getattr__(self, key):
        # 让调用这可以通过索引或者属性引用皆可
        return self[key]

    def set_bar(self, tick):
        """设置回测循环中的当前时间"""
        self["time"] = tick
        self["bar"] = self["feed"].loc[tick]

class Scheduler(object):
    """
    整个回测过程中的调度中心, 通过一个个tick来驱动回测逻辑
    所有被调度的对象都会绑定一个叫做ctx的Context对象来共享整个回测过程中的所有关键数据
    可用变量包括:
        ctx.feed: pd.DataFrame对象
        ctx.benchmark: pd。Series对象
        ctx.time: 循环时当前tick所处时间
        ctx.bar: 循环时当前tick上的数据，包含OHLC以及signal和昨收盘价数据，pd.Series数据结构
        ctx.trade_calc: 回测日历
        ctx.broker: Broker对象
        ctx.st: Strategy对象
    """

    def __init__(self):
        self.ctx = Context()
        self._pre_hook_lst = []
        self._post_hook_lst = []
        self._runner_lst = []

    def add_feed(self, feed):
        self.ctx["feed"] = feed

    def add_benchmark(self, benchmark):
        self.ctx["benchmark"] = benchmark

    def add_broker(self, broker):
        self.ctx["broker"] = broker
        broker.ctx = self.ctx

    def add_strategy(self, strategy):
        self.ctx["st"] = strategy

    def add_runner(self, runner):
        self._runner_lst.append(runner)

    def add_trade_calc(self, trade_calc):
        self.ctx["trade_calc"] = trade_calc

    def add_hook(self, hook, typ="post"):
        if typ == "post" and hook not in self._post_hook_lst:
            self._post_hook_lst.append(hook)
        elif typ == "pre" and hook not in self._pre_hook_lst:
            self._pre_hook_lst.append(hook)

    def run(self):
        # runner指存在可调用的initialize, finish, run(tick)的对象
        runner_lst = list(chain(self._pre_hook_lst, self._runner_lst, self._post_hook_lst))
        # 循环开始前为broker, strategy, hook等实例绑定ctx对象
        for runner in runner_lst:
            runner.ctx = self.ctx
        # 循环开始前调用broker, strategy, hook等实例initialize方法
        for runner in self._runner_lst:
            runner.initialize()

        for tick in self.ctx.trade_calc:
            self.ctx.set_bar(tick)
            self.ctx.st.run(tick)
        # 循环结束后调用broker, strategy, hook等实例initialize方法
        for runner in self._runner_lst:
            runner.finish()


class Strategy(ABC):
    """
    回测引擎的基类
    ===========
    Parameters:
      feed: DataFrame
            指数历史日期数据，包括每日信号，包含列字段为:
            open/high/low/close/signal/preclose
            开盘价/最高价/最低价/收盘价/信号/昨收盘价
            signal:{1,0,-1}, 取值1表示多头，0表示看平或者平仓，-1表示空头
      commission: 每单位头寸交易手续费，默认为2个基点
      slippage: 每单位头寸交易滑点，默认为1个基点

    """

    def __init__(self, feed, benchmark, commission=2, slippage=1):
        # 设置回测起始与结束日期
        start_date = max(feed.index[0], benchmark.index[0])
        end_date = min(feed.index[-1], benchmark.index[-1])
        self.feed = feed[start_date:end_date]
        self._sch = Scheduler()
        self._logger = logger
        # 设置backtest, broker对象, 以及将自身实例放在调度器的runner_list中
        self._sch.add_runner(self)
        self._sch.add_backtest(self)

        broker = Broker(commission, slippage)
        self._sch.add_broker(broker)

        self._sch.add_feed(feed[start_date:end_date])
        self._sch.add_benchmark(benchmark[start_date:end_date])
        self.stat = Summary()     # 创建统计功能
        self._sch.add_hook(self.stat)

        trade_calc = list(self.feed)  # 回测日历默认为提供数据起始日范围
        self._sch.add_trade_calc(trade_calc)

    def info(self, msg):
        self._logger.info(msg)

    def add_hook(self, *agrs, **kwargs):
        self._sch.add_hook(*agrs, **kwargs)

    def initialize(self):
        """在回测开始前的初始化"""
        pass

    def run(self, tick):
        self.on_tick(tick)

    def start(self):
        self._sch.run()

    def finish(self):
        """在回测结束后调用"""
        pass

    @abstractmethod
    def on_tick(self, tick):
        """
        回测实例必须实现的方法，并编写自己的交易逻辑
        """
        pass

