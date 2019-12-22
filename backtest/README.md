本项目是一个简单的指数择时回测框架，整个框架结构如下：

> backtest/
>
>    -strategy.py
>
>    -broker.py
>
>    -summary.py
>
>    -performance.py  



strategy.py文件定义了策略回测的基类***Strategy***,策略回测只需要继承这个基类并重写*initialize*、*finish*、*on_tick*方法即可：

```
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
        self._sch = Scheduler() # 调度器对象
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
```

在***Strategy***类实例化的时候会自动创建一个调度器对象***Schedule***r，然后通过***Strategy***实例的start方法就能启动调度器，而调度器会根据历史数据的一个一个时间戳不断驱动***Strategy***, ***Broker***实例被调用。

为了处理不同实例之间的数据访问隔离，创建了一个***Context***对象并将其绑定到***Strategy***, ***Broker***实例上，通过*self.ctx*访问共享的数据，共享的数据主要包括*feed*和*benchmark*对象，即指数的相关历史数据，*benchmark*为指数历史收盘价格序列，为*pd.Series*对象，*feed*为*pd.DataFrame*格式，包含以下字段：

| 日期索引   | open | high | low  | close | signal | lastclose |
| ---------- | ---- | ---- | ---- | ----- | ------ | --------- |
| 2018-12-01 | 3450 | 3469 | 3420 | 3457  | 1      | 3400      |

> signal: 交易信号，1代表看多，0代表空仓或者平仓，-1代表看空
>
> lastclose: 代表昨收盘价价

而这个***Context***对象也绑定了***Strategy***, ***Broker***的实例, 这就可以使得数据访问接口统一。***Broker***类中定义了*order_open*和*order_close*两个方法,内部根据*signal*的值封装了不同的处理逻辑。

summary.py文件中定义了***Summary***类来获取回测结果并且以属性方式提供，performance.py中则定义了许多风险收益指标计算和绘图的功能函数。

