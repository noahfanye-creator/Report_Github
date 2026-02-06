# src/indicators/formulas/rsi_formulas.py
"""
RSI计算公式
"""

def calculate_rsi(prices, period=14):
    """计算相对强弱指数"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi