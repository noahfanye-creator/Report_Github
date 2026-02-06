# src/api/capital_flow_api.py
"""
资金面数据API接口
"""

class CapitalFlowAPI:
    """资金面数据API"""
    
    @staticmethod
    def get_capital_summary(symbol: str, date: str = None) -> Dict:
        """
        获取资金面概要
        """
        pass
    
    @staticmethod
    def get_flow_history(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取历史资金流向
        """
        pass
    
    @staticmethod
    def get_realtime_flow(symbol: str) -> Dict:
        """
        获取实时资金流向
        """
        pass
    
    @staticmethod
    def get_sentiment_analysis(symbol: str) -> Dict:
        """
        获取资金情绪分析
        """
        pass
    
    @staticmethod
    def get_margin_data(symbol: str) -> Dict:
        """
        获取融资融券数据（A股）
        """
        pass
    
    @staticmethod
    def generate_capital_report(symbol: str, report_type: str = "full") -> Dict:
        """
        生成资金面分析报告
        :param symbol: 股票代码
        :param report_type: 报告类型（summary/full/detailed）
        """
        pass