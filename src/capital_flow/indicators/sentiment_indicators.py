"""
资金情绪指标
"""


def calculate_composite_sentiment(indicators, weights):
    w = sum(i * w for i, w in zip(indicators, weights))
    return min(max(w, 0), 100)


def calculate_sentiment_trend(sentiment_series, period=5):
    if len(sentiment_series) < period:
        return "insufficient_data"
    recent = sentiment_series[-period:].mean()
    previous = sentiment_series[-(period * 2) : -period].mean()
    if previous == 0:
        return "stable"
    if recent > previous * 1.1:
        return "strong_up"
    if recent > previous * 1.02:
        return "up"
    if recent < previous * 0.9:
        return "strong_down"
    if recent < previous * 0.98:
        return "down"
    return "stable"


def calculate_volatility_adjusted_sentiment(sentiment_score, volatility):
    adj = 1 / (1 + volatility)
    return sentiment_score * adj
