"""
斐波那契回撤和扩展位计算
"""


def calculate_fibonacci_retracement(high, low):
    """计算斐波那契回撤位"""
    pr = high - low
    return {
        "0.0%": low,
        "23.6%": high - 0.236 * pr,
        "38.2%": high - 0.382 * pr,
        "50.0%": high - 0.5 * pr,
        "61.8%": high - 0.618 * pr,
        "78.6%": high - 0.786 * pr,
        "100.0%": high,
    }


def calculate_fibonacci_extensions(high, low):
    """计算斐波那契扩展位"""
    pr = high - low
    return {
        "127.2%": low + 1.272 * pr,
        "161.8%": low + 1.618 * pr,
        "261.8%": low + 2.618 * pr,
        "423.6%": low + 4.236 * pr,
    }
