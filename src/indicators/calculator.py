"""
技术指标计算器（pandas 实现，无需 TA-Lib）
"""
import numpy as np
import pandas as pd

from .formulas.ma_formulas import calculate_ema, calculate_sma
from .formulas.macd_formulas import calculate_macd
from .formulas.rsi_formulas import calculate_rsi


class TechnicalIndicatorCalculator:
    """技术指标计算器"""

    def __init__(self, data: pd.DataFrame):
        self.data = data.copy()
        self.indicators = {}

    def calculate_all_indicators(self) -> pd.DataFrame:
        """计算所有技术指标"""
        self._calculate_trend_indicators()
        self._calculate_momentum_indicators()
        self._calculate_volatility_indicators()
        self._calculate_volume_indicators()

        result = self.data.copy()
        for cat, inds in self.indicators.items():
            for name, vals in inds.items():
                result[name] = vals
        return result

    def _calculate_trend_indicators(self):
        close = self.data["close"]
        macd_line, signal_line, hist = calculate_macd(close)
        self.indicators["trend"] = {
            "MA5": calculate_sma(close, 5),
            "MA10": calculate_sma(close, 10),
            "MA20": calculate_sma(close, 20),
            "MA30": calculate_sma(close, 30),
            "MA50": calculate_sma(close, 50),
            "MA60": calculate_sma(close, 60),
            "EMA12": calculate_ema(close, 12),
            "EMA26": calculate_ema(close, 26),
            "MACD": macd_line,
            "MACD_signal": signal_line,
            "MACD_hist": hist,
        }

    def _calculate_momentum_indicators(self):
        close = self.data["close"]
        high, low = self.data["high"], self.data["low"]
        low_14 = low.rolling(14).min()
        high_14 = high.rolling(14).max()
        r = (high_14 - low_14).replace(0, np.nan)
        stoch_k = 100 * (close - low_14) / r
        stoch_d = stoch_k.rolling(3).mean()
        self.indicators["momentum"] = {
            "RSI": calculate_rsi(close, 14),
            "STOCH_K": stoch_k,
            "STOCH_D": stoch_d,
        }

    def _calculate_volatility_indicators(self):
        close = self.data["close"]
        mid = close.rolling(20).mean()
        std = close.rolling(20).std()
        upper = mid + 2 * std
        lower = mid - 2 * std
        width = (upper - lower) / mid.replace(0, np.nan)
        atr = (
            pd.concat(
                [
                    self.data["high"] - self.data["low"],
                    (self.data["high"] - self.data["close"].shift(1)).abs(),
                    (self.data["low"] - self.data["close"].shift(1)).abs(),
                ],
                axis=1,
            )
            .max(axis=1)
            .rolling(14)
            .mean()
        )
        self.indicators["volatility"] = {
            "BB_upper": upper,
            "BB_middle": mid,
            "BB_lower": lower,
            "BB_width": width,
            "ATR": atr,
        }

    def _calculate_volume_indicators(self):
        vol = self.data["volume"]
        close = self.data["close"]
        obv = (np.sign(close.diff()) * vol).fillna(0).cumsum()
        self.indicators["volume"] = {
            "VOL_MA5": vol.rolling(5).mean(),
            "VOL_MA10": vol.rolling(10).mean(),
            "VOL_MA20": vol.rolling(20).mean(),
            "OBV": obv,
        }
