# src/indicators/formulas/fibonacci.py
"""
斐波那契回撤和扩展位计算
"""

def calculate_fibonacci_retracement(high, low):
    """计算斐波那契回撤位"""
    price_range = high - low
    
    levels = {
        '0.0%': low,
        '23.6%': high - 0.236 * price_range,
        '38.2%': high - 0.382 * price_range,
        '50.0%': high - 0.5 * price_range,
        '61.8%': high - 0.618 * price_range,
        '78.6%': high - 0.786 * price_range,
        '100.0%': high,
    }
    
    return levels

def calculate_fibonacci_extensions(high, low):
    """计算斐波那契扩展位"""
    price_range = high - low
    
    extensions = {
        '127.2%': low + 1.272 * price_range,
        '161.8%': low + 1.618 * price_range,
        '261.8%': low + 2.618 * price_range,
        '423.6%': low + 4.236 * price_range,
    }
    
    return extensions