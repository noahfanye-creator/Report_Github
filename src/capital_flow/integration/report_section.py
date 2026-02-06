"""
资金面报告章节
"""
from typing import Dict, List


class CapitalFlowReportSection:
    """资金面报告章节生成器"""

    def generate_section(self, symbol: str, market_type: str, analysis_data: Dict):
        return None

    def generate_summary_table(self, capital_data: Dict):
        return ""

    def generate_signals(self, analysis_data: Dict) -> List:
        return []
