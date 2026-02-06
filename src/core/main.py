"""
系统主入口与编排
"""
from .multi_market_analysis_system import MultiMarketAnalysisSystem


class StockAnalysisSystem:
    """股票分析系统（主入口）"""

    def __init__(self):
        self._engine = MultiMarketAnalysisSystem()

    def analyze_stock(self, symbol: str, **kwargs):
        return self._engine.analyze_stock(symbol, **kwargs)
