"""
港股分析流水线
"""
from datetime import datetime
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import pandas as pd
import json
import os

from data_sources.unified_market_data import UnifiedMarketDataSystem
from indicators.hk_indicator_calculator import HKIndicatorCalculator
from visualizer.multi_market_chart_renderer import MultiMarketChartRenderer
from utils.data_validator import DataQualityValidator


class HKAnalysisPipeline:
    """港股分析流水线"""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.market = "港股"
        self.data_system = UnifiedMarketDataSystem(["akshare", "yfinance"])
        self.hk_calculator = HKIndicatorCalculator()
        self.chart_renderer = MultiMarketChartRenderer()
        self.validator = DataQualityValidator()
        self.hk_data = None
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
        print(f"开始港股分析: {self.symbol}")
        print("=" * 60)

        self._fetch_hk_data(start_date, end_date)
        if include_index:
            self._fetch_hk_index_data(start_date, end_date)
        if include_comparison:
            self._fetch_comparison_data(include_comparison, start_date, end_date)

        quality_report = self._validate_hk_data()
        result["quality_report"] = quality_report

        indicators_data = self._calculate_hk_indicators()
        result.update(indicators_data)

        market_characteristics = self._analyze_hk_market()
        result["market_characteristics"] = market_characteristics

        charts = self._generate_hk_charts()
        result["charts"] = charts

        ai_data = self._prepare_hk_ai_data(result)
        result["ai_data"] = ai_data

        print("\n" + "=" * 60)
        print("港股分析完成!")
        print(f"数据点数: {len(self.hk_data) if self.hk_data is not None else 0}")
        print(f"数据质量: {quality_report.get('status', 'UNKNOWN')}")
        print(f"生成图表: {len(charts)}张")
        print("=" * 60)
        return result

    def _fetch_hk_data(self, start_date: str, end_date: str):
        self.hk_data = self.data_system.get_market_data(
            symbol=self.symbol, market=self.market,
            start_date=start_date, end_date=end_date, data_type="daily"
        )
        if self.hk_data is None or self.hk_data.empty:
            raise ValueError(f"无法获取港股 {self.symbol} 数据")
        print(f"获取港股数据成功: {len(self.hk_data)} 条")

    def _fetch_hk_index_data(self, start_date: str, end_date: str):
        self.index_data = self.data_system.get_hk_index_data(
            index_code="HSI", start_date=start_date, end_date=end_date
        )
        if self.index_data is not None:
            print(f"恒生指数数据: {len(self.index_data)} 条")

    def _fetch_comparison_data(self, symbols: List[str], start_date: str, end_date: str):
        for s in symbols:
            try:
                d = self.data_system.get_market_data(s, start_date, end_date, data_type="daily")
                if d is not None:
                    self.comparison_data[s] = d
                    print(f"对比数据 {s} 成功")
            except Exception as e:
                print(f"对比数据 {s} 失败: {e}")

    def _validate_hk_data(self) -> Dict:
        if self.hk_data is None:
            return {"status": "FAIL", "message": "没有数据"}
        base = self.validator.validate_ohlcv(self.hk_data)
        vol = self.hk_data["volume"]
        hk_report = {
            "status": base["status"],
            "completeness": base["completeness"],
            "data_points": len(self.hk_data),
            "price_range": {
                "min": float(self.hk_data["low"].min()),
                "max": float(self.hk_data["high"].max()),
                "current": float(self.hk_data["close"].iloc[-1]),
            },
            "volume_analysis": {
                "avg_volume": float(vol.mean()),
                "max_volume": float(vol.max()),
                "recent_volume": float(vol.tail(5).mean()),
            },
            "hk_specific_checks": self._perform_hk_specific_checks(),
        }
        return hk_report

    def _perform_hk_specific_checks(self) -> Dict:
        c = {"price_gaps": 0, "volume_anomalies": 0, "trading_days_check": "PASS"}
        if self.hk_data is None:
            return c
        c["price_gaps"] = int((self.hk_data["close"].pct_change().abs() > 0.1).sum())
        vm, vs = self.hk_data["volume"].mean(), self.hk_data["volume"].std()
        if vs and vs > 0:
            c["volume_anomalies"] = int((self.hk_data["volume"] - vm).abs().gt(3 * vs).sum())
        dr = (self.hk_data.index[-1] - self.hk_data.index[0]).days
        exp = dr * 250 / 365
        if exp and abs(len(self.hk_data) - exp) / exp > 0.2:
            c["trading_days_check"] = "WARNING"
        return c

    def _calculate_hk_indicators(self) -> Dict:
        if self.hk_data is None:
            return {}
        self.hk_data = self.hk_calculator.calculate_hk_indicators(self.hk_data)
        latest = self.hk_data.iloc[-1]
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
                "hk_specific_indicators": {
                    "HV_20": float(latest.get("HK_HV_20", 0)),
                    "VOL_INDEX": float(latest.get("HK_VOL_INDEX", 0)),
                    "MONEY_FLOW": float(latest.get("HK_MONEY_FLOW", 0)),
                },
            },
            "price_data": self._extract_price_history(),
            "volume_analysis": self._analyze_volume_patterns(),
        }
        return result

    def _extract_price_history(self) -> List[Dict]:
        if self.hk_data is None:
            return []
        out = []
        for idx, row in self.hk_data.tail(50).iterrows():
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
        if self.hk_data is None:
            return {}
        v = self.hk_data["volume"]
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
        r = vol.tail(5).mean()
        p = vol.tail(10).head(5).mean()
        if not p or p == 0:
            return "STABLE"
        if r > p * 1.2:
            return "INCREASING"
        if r < p * 0.8:
            return "DECREASING"
        return "STABLE"

    def _analyze_hk_market(self) -> Dict:
        if self.hk_data is None:
            return {}
        return self.hk_calculator.get_hk_market_characteristics(self.hk_data)

    def _generate_hk_charts(self) -> Dict:
        charts = {}
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = os.path.join("outputs", "charts")
        os.makedirs(out_dir, exist_ok=True)
        try:
            main_path = os.path.join(out_dir, f"hk_main_chart_{ts_str}.png")
            self.chart_renderer.create_hk_stock_chart(
                hk_data=self.hk_data,
                index_data=self.index_data,
                comparison_data=self.comparison_data or None,
                save_path=main_path,
            )
            charts["main_chart"] = main_path
            plt.close("all")
            if self.comparison_data:
                cmp_path = os.path.join(out_dir, f"hk_comparison_chart_{ts_str}.png")
                all_data = {self.symbol: self.hk_data, **self.comparison_data}
                self.chart_renderer.create_multi_market_comparison(market_data=all_data, save_path=cmp_path)
                charts["comparison_chart"] = cmp_path
                plt.close("all")
            ind_path = os.path.join(out_dir, f"hk_indicator_chart_{ts_str}.png")
            self._create_hk_indicator_trend_chart(ind_path)
            charts["indicator_chart"] = ind_path
        except Exception as e:
            print(f"生成图表失败: {e}")
        return charts

    def _create_hk_indicator_trend_chart(self, save_path: str):
        if self.hk_data is None:
            return
        fig, axes = plt.subplots(3, 1, figsize=(15, 10))
        if "HK_HV_20" in self.hk_data.columns:
            axes[0].plot(self.hk_data.index[-100:], self.hk_data["HK_HV_20"].tail(100), color="orange", lw=2)
            axes[0].set_title("港股历史波动率 (20日)", fontsize=12)
            axes[0].set_ylabel("波动率 (%)", fontsize=10)
            axes[0].grid(True, alpha=0.3)
        if "HK_MONEY_FLOW" in self.hk_data.columns:
            axes[1].plot(self.hk_data.index[-100:], self.hk_data["HK_MONEY_FLOW"].tail(100), color="blue", lw=2)
            axes[1].axhline(50, color="gray", linestyle="--", alpha=0.5)
            axes[1].set_title("港股资金流向指标", fontsize=12)
            axes[1].set_ylabel("资金流向 (%)", fontsize=10)
            axes[1].set_ylim(0, 100)
            axes[1].grid(True, alpha=0.3)
        if "close" in self.hk_data.columns and "volume" in self.hk_data.columns:
            ax2 = axes[2].twinx()
            axes[2].plot(self.hk_data.index[-100:], self.hk_data["close"].tail(100), color="green", lw=2, label="价格")
            axes[2].set_ylabel("价格 (HKD)", fontsize=10, color="green")
            vn = self.hk_data["volume"].tail(100)
            vmax = vn.max()
            if vmax and vmax > 0:
                ax2.bar(self.hk_data.index[-100:], vn / vmax * 100, alpha=0.3, color="gray", label="成交量")
            ax2.set_ylabel("成交量 (%)", fontsize=10, color="gray")
            axes[2].set_title("港股价格与成交量对比", fontsize=12)
            axes[2].grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()

    def _prepare_hk_ai_data(self, analysis_result: Dict) -> Dict:
        mc = analysis_result.get("market_characteristics", {})
        pr = mc.get("price_range", {})
        va = analysis_result.get("volume_analysis", {})
        ti = analysis_result.get("technical_indicators", {})
        ai = {
            "metadata": {
                "symbol": self.symbol,
                "market": self.market,
                "analysis_date": analysis_result["analysis_time"],
                "data_points": len(self.hk_data) if self.hk_data is not None else 0,
            },
            "current_status": {
                "price": pr.get("current", 0),
                "volume": va.get("recent_avg", 0),
                "market_trend": self._determine_market_trend(),
            },
            "technical_signals": ti,
            "hk_specific_analysis": {
                "volatility": mc.get("volatility", {}),
                "liquidity": mc.get("liquidity", {}),
                "hk_indicators": ti.get("hk_specific_indicators", {}),
            },
            "comparison_data": self._prepare_comparison_summary(),
        }
        os.makedirs("outputs/json_data", exist_ok=True)
        json_path = os.path.join("outputs", "json_data", f"hk_ai_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(ai, f, ensure_ascii=False, indent=2)
        ai["json_path"] = json_path
        return ai

    def _determine_market_trend(self) -> str:
        if self.hk_data is None or len(self.hk_data) < 20:
            return "UNKNOWN"
        c = self.hk_data["close"]
        short = "UP" if c.iloc[-1] > c.iloc[-5] else "DOWN"
        ma20 = c.rolling(20).mean()
        mid = "UP" if c.iloc[-1] > ma20.iloc[-1] else "DOWN"
        if short == "UP" and mid == "UP":
            return "STRONG_UP"
        if short == "DOWN" and mid == "DOWN":
            return "STRONG_DOWN"
        return short

    def _prepare_comparison_summary(self) -> Dict:
        out = {}
        for sym, data in self.comparison_data.items():
            if data is not None and not data.empty:
                latest = data.iloc[-1]
                pct = data["close"].pct_change().iloc[-1] * 100 if len(data) > 1 else 0
                out[sym] = {"price": float(latest["close"]), "pct_change": float(pct), "volume": float(latest["volume"])}
        return out
