# -*- coding: utf-8 -*-

"""
此文件提供策略相关收益风险指标的功能函数以及相关绘图函数
"""

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt


# ================================
# 计算年化收益、夏普比以及收益回撤比
# ================================

def to_returns(prices):
    """
    根据价格序列或者资产净值序列计算日简单收益序列
    """
    return prices / prices.shift(1) - 1


def to_log_returns(prices):
    """
    根据价格序列或者资产净值序列计算日对数收益序列
    """
    return np.log(prices / prices.shift(1))


def to_total_returns(prices):
    """
    根据价格序列或者资产净值序列计算期末总收益（%）
    """
    total_ret = prices.iloc[-1] / prices.iloc[0] - 1.
    return np.around(100 * total_ret, decimals=2)


def to_monthly_returns(returns):
    """
    根据日收益序列统计月收益
    """

    def accumulate_returns(x):
        return ((x + 1).cumprod() - 1).iloc[-1]

    grouping = [lambda x: x.year, lambda x: x.month]
    return returns.groupby(grouping).apply(accumulate_returns).unstack().round(3)


def to_price_index(returns, start=100):
    """
    根据日收益序列编制价格序列（策略累计净值曲线，起始基点100）
    """
    return (returns.replace(to_replace=np.nan, value=0) + 1).cumprod() * start


def rebase(prices, value=100):
    """
    校准所有序列同一起始基点方便比较，默认为100
    """
    return prices / prices.iloc[0] * value


def annual_return(prices, year_days=245):
    """
    根据策略净值序列计算年化收益率,一年按245个交易日计算
    """
    T = len(prices) - 1
    ret = (prices.iloc[-1] / prices.iloc[0]) ** (year_days / T) - 1.

    return np.around(100 * ret, decimals=2)


def annual_vol(prices, year_days=245):
    """
    根据策略净值序列计算年化波动率，一年按245个交易日计算
    """
    daily_return = prices / prices.shift(1) - 1.
    annualized_vol = np.std(daily_return.dropna()) * np.sqrt(year_days)

    return np.around(100 * annualized_vol, decimals=2)


def max_drawdown(prices):
    """
    根据策略净值序列计算历史最大回撤
    """
    max_dd = (prices / prices.expanding(min_periods=1).max()).min() - 1

    return np.around(max_dd * 100, decimals=2)


def sharpe_ratio(prices, year_days=245, free_risk_rate=3.):
    """
    根据策略净值序列计算夏普比，一年按245个交易日计算，无风险收益率设定为3.
    """
    ret = annual_return(prices, year_days=year_days)
    vol = annual_vol(prices, year_days=year_days)
    sharpe = (ret - free_risk_rate) / vol

    return np.around(sharpe, decimals=2)


def calmar_ratio(prices, year_days=245):
    """
    根据策略净值序列计算卡尔玛比率，一年按245个交易日计算。
    """
    ret = annual_return(prices, year_days=year_days)
    max_dd = max_drawdown(prices)
    ratio = ret / abs(max_dd)

    return np.around(ratio, decimals=2)


# ==================================
# 回撤相关信息
# ==================================

def to_drawdown_series(prices):
    """
    根据策略净值序列计算回撤序列
    """
    # 创建原始数据副本以免修改原始数据
    drawdown = prices.copy()
    # 前向填充缺失值
    drawdown = drawdown.fillna(method='ffill')
    # 忽略起始位置缺失值
    drawdown[np.isnan(drawdown)] = -np.Inf
    # 滚动最大值
    roll_max = np.maximum.accumulate(drawdown)
    drawdown = drawdown / roll_max - 1.
    return np.around(drawdown * 100, decimals=2)


def drawdown_details(prices, ascending=True, index_type=pd.DatetimeIndex):
    """
    根据价格序列计算并返回回撤信息：包括起始日期、结束日期、持续时间以及回撤幅度.
    持续日期为实际日历日，并非交易日.
    """
    # 计算回撤序列
    drawdown = to_drawdown_series(prices)

    is_zero = drawdown == 0
    # 找到起始日 (回撤值为0后第一个回撤值非零日期)
    start = ~is_zero & is_zero.shift(1)
    start = list(start[start == True].index)

    # 找到结束日 (回撤值非零后第一个回撤值为零的日期)
    end = is_zero & (~is_zero).shift(1)
    end = list(end[end == True].index)

    if len(start) is 0:
        return None

    # 回撤没有结束日期 (以回撤序列结束日代替)
    if len(end) is 0:
        end.append(drawdown.index[-1])

    # 如果第一个回撤起始日大于第一个回撤结束日
    # 意味着回撤序列以回撤形式开始
    # 因此将回撤序列起始日作为第一个回撤起始日
    if start[0] > end[0]:
        start.insert(0, drawdown.index[0])

    # 如果最后一个回撤起始日大于最后一个回撤结束日
    # 将回撤序列结束日作为最后一个回撤结束日
    if start[-1] > end[-1]:
        end.append(drawdown.index[-1])

    result = pd.DataFrame(
        columns=('Start', 'Valley', 'End', 'Duration', 'Drawdown(%)'),
        index=range(0, len(start))
    )

    for i in range(0, len(start)):
        dd = drawdown[start[i]:end[i]].min()
        idxmin = drawdown[start[i]:end[i]].argmin()  # 期间最大回撤发生日

        if index_type is pd.DatetimeIndex:
            result.iloc[i] = (start[i], idxmin, end[i], (end[i] - start[i]).days, dd)
        else:
            result.iloc[i] = (start[i], idxmin, end[i], (end[i] - start[i]), dd)

    if ascending:
        result = result.sort_values(by='Drawdown(%)', ascending=True)

    return result


