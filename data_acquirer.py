# 修改 src/data/data_acquirer.py
class EnhancedDataAcquirer(DataAcquirer):
    """增强版数据获取器（集成资金面数据）"""
    
    def get_all_data(self, symbol, **kwargs):
        """获取全部数据（包括资金面）"""
        # 原有技术面数据
        technical_data = super().get_all_data(symbol, **kwargs)
        
        # 新增资金面数据
        capital_data = self._get_capital_flow_data(symbol)
        margin_data = self._get_margin_data(symbol) if self.is_a_share else None
        sentiment_data = self._get_sentiment_data(symbol)
        
        return {
            'technical': technical_data,
            'capital_flow': capital_data,
            'margin_trading': margin_data,
            'sentiment': sentiment_data
        }