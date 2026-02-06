"""
A股技术指标计算器
"""
import numpy as np
import pandas as pd
from typing import Dict

from .calculator import TechnicalIndicatorCalculator


class AIndicatorCalculator:
    """A股市场技术指标计算器"""

    def __init__(self):
        self.a_params = {"trading_days_per_year": 240}  # A股年交易日约240天

    def calculate_a_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算A股技术指标"""
        df = data.copy()
        base = TechnicalIndicatorCalculator(df)
        df = base.calculate_all_indicators()
        df = self._add_a_specific_indicators(df)
        return df

    def _add_a_specific_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加A股特有指标"""
        if "close" not in df.columns:
            return df
        
        # A股历史波动率
        ret = df["close"].pct_change()
        n = np.sqrt(self.a_params["trading_days_per_year"])
        df["A_HV_20"] = ret.rolling(20).std() * n * 100  # 转换为百分比
        df["A_HV_60"] = ret.rolling(60).std() * n * 100
        
        # A股波动率指数
        hv20 = ret.rolling(20).std() * np.sqrt(240) * 100
        hv60 = ret.rolling(60).std() * np.sqrt(240) * 100
        vol_idx = 0.7 * hv20 + 0.3 * hv60
        rmax = vol_idx.rolling(100).max().replace(0, np.nan)
        df["A_VOL_INDEX"] = (vol_idx / rmax * 100).fillna(0)

        # A股资金流向指标
        if all(c in df.columns for c in ["close", "volume", "amount"]):
            tp = (df["high"] + df["low"] + df["close"]) / 3
            mf = tp * df["volume"]
            pc = df["close"].diff()
            mf_pos = mf.copy()
            mf_neg = mf.copy()
            mf_pos[pc <= 0] = 0
            mf_neg[pc > 0] = 0
            s20 = mf_pos.rolling(20).sum()
            s20n = mf_neg.rolling(20).sum()
            r = s20 / (s20 + s20n).replace(0, np.nan)
            df["A_MONEY_FLOW"] = (r.fillna(0.5) * 100)

            # A股大单交易比例
            vma = df["volume"].rolling(20).mean()
            vstd = df["volume"].rolling(20).std()
            thresh = vma + 2 * vstd
            block = df["volume"].where(df["volume"] >= thresh, 0)
            df["A_BLOCK_TRADE_RATIO"] = (block / df["volume"]).fillna(0)

        # A股涨跌停标识（如果价格变动接近±10%或±20%）
        if "pct_change" in df.columns:
            df["A_LIMIT_UP"] = (df["pct_change"] >= 9.5) | (df["pct_change"] >= 19.5)
            df["A_LIMIT_DOWN"] = (df["pct_change"] <= -9.5) | (df["pct_change"] <= -19.5)

        return df

    def get_a_market_characteristics(self, data: pd.DataFrame) -> Dict:
        """获取A股市场特征"""
        if data.empty:
            return {}
        d = {
            "market_type": "A股",
            "trading_currency": "CNY",
            "data_points": len(data),
            "price_range": {
                "min": float(data["close"].min()),
                "max": float(data["close"].max()),
                "current": float(data["close"].iloc[-1]),
            },
            "volatility": {
                "daily_vol": float(data["close"].pct_change().std()),
                "annual_vol": float(data["close"].pct_change().std() * np.sqrt(240)),
            },
            "liquidity": {
                "avg_volume": float(data["volume"].mean()),
                "avg_amount": float(data["amount"].mean()),
            },
        }
        if "A_HV_20" in data.columns:
            d["a_specific"] = {
                "hv_20": float(data["A_HV_20"].iloc[-1]),
                "vol_index": float(data.get("A_VOL_INDEX", pd.Series([0])).iloc[-1]),
                "money_flow": float(data.get("A_MONEY_FLOW", pd.Series([50])).iloc[-1]),
            }
        return d