def show_worst_drawdown_periods(prices, top=5):
    """
    打印最糟糕回撤相关信息.
    打印回撤起始日、谷底日、回复日以及期间最大回撤
    默认打印前5次最糟糕回撤信息。
    """
    # 升序排列
    drawdown = drawdown_details(prices, ascending=True, index_type=pd.DatetimeIndex)
    return drawdown.iloc[:top]


# =========================================
# 相关绘图函数
# =========================================

def plot_drawdown_periods(prices, top=5, **kwargs):
    """
    绘图累计净值曲线并显示几个最糟糕回撤期间。
    """

    fig, ax = plt.subplots(figsize=(10, 5))

    prices.plot(ax=ax, color='blue', lw=2.0)
    drawdowns = (drawdown_details(prices)).iloc[:top]
    drawdowns.index = range(len(drawdowns))

    lim = ax.get_ylim()
    colors = sns.cubehelix_palette(len(drawdowns))[::-1]
    for i, (peak, recovery) in drawdowns[['Start', 'End']].iterrows():
        ax.fill_between((peak, recovery),
                        lim[0],
                        lim[1],
                        alpha=.4,
                        color=colors[i])
    ax.set_ylim(lim)
    ax.set_title('Cummulative NAV & Top %d drawdown periods' % top)
    ax.set_ylabel('Cumulative NAV')
    ax.legend(['Portfolio'], loc='upper left',
              frameon=True, framealpha=0.5)
    ax.set_xlabel('')
    return ax


def plot_drawdown_underwater(prices, **kwargs):
    """
    绘图策略累计净值曲线以及回撤曲线
    """
    fig, ax = plt.subplots(figsize=(10, 5))

    prices.plot(ax=ax, color='blue', lw=2.0)
    ax.set_ylabel('Cummulative NAV')
    ax.set_title('Cummulative NAV & Underwater plot')
    ax.set_xlabel('Date')

    underwater = to_drawdown_series(prices)
    ax2 = ax.twinx()
    underwater.plot(ax=ax2, kind='area', color='coral', alpha=0.7, **kwargs)
    ax2.set_ylabel('Drawdown(%)')
    return ax


def plot_order_returns_dist(returns, bins=10, ax=None, **kwargs):
    """
    每笔交易基点收益分布直方图
    """
    if ax is None:
        ax = plt.gca()

    ax.hist(
        returns,
        color='orangered',
        alpha=0.80,
        bins=bins,
        **kwargs)

    ax.axvline(
        np.mean(returns),
        color='gold',
        linestyle='--',
        lw=4,
        alpha=1.0)

    ax.axvline(0.0, color='black', linestyle='-', lw=3, alpha=0.75)
    ax.legend(['Mean'], frameon=True, framealpha=0.5)
    ax.set_ylabel('Number of orders')
    ax.set_xlabel('Basis Returns')
    ax.set_title("Distribution of returns by order")
    return ax


def plot_holding_days_dist(holdings, bins=10, ax=None, **kwargs):
    """
    每笔交易持仓时间分布直方图
    """
    if ax is None:
        ax = plt.gca()

    ax.hist(
        holdings,
        color='orangered',
        alpha=0.80,
        bins=bins,
        **kwargs)

    ax.axvline(
        np.mean(holdings),
        color='gold',
        linestyle='--',
        lw=4,
        alpha=1.0)

    ax.legend(['Mean'], frameon=True, framealpha=0.5)
    ax.set_ylabel('Number of orders')
    ax.set_xlabel('Holding Days')
    ax.set_title("Distribution of Holding Days")
    return ax


def plot_monthly_returns_heatmap(returns, ax=None, **kwargs):
    """
    根据策略日频收益计算月频收益并绘制月频收益热力图
    """
    if ax is None:
        ax = plt.gca()

    monthly_ret_table = to_monthly_returns(returns)

    sns.heatmap(
        monthly_ret_table.fillna(0) *
        100.0,
        annot=True,
        annot_kws={"size": 9},
        alpha=1.0,
        center=0.0,
        cbar=False,
        cmap='RdBu',
        ax=ax, **kwargs)
    ax.set_ylabel('Year')
    ax.set_xlabel('Month')
    ax.set_title("Monthly returns (%)")
    return ax