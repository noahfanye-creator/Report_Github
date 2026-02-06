# src/capital_flow/indicators/sentiment_indicators.py
"""
资金情绪指标计算公式
"""

def calculate_composite_sentiment(indicators, weights):
    """计算综合资金情绪指数"""
    weighted_sum = sum(indicator * weight for indicator, weight in zip(indicators, weights))
    return min(max(weighted_sum, 0), 100)  # 限制在0-100范围

def calculate_sentiment_trend(sentiment_series, period=5):
    """计算情绪趋势"""
    if len(sentiment_series) < period:
        return "insufficient_data"
    
    recent = sentiment_series[-period:].mean()
    previous = sentiment_series[-(period*2):-period].mean()
    
    if recent > previous * 1.1:
        return "strong_up"
    elif recent > previous * 1.02:
        return "up"
    elif recent < previous * 0.9:
        return "strong_down"
    elif recent < previous * 0.98:
        return "down"
    else:
        return "stable"

def calculate_volatility_adjusted_sentiment(sentiment_score, volatility):
    """计算波动率调整后的情绪得分"""
    # 高波动率时降低情绪得分置信度
    adjustment = 1 / (1 + volatility)
    return sentiment_score * adjustment