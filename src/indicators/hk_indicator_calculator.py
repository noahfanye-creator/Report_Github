"""
港股技术指标计算器
"""
import numpy as np
import pandas as pd
from typing import Dict

from .calculator import TechnicalIndicatorCalculator


class HKIndicatorCalculator:
    """港股市场技术指标计算器"""

    def __init__(self):
        self.hk_params = {"trading_days_per_year": 250}

    def calculate_hk_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        base = TechnicalIndicatorCalculator(df)
        df = base.calculate_all_indicators()
        df = self._add_hk_specific_indicators(df)
        return df

    def _add_hk_specific_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        if "close" not in df.columns:
            return df
        ret = df["close"].pct_change()
        n = np.sqrt(self.hk_params["trading_days_per_year"])
        df["HK_HV_20"] = ret.rolling(20).std() * n
        df["HK_HV_60"] = ret.rolling(60).std() * n
        hv20 = ret.rolling(20).std() * np.sqrt(250)
        hv60 = ret.rolling(60).std() * np.sqrt(250)
        vol_idx = 0.7 * hv20 + 0.3 * hv60
        rmax = vol_idx.rolling(100).max().replace(0, np.nan)
        df["HK_VOL_INDEX"] = (vol_idx / rmax * 100).fillna(0)

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
            df["HK_MONEY_FLOW"] = (r.fillna(0.5) * 100)

            vma = df["volume"].rolling(20).mean()
            vstd = df["volume"].rolling(20).std()
            thresh = vma + 2 * vstd
            block = df["volume"].where(df["volume"] >= thresh, 0)
            df["HK_BLOCK_TRADE_RATIO"] = (block / df["volume"]).fillna(0)

        df["HK_A_PREMIUM"] = np.nan
        df["HK_CONNECT_NORTH"] = np.nan
        df["HK_CONNECT_SOUTH"] = np.nan
        return df

    def get_hk_market_characteristics(self, data: pd.DataFrame) -> Dict:
        if data.empty:
            return {}
        d = {
            "market_type": "港股",
            "trading_currency": "HKD",
            "data_points": len(data),
            "price_range": {
                "min": float(data["close"].min()),
                "max": float(data["close"].max()),
                "current": float(data["close"].iloc[-1]),
            },
            "volatility": {
                "daily_vol": float(data["close"].pct_change().std()),
                "annual_vol": float(data["close"].pct_change().std() * np.sqrt(250)),
            },
            "liquidity": {
                "avg_volume": float(data["volume"].mean()),
                "avg_amount": float(data["amount"].mean()),
            },
        }
        if "HK_HV_20" in data.columns:
            d["hk_specific"] = {
                "hv_20": float(data["HK_HV_20"].iloc[-1]),
                "vol_index": float(data.get("HK_VOL_INDEX", pd.Series([0])).iloc[-1]),
                "money_flow": float(data.get("HK_MONEY_FLOW", pd.Series([50])).iloc[-1]),
            }
        return d
