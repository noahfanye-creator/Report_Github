"""
数据质量验证
"""
import pandas as pd
import numpy as np
from typing import Dict


class DataQualityValidator:
    """数据质量验证系统"""

    @staticmethod
    def validate_ohlcv(df: pd.DataFrame) -> Dict:
        """
        验证OHLCV数据质量
        返回质量报告
        """
        report = {
            "status": "PASS",
            "issues": [],
            "statistics": {},
            "completeness": 0.0,
        }

        required_cols = ["open", "high", "low", "close", "volume"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            report["status"] = "FAIL"
            report["issues"].append(f"缺少必要列: {missing_cols}")
            return report

        for col in ["open", "high", "low", "close"]:
            if col in df.columns and df[col].max() > 100000:
                report["issues"].append(f"{col}价格异常高: {df[col].max()}")

        logic_errors = 0
        for _, row in df.iterrows():
            if not (
                row["low"] <= row["open"] <= row["high"]
                and row["low"] <= row["close"] <= row["high"]
            ):
                logic_errors += 1
        if logic_errors > 0:
            report["issues"].append(f"发现 {logic_errors} 条OHLC逻辑错误")

        missing_vals = df[required_cols].isnull().sum().sum()
        total_vals = len(df) * len(required_cols)
        completeness = 1.0 - missing_vals / total_vals if total_vals else 0.0
        report["completeness"] = completeness
        if completeness < 0.95:
            report["status"] = "WARNING"
            report["issues"].append(f"数据完整度较低: {completeness:.2%}")

        if isinstance(df.index, pd.DatetimeIndex):
            date_diff = df.index.to_series().diff().dt.days
            gap_days = date_diff[date_diff > 1]
            if len(gap_days) > 0:
                report["issues"].append(f"数据存在 {len(gap_days)} 处时间间隔超过1天")

        report["statistics"] = {
            "data_points": len(df),
            "date_range": (str(df.index.min()), str(df.index.max())),
            "price_mean": float(df["close"].mean()),
            "price_std": float(df["close"].std()),
            "volume_mean": float(df["volume"].mean()),
            "completeness": completeness,
        }
        return report

    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        """数据清洗"""
        df_clean = df.copy()
        df_clean = df_clean.ffill().bfill()

        df_clean["high"] = df_clean[["high", "open", "close"]].max(axis=1)
        df_clean["low"] = df_clean[["low", "open", "close"]].min(axis=1)

        for col in ["open", "high", "low", "close"]:
            if col not in df_clean.columns:
                continue
            q1, q3 = df_clean[col].quantile(0.25), df_clean[col].quantile(0.75)
            iqr = q3 - q1
            lb, ub = q1 - 3 * iqr, q3 + 3 * iqr
            df_clean[col] = df_clean[col].clip(lb, ub)

        if "volume" in df_clean.columns:
            df_clean["volume_log"] = np.log1p(df_clean["volume"])

        df_clean = df_clean[~df_clean.index.duplicated(keep="first")]
        return df_clean
