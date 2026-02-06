# 修改 src/report/json_generator.py
class EnhancedJSONGenerator(JSONGenerator):
    """增强版JSON生成器（包含资金面数据）"""
    
    def generate_ai_data(self, analysis_data):
        """生成AI分析数据（包含资金面）"""
        base_data = super().generate_ai_data(analysis_data)
        
        # 添加资金面数据
        capital_data = {
            'capital_flow': {
                'net_inflow': analysis_data['capital_flow']['net_inflow'],
                'main_force_ratio': analysis_data['capital_flow']['main_force_ratio'],
                'flow_trend': analysis_data['capital_flow']['trend'],
                'anomalies': analysis_data['capital_flow']['anomalies']
            },
            'sentiment': {
                'overall_score': analysis_data['sentiment']['overall'],
                'main_force_sentiment': analysis_data['sentiment']['main_force'],
                'sentiment_state': analysis_data['sentiment']['state']
            },
            'signals': analysis_data.get('capital_signals', [])
        }
        
        if analysis_data.get('margin_trading'):
            capital_data['margin_trading'] = {
                'margin_balance': analysis_data['margin_trading']['balance'],
                'margin_ratio': analysis_data['margin_trading']['ratio'],
                'trend': analysis_data['margin_trading']['trend']
            }
        
        base_data['capital_analysis'] = capital_data
        return base_data