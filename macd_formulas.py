# src/indicators/formulas/macd_formulas.py
"""
MACD计算公式
"""

def calculate_macd(prices, fast_period=12, slow_period=26, signal_period=9):
    """计算MACD指标"""
    ema_fast = calculate_ema(prices, fast_period)
    ema_slow = calculate_ema(prices, slow_period)
    
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram