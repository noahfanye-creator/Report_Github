"""
多市场分析系统
"""
from typing import Dict, List, Tuple, Optional

import numpy as np

from data_sources.unified_market_data import UnifiedMarketDataSystem
from .hk_pipeline import HKAnalysisPipeline
from .a_pipeline import AAnalysisPipeline


class MultiMarketAnalysisSystem:
    """多市场分析系统"""

    def __init__(self):
        self.data_system = UnifiedMarketDataSystem()
        self.market_pipelines = {}
        self.pipeline_classes = {
            "港股": HKAnalysisPipeline,
            "A股": AAnalysisPipeline,
        }

    def analyze_stock(
        self,
        symbol: str,
        market: Optional[str] = None,
        start_date: str = "2025-01-01",
        end_date: str = "2026-01-26",
        **kwargs,
    ) -> Dict:
        if market is None:
            market = self.data_system.detect_market(symbol)
        pipeline_class = self.pipeline_classes.get(market)
        if pipeline_class is None:
            raise ValueError(f"暂不支持市场类型: {market}，当前支持: {', '.join(self.pipeline_classes.keys())}")
        print(f"开始分析 {market} 股票: {symbol}")
        pipeline = pipeline_class(symbol)
        result = pipeline.run_complete_analysis(start_date=start_date, end_date=end_date, **kwargs)
        self.market_pipelines[symbol] = pipeline
        result["report_type"] = "收盘分析"
        result["data_cutoff"] = result.get("analysis_time", "")
        charts = result.get("charts", {})
        report_path = charts.get("main_chart", "") or ""
        if report_path:
            result["report_path"] = report_path
        else:
            result["report_path"] = result.get("ai_data", {}).get("json_path", "N/A")
        return result

    def analyze_multiple_stocks(
        self,
        stock_list: List[Tuple[str, str]],
        start_date: str,
        end_date: str,
    ) -> Dict:
        results = {}
        for symbol, market in stock_list:
            try:
                results[symbol] = self.analyze_stock(
                    symbol=symbol, market=market, start_date=start_date, end_date=end_date
                )
            except Exception as e:
                print(f"分析 {symbol} 失败: {e}")
                results[symbol] = {"error": str(e)}
        return results

    def compare_markets(
        self,
        hk_symbols: List[str],
        a_symbols: List[str],
        start_date: str,
        end_date: str,
    ) -> Dict:
        all_stocks = [(s, "港股") for s in hk_symbols] + [(s, "A股") for s in a_symbols]
        results = self.analyze_multiple_stocks(all_stocks, start_date, end_date)
        comparison_report = self._generate_market_comparison_report(results)
        return {"individual_results": results, "comparison_report": comparison_report}

    def _generate_market_comparison_report(self, results: Dict) -> Dict:
        report = {
            "港股": {"count": 0, "avg_volatility": 0, "avg_return": 0, "stocks": []},
            "A股": {"count": 0, "avg_volatility": 0, "avg_return": 0, "stocks": []},
        }
        hk_vol, hk_ret, a_vol, a_ret = [], [], [], []
        for symbol, r in results.items():
            if "error" in r:
                continue
            m = r.get("market", "未知")
            if m not in report:
                continue
            report[m]["count"] += 1
            report[m]["stocks"].append(symbol)
            vol = r.get("market_characteristics", {}).get("volatility", {}).get("daily_vol", 0)
            ret = (r.get("price_data") or [{}])[-1].get("pct_change", 0)
            if m == "港股":
                hk_vol.append(vol)
                hk_ret.append(ret)
            elif m == "A股":
                a_vol.append(vol)
                a_ret.append(ret)
        if hk_vol:
            report["港股"]["avg_volatility"] = float(np.mean(hk_vol))
            report["港股"]["avg_return"] = float(np.mean(hk_ret))
        if a_vol:
            report["A股"]["avg_volatility"] = float(np.mean(a_vol))
            report["A股"]["avg_return"] = float(np.mean(a_ret))
        return report
