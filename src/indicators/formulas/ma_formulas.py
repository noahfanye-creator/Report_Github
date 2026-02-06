"""
移动平均线计算公式
"""
import numpy as np
import pandas as pd


def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
    """简单移动平均线"""
    return prices.rolling(window=period).mean()


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """指数移动平均线"""
    return prices.ewm(span=period, adjust=False).mean()


def calculate_wma(prices: pd.Series, period: int) -> pd.Series:
    """加权移动平均线"""
    weights = np.arange(1, period + 1, dtype=float)
    return prices.rolling(window=period).apply(
        lambda x: np.dot(x, weights) / weights.sum(), raw=True
    )
