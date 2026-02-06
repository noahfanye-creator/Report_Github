"""
A股分析流水线
"""
from datetime import datetime
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import pandas as pd
import json
import os

from data_sources.unified_market_data import UnifiedMarketDataSystem
from indicators.a_indicator_calculator import AIndicatorCalculator
from visualizer.multi_market_chart_renderer import MultiMarketChartRenderer
from utils.data_validator import DataQualityValidator


class AAnalysisPipeline:
    """A股分析流水线"""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.market = "A股"
        self.data_system = UnifiedMarketDataSystem(["akshare", "yfinance", "tushare"])
        self.a_calculator = AIndicatorCalculator()
        self.chart_renderer = MultiMarketChartRenderer()
        self.validator = DataQualityValidator()
        self.a_data = None
        self.index_data = None
        self.comparison_data = {}

    def run_complete_analysis(
        self,
        start_date: str = "2025-01-01",
        end_date: str = "2026-01-26",
        include_index: bool = True,
        include_comparison: Optional[List[str]] = None,
    ) -> Dict:
        result = {
            "symbol": self.symbol,
            "market": self.market,
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        include_comparison = include_comparison or []

        print("=" * 60)
        print(f"开始A股分析: {self.symbol}")
        print("=" * 60)

        self._fetch_a_data(start_date, end_date)
        if include_index:
            self._fetch_a_index_data(start_date, end_date)
        if include_comparison:
            self._fetch_comparison_data(include_comparison, start_date, end_date)

        quality_report = self._validate_a_data()
        result["quality_report"] = quality_report

        indicators_data = self._calculate_a_indicators()
        result.update(indicators_data)

        market_characteristics = self._analyze_a_market()
        result["market_characteristics"] = market_characteristics

        charts = self._generate_a_charts()
        result["charts"] = charts

        ai_data = self._prepare_a_ai_data(result)
        result["ai_data"] = ai_data

        print("\n" + "=" * 60)
        print("A股分析完成!")
        print(f"数据点数: {len(self.a_data) if self.a_data is not None else 0}")
        print(f"数据质量: {quality_report.get('status', 'UNKNOWN')}")
        print(f"生成图表: {len(charts)}张")
        print("=" * 60)
        return result

    def _fetch_a_data(self, start_date: str, end_date: str):
        """获取A股数据"""
        self.a_data = self.data_system.get_market_data(
            symbol=self.symbol, market=self.market,
            start_date=start_date, end_date=end_date, data_type="daily"
        )
        if self.a_data is None or self.a_data.empty:
            raise ValueError(f"无法获取A股 {self.symbol} 数据")
        print(f"获取A股数据成功: {len(self.a_data)} 条")

    def _fetch_a_index_data(self, start_date: str, end_date: str):
        """获取A股指数数据（如上证指数、深证成指）"""
        # 根据股票代码判断交易所
        symbol_clean = self.symbol.replace(".SH", "").replace(".SZ", "").replace(".BJ", "").strip()
        if symbol_clean.startswith(("6", "9")):
            # 上海交易所
            index_code = "000001.SH"  # 上证指数
        elif symbol_clean.startswith(("0", "3")):
            # 深圳交易所
            index_code = "399001.SZ"  # 深证成指
        elif symbol_clean.startswith(("8", "4")):
            # 北京交易所
            index_code = "899050.BJ"  # 北证50
        else:
            index_code = "000001.SH"  # 默认上证指数
        
        try:
            self.index_data = self.data_system.get_market_data(
                symbol=index_code, market="A股",
                start_date=start_date, end_date=end_date, data_type="daily"
            )
            if self.index_data is not None:
                print(f"A股指数数据: {len(self.index_data)} 条")
        except Exception as e:
            print(f"获取A股指数数据失败: {e}")

    def _fetch_comparison_data(self, symbols: List[str], start_date: str, end_date: str):
        """获取对比股票数据"""
        for s in symbols:
            try:
                d = self.data_system.get_market_data(s, start_date, end_date, data_type="daily")
                if d is not None:
                    self.comparison_data[s] = d
                    print(f"对比数据 {s} 成功")
            except Exception as e:
                print(f"对比数据 {s} 失败: {e}")

    def _validate_a_data(self) -> Dict:
        """验证A股数据质量"""
        if self.a_data is None:
            return {"status": "FAIL", "message": "没有数据"}
        base = self.validator.validate_ohlcv(self.a_data)
        vol = self.a_data["volume"]
        a_report = {
            "status": base["status"],
            "completeness": base["completeness"],
            "data_points": len(self.a_data),
            "price_range": {
                "min": float(self.a_data["low"].min()),
                "max": float(self.a_data["high"].max()),
                "current": float(self.a_data["close"].iloc[-1]),
            },
            "volume_analysis": {
                "avg_volume": float(vol.mean()),
                "max_volume": float(vol.max()),
                "recent_volume": float(vol.tail(5).mean()),
            },
            "a_specific_checks": self._perform_a_specific_checks(),
        }
        return a_report

    def _perform_a_specific_checks(self) -> Dict:
        """执行A股特定检查"""
        c = {"price_gaps": 0, "volume_anomalies": 0, "trading_days_check": "PASS", "limit_up_down": 0}
        if self.a_data is None:
            return c
        c["price_gaps"] = int((self.a_data["close"].pct_change().abs() > 0.1).sum())
        vm, vs = self.a_data["volume"].mean(), self.a_data["volume"].std()
        if vs and vs > 0:
            c["volume_anomalies"] = int((self.a_data["volume"] - vm).abs().gt(3 * vs).sum())
        dr = (self.a_data.index[-1] - self.a_data.index[0]).days
        exp = dr * 240 / 365  # A股年交易日约240天
        if exp and abs(len(self.a_data) - exp) / exp > 0.2:
            c["trading_days_check"] = "WARNING"
        # 检查涨跌停
        if "pct_change" in self.a_data.columns:
            c["limit_up_down"] = int((self.a_data["pct_change"].abs() >= 9.5).sum())
        return c

    def _calculate_a_indicators(self) -> Dict:
        """计算A股技术指标"""
        if self.a_data is None:
            return {}
        self.a_data = self.a_calculator.calculate_a_indicators(self.a_data)
        latest = self.a_data.iloc[-1]
        rsi = latest.get("RSI", 0)
        result = {
            "technical_indicators": {
                "trend_indicators": {
                    "MA10": float(latest.get("MA10", 0)),
                    "MA20": float(latest.get("MA20", 0)),
                    "MA50": float(latest.get("MA50", 0)),
                    "MACD": float(latest.get("MACD", 0)),
                    "MACD_signal": float(latest.get("MACD_signal", 0)),
                },
                "momentum_indicators": {
                    "RSI": float(rsi),
                    "RSI_status": "OVERBOUGHT" if rsi > 70 else "OVERSOLD" if rsi < 30 else "NEUTRAL",
                    "STOCH_K": float(latest.get("STOCH_K", 0)),
                    "STOCH_D": float(latest.get("STOCH_D", 0)),
                },
                "a_specific_indicators": {
                    "HV_20": float(latest.get("A_HV_20", 0)),
                    "VOL_INDEX": float(latest.get("A_VOL_INDEX", 0)),
                    "MONEY_FLOW": float(latest.get("A_MONEY_FLOW", 0)),
                },
            },
            "price_data": self._extract_price_history(),
            "volume_analysis": self._analyze_volume_patterns(),
        }
        return result

    def _extract_price_history(self) -> List[Dict]:
        """提取价格历史"""
        if self.a_data is None:
            return []
        out = []
        for idx, row in self.a_data.tail(50).iterrows():
            out.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
                "pct_change": float(row.get("pct_change", 0)),
            })
        return out

    def _analyze_volume_patterns(self) -> Dict:
        """分析成交量模式"""
        if self.a_data is None:
            return {}
        v = self.a_data["volume"]
        recent = v.tail(20).mean()
        hist = v.mean()
        ratio = recent / hist if hist and hist > 0 else 1.0
        return {
            "recent_avg": float(recent),
            "historical_avg": float(hist),
            "volume_ratio": float(ratio),
            "volume_trend": self._determine_volume_trend(v),
            "unusual_volume_days": int((v > v.rolling(20).mean() * 1.5).sum()),
        }

    def _determine_volume_trend(self, vol: pd.Series) -> str:
        """判断成交量趋势"""
        r = vol.tail(5).mean()
        p = vol.tail(10).head(5).mean()
        if not p or p == 0:
            return "STABLE"
        if r > p * 1.2:
            return "INCREASING"
        if r < p * 0.8:
            return "DECREASING"
        return "STABLE"

    def _analyze_a_market(self) -> Dict:
        """分析A股市场特征"""
        if self.a_data is None:
            return {}
        return self.a_calculator.get_a_market_characteristics(self.a_data)

    def _generate_a_charts(self) -> Dict:
        """生成A股图表"""
        charts = {}
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = os.path.join("outputs", "charts")
        os.makedirs(out_dir, exist_ok=True)
        try:
            main_path = os.path.join(out_dir, f"a_main_chart_{ts_str}.png")
            self.chart_renderer.create_a_stock_chart(
                a_data=self.a_data,
                index_data=self.index_data,
                comparison_data=self.comparison_data or None,
                save_path=main_path,
            )
            charts["main_chart"] = main_path
            plt.close("all")
            if self.comparison_data:
                cmp_path = os.path.join(out_dir, f"a_comparison_chart_{ts_str}.png")
                all_data = {self.symbol: self.a_data, **self.comparison_data}
                self.chart_renderer.create_multi_market_comparison(market_data=all_data, save_path=cmp_path)
                charts["comparison_chart"] = cmp_path
                plt.close("all")
            ind_path = os.path.join(out_dir, f"a_indicator_chart_{ts_str}.png")
            self._create_a_indicator_trend_chart(ind_path)
            charts["indicator_chart"] = ind_path
        except Exception as e:
            print(f"生成图表失败: {e}")
        return charts

    def _create_a_indicator_trend_chart(self, save_path: str):
        """创建A股指标趋势图"""
        if self.a_data is None:
            return
        fig, axes = plt.subplots(3, 1, figsize=(15, 10))
        if "A_HV_20" in self.a_data.columns:
            axes[0].plot(self.a_data.index[-100:], self.a_data["A_HV_20"].tail(100), color="orange", lw=2)
            axes[0].set_title("A股历史波动率 (20日)", fontsize=12)
            axes[0].set_ylabel("波动率 (%)", fontsize=10)
            axes[0].grid(True, alpha=0.3)
        if "A_MONEY_FLOW" in self.a_data.columns:
            axes[1].plot(self.a_data.index[-100:], self.a_data["A_MONEY_FLOW"].tail(100), color="blue", lw=2)
            axes[1].axhline(50, color="gray", linestyle="--", alpha=0.5)
            axes[1].set_title("A股资金流向指标", fontsize=12)
            axes[1].set_ylabel("资金流向 (%)", fontsize=10)
            axes[1].set_ylim(0, 100)
            axes[1].grid(True, alpha=0.3)
        if "close" in self.a_data.columns and "volume" in self.a_data.columns:
            ax2 = axes[2].twinx()
            axes[2].plot(self.a_data.index[-100:], self.a_data["close"].tail(100), color="green", lw=2, label="价格")
            axes[2].set_ylabel("价格 (CNY)", fontsize=10, color="green")
            vn = self.a_data["volume"].tail(100)
            vmax = vn.max()
            if vmax and vmax > 0:
                ax2.bar(self.a_data.index[-100:], vn / vmax * 100, alpha=0.3, color="gray", label="成交量")
            ax2.set_ylabel("成交量 (%)", fontsize=10, color="gray")
            axes[2].set_title("A股价格与成交量对比", fontsize=12)
            axes[2].grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()

    def _prepare_a_ai_data(self, analysis_result: Dict) -> Dict:
        """准备A股AI分析数据"""
        mc = analysis_result.get("market_characteristics", {})
        pr = mc.get("price_range", {})
        va = analysis_result.get("volume_analysis", {})
        ti = analysis_result.get("technical_indicators", {})
        ai = {
            "metadata": {
                "symbol": self.symbol,
                "market": self.market,
                "analysis_date": analysis_result["analysis_time"],
                "data_points": len(self.a_data) if self.a_data is not None else 0,
            },
            "current_status": {
                "price": pr.get("current", 0),
                "volume": va.get("recent_avg", 0),
                "market_trend": self._determine_market_trend(),
            },
            "technical_signals": ti,
            "a_specific_analysis": {
                "volatility": mc.get("volatility", {}),
                "liquidity": mc.get("liquidity", {}),
                "a_indicators": ti.get("a_specific_indicators", {}),
            },
            "comparison_data": self._prepare_comparison_summary(),
        }
        os.makedirs("outputs/json_data", exist_ok=True)
        json_path = os.path.join("outputs", "json_data", f"a_ai_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(ai, f, ensure_ascii=False, indent=2)
        ai["json_path"] = json_path
        return ai

    def _determine_market_trend(self) -> str:
        """判断市场趋势"""
        if self.a_data is None or len(self.a_data) < 20:
            return "UNKNOWN"
        c = self.a_data["close"]
        short = "UP" if c.iloc[-1] > c.iloc[-5] else "DOWN"
        ma20 = c.rolling(20).mean()
        mid = "UP" if c.iloc[-1] > ma20.iloc[-1] else "DOWN"
        if short == "UP" and mid == "UP":
            return "STRONG_UP"
        if short == "DOWN" and mid == "DOWN":
            return "STRONG_DOWN"
        return short

    def _prepare_comparison_summary(self) -> Dict:
        """准备对比数据摘要"""
        out = {}
        for sym, data in self.comparison_data.items():
            if data is not None and not data.empty:
                latest = data.iloc[-1]
                pct = data["close"].pct_change().iloc[-1] * 100 if len(data) > 1 else 0
                out[sym] = {"price": float(latest["close"]), "pct_change": float(pct), "volume": float(latest["volume"])}
        return out
