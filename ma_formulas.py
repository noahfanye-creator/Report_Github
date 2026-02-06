# src/indicators/formulas/ma_formulas.py
"""
移动平均线计算公式
"""

def calculate_sma(prices, period):
    """简单移动平均线"""
    return prices.rolling(window=period).mean()

def calculate_ema(prices, period):
    """指数移动平均线"""
    return prices.ewm(span=period, adjust=False).mean()

def calculate_wma(prices, period):
    """加权移动平均线"""
    weights = np.arange(1, period + 1)
    return prices.rolling(window=period).apply(
        lambda x: np.dot(x, weights) / weights.sum(), raw=True
    )