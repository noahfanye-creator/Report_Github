"""
多市场图表渲染器
"""
from typing import Dict

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd
import numpy as np

try:
    import mplfinance as mpf
except ImportError:
    mpf = None


class MultiMarketChartRenderer:
    """多市场图表渲染器"""

    def __init__(self):
        self.colors = {
            "hk_primary": "#E74C3C",
            "hk_secondary": "#C0392B",
            "a_primary": "#2E86AB",
            "a_secondary": "#1A5276",
            "us_primary": "#27AE60",
            "index_color": "#8E44AD",
        }
        self.market_styles = {
            "港股": {
                "candle_up": "#E74C3C",
                "candle_down": "#27AE60",
                "ma_colors": ["#FF6B6B", "#FF8E53", "#FFAA64", "#FFC785"],
            },
            "A股": {
                "candle_up": "#E74C3C",
                "candle_down": "#27AE60",
                "ma_colors": ["#2E86AB", "#45B7D1", "#73C6B6", "#95A5A6"],
            },
            "美股": {
                "candle_up": "#27AE60",
                "candle_down": "#E74C3C",
                "ma_colors": ["#27AE60", "#2ECC71", "#58D68D", "#82E0AA"],
            },
        }

    def create_hk_stock_chart(
        self,
        hk_data: pd.DataFrame,
        index_data: pd.DataFrame = None,
        comparison_data: Dict = None,
        save_path: str = "hk_chart.png",
    ) -> plt.Figure:
        fig = plt.figure(figsize=(18, 12))
        gs = gridspec.GridSpec(4, 3, figure=fig, height_ratios=[3, 1, 1, 1], width_ratios=[3, 1, 1])
        ax_main = fig.add_subplot(gs[0, 0])
        self._plot_hk_main_chart(ax_main, hk_data)
        ax_vol = fig.add_subplot(gs[1, 0], sharex=ax_main)
        self._plot_hk_volume_chart(ax_vol, hk_data)
        ax_macd = fig.add_subplot(gs[2, 0], sharex=ax_main)
        self._plot_hk_macd_chart(ax_macd, hk_data)
        ax_rsi = fig.add_subplot(gs[3, 0], sharex=ax_main)
        self._plot_hk_rsi_chart(ax_rsi, hk_data)
        if index_data is not None:
            ax_idx = fig.add_subplot(gs[0, 1])
            self._plot_hk_index_chart(ax_idx, index_data, hk_data)
        ax_panel = fig.add_subplot(gs[0, 2])
        self._plot_hk_indicator_panel(ax_panel, hk_data)
        if comparison_data:
            ax_cmp = fig.add_subplot(gs[1:, 1:])
            self._plot_market_comparison(ax_cmp, hk_data, comparison_data)
        sym = hk_data["symbol"].iloc[0] if "symbol" in hk_data.columns else "HK"
        plt.suptitle(f"港股技术分析 - {sym}", fontsize=16, fontweight="bold")
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
        return fig

    def _plot_hk_main_chart(self, ax, hk_data: pd.DataFrame):
        style = self.market_styles.get("港股", self.market_styles["A股"])
        ohlcv = ["open", "high", "low", "close", "volume"]
        plot_df = hk_data[[c for c in ohlcv if c in hk_data.columns]].tail(100).copy()
        if mpf is not None:
            plot_df = plot_df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
            mpf.plot(plot_df, type="candle", ax=ax, style="yahoo")
        else:
            ax.plot(plot_df.index, plot_df["close"], color="gray", label="收盘价", lw=1)
            ax.fill_between(plot_df.index, plot_df["low"], plot_df["high"], alpha=0.2)
        for i, (name, key) in enumerate([("MA10", "MA10"), ("MA20", "MA20"), ("MA50", "MA50")]):
            if key in hk_data.columns:
                ax.plot(hk_data.index[-100:], hk_data[key].tail(100), color=style["ma_colors"][i % len(style["ma_colors"])], label=name, lw=1.5)
        if all(c in hk_data.columns for c in ["BB_upper", "BB_lower"]):
            ax.fill_between(hk_data.index[-100:], hk_data["BB_upper"].tail(100), hk_data["BB_lower"].tail(100), alpha=0.2, color="gray")
        ax.set_title("港股价格走势", fontsize=12, fontweight="bold")
        ax.set_ylabel("价格 (HKD)", fontsize=10)
        ax.legend(loc="upper left", fontsize=8)
        ax.grid(True, alpha=0.3)
        cur = hk_data["close"].iloc[-1]
        ax.annotate(f"当前: {cur:.2f} HKD", xy=(0.02, 0.95), xycoords="axes fraction", fontsize=9, bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))

    def _plot_hk_volume_chart(self, ax, hk_data: pd.DataFrame):
        v = hk_data["volume"].tail(100)
        colors = ["red" if c >= o else "green" for c, o in zip(hk_data["close"].tail(100), hk_data["open"].tail(100))]
        ax.bar(hk_data.index[-100:], v, color=colors, alpha=0.7, width=0.8)
        if "VOL_MA20" in hk_data.columns:
            ax.plot(hk_data.index[-100:], hk_data["VOL_MA20"].tail(100), color="blue", label="VOL_MA20", lw=1.5)
        ax.set_ylabel("成交量", fontsize=10)
        ax.legend(loc="upper left", fontsize=8)
        ax.grid(True, alpha=0.3)
        if v.min() > 0 and v.max() / v.min() > 10:
            ax.set_yscale("log")

    def _plot_hk_macd_chart(self, ax, hk_data: pd.DataFrame):
        if not all(c in hk_data.columns for c in ["MACD", "MACD_signal", "MACD_hist"]):
            return
        ax.plot(hk_data.index[-100:], hk_data["MACD"].tail(100), color="blue", label="MACD", lw=1.5)
        ax.plot(hk_data.index[-100:], hk_data["MACD_signal"].tail(100), color="red", label="Signal", lw=1.5)
        ax.bar(hk_data.index[-100:], hk_data["MACD_hist"].tail(100), color=["green" if x >= 0 else "red" for x in hk_data["MACD_hist"].tail(100)], alpha=0.5, width=0.8)
        ax.axhline(0, color="black", linestyle="-", lw=0.5)
        ax.set_ylabel("MACD", fontsize=10)
        ax.legend(loc="upper left", fontsize=8)
        ax.grid(True, alpha=0.3)

    def _plot_hk_rsi_chart(self, ax, hk_data: pd.DataFrame):
        if "RSI" not in hk_data.columns:
            return
        ax.plot(hk_data.index[-100:], hk_data["RSI"].tail(100), color="purple", lw=2, label="RSI(14)")
        ax.axhline(70, color="red", linestyle="--", lw=1, label="超买")
        ax.axhline(30, color="green", linestyle="--", lw=1, label="超卖")
        ax.fill_between(hk_data.index[-100:], 30, 70, alpha=0.1, color="gray")
        ax.set_ylabel("RSI", fontsize=10)
        ax.set_ylim(0, 100)
        ax.legend(loc="upper left", fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel("日期", fontsize=10)

    def _plot_hk_index_chart(self, ax, index_data: pd.DataFrame, hk_data: pd.DataFrame):
        ci = index_data.index.intersection(hk_data.index)
        if len(ci) == 0:
            return
        hp = hk_data.loc[ci, "close"]
        ip = index_data.loc[ci, "close"]
        hn = hp / hp.iloc[0] * 100
        inn = ip / ip.iloc[0] * 100
        sym = hk_data["symbol"].iloc[0] if "symbol" in hk_data.columns else "HK"
        ax.plot(ci[-100:], hn.tail(100), color=self.colors["hk_primary"], label=sym, lw=2)
        ax.plot(ci[-100:], inn.tail(100), color=self.colors["index_color"], label="恒生指数", lw=2)
        ax.set_title("相对恒生指数表现", fontsize=10)
        ax.set_ylabel("相对表现 (%)", fontsize=9)
        ax.legend(loc="upper left", fontsize=8)
        ax.grid(True, alpha=0.3)

    def _plot_hk_indicator_panel(self, ax, hk_data: pd.DataFrame):
        ax.axis("off")
        latest = hk_data.iloc[-1]
        rows = [["价格 (HKD)", f"{latest['close']:.2f}"]]
        if "pct_change" in hk_data.columns:
            pct = hk_data["pct_change"].iloc[-1]
            tag = "🔴" if pct > 0 else "🟢"
            rows.append(["日涨跌幅", f"{tag} {pct:+.2f}%"])
        if "HK_HV_20" in hk_data.columns:
            rows.append(["历史波动率", f"{latest['HK_HV_20']:.1f}%"])
        if "HK_VOL_INDEX" in hk_data.columns:
            vi = latest["HK_VOL_INDEX"]
            vs = "高" if vi > 70 else "低" if vi < 30 else "中"
            rows.append(["波动率指数", f"{vi:.1f} ({vs})"])
        if "HK_MONEY_FLOW" in hk_data.columns:
            mf = latest["HK_MONEY_FLOW"]
            fs = "流入" if mf > 60 else "流出" if mf < 40 else "平衡"
            rows.append(["资金流向", f"{mf:.1f} ({fs})"])
        if "volume" in hk_data.columns:
            vol_ma = hk_data["volume"].rolling(20).mean().iloc[-1]
            vr = latest["volume"] / vol_ma if vol_ma and vol_ma > 0 else 1
            vs = "放量" if vr > 1.5 else "缩量" if vr < 0.5 else "正常"
            rows.append(["成交量", f"{vr:.1f}x ({vs})"])
        if rows:
            t = ax.table(cellText=rows, cellLoc="left", loc="center", colWidths=[0.5, 0.5])
            t.auto_set_font_size(False)
            t.set_fontsize(9)
            t.scale(1, 2)
            for i in range(len(rows)):
                t[i, 0].set_facecolor("#F2F3F4")
                t[i, 0].set_text_props(weight="bold")
        ax.set_title("港股特有指标", fontsize=11, fontweight="bold", pad=20)

    def _plot_market_comparison(self, ax, hk_data: pd.DataFrame, comparison_data: Dict):
        md = {hk_data["symbol"].iloc[0] if "symbol" in hk_data.columns else "HK": hk_data}
        md.update(comparison_data)
        for label, d in md.items():
            if d is not None and "close" in d.columns:
                n = d["close"] / d["close"].iloc[0] * 100
                ax.plot(d.index, n, label=label, lw=2)
        ax.set_title("多市场对比", fontsize=12)
        ax.set_ylabel("相对价格 (%)", fontsize=10)
        ax.legend(loc="upper left", fontsize=9)
        ax.grid(True, alpha=0.3)

    def create_multi_market_comparison(
        self,
        market_data: Dict[str, pd.DataFrame],
        save_path: str = "market_comparison.png",
    ) -> plt.Figure:
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        ax1, ax2, ax3, ax4 = axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]
        self._plot_price_comparison(ax1, market_data)
        self._plot_volatility_comparison(ax2, market_data)
        self._plot_correlation_analysis(ax3, market_data)
        self._plot_relative_strength(ax4, market_data)
        plt.suptitle("多市场对比分析", fontsize=16, fontweight="bold")
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
        return fig

    def _plot_price_comparison(self, ax, market_data: Dict):
        for label, data in market_data.items():
            if data is not None and "close" in data.columns:
                n = data["close"] / data["close"].iloc[0] * 100
                ax.plot(data.index, n, label=label, lw=2)
        ax.set_title("价格走势对比 (归一化)", fontsize=12)
        ax.set_ylabel("相对价格 (%)", fontsize=10)
        ax.legend(loc="upper left", fontsize=9)
        ax.grid(True, alpha=0.3)

    def _plot_volatility_comparison(self, ax, market_data: Dict):
        for label, data in market_data.items():
            if data is not None and "close" in data.columns:
                vol = data["close"].pct_change().rolling(20).std() * np.sqrt(252) * 100
                ax.plot(data.index, vol, label=label, lw=1.5)
        ax.set_title("波动率对比 (20日年化)", fontsize=12)
        ax.set_ylabel("波动率 (%)", fontsize=10)
        ax.legend(loc="upper left", fontsize=9)
        ax.grid(True, alpha=0.3)

    def _plot_correlation_analysis(self, ax, market_data: Dict):
        valid = {k: v for k, v in market_data.items() if v is not None and "close" in v.columns and len(v) > 20}
        if len(valid) < 2:
            ax.text(0.5, 0.5, "数据不足", ha="center", va="center", transform=ax.transAxes)
            return
        rev = pd.DataFrame({k: v["close"].pct_change() for k, v in valid.items()}).dropna()
        corr = rev.corr()
        im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_xticks(range(len(corr)))
        ax.set_xticklabels(list(corr.columns), rotation=45, ha="right")
        ax.set_yticks(range(len(corr)))
        ax.set_yticklabels(list(corr.columns))
        plt.colorbar(im, ax=ax)
        ax.set_title("收益率相关性", fontsize=12)

    def _plot_relative_strength(self, ax, market_data: Dict):
        for label, data in market_data.items():
            if data is not None and "close" in data.columns:
                n = data["close"] / data["close"].iloc[0] * 100
                ax.plot(data.index, n, label=label, lw=2)
        ax.set_title("相对强度", fontsize=12)
        ax.set_ylabel("相对强度 (%)", fontsize=10)
        ax.legend(loc="upper left", fontsize=9)
        ax.grid(True, alpha=0.3)

    def create_a_stock_chart(
        self,
        a_data: pd.DataFrame,
        index_data: pd.DataFrame = None,
        comparison_data: Dict = None,
        save_path: str = "a_chart.png",
    ) -> plt.Figure:
        """创建A股技术分析图表"""
        fig = plt.figure(figsize=(18, 12))
        gs = gridspec.GridSpec(4, 3, figure=fig, height_ratios=[3, 1, 1, 1], width_ratios=[3, 1, 1])
        ax_main = fig.add_subplot(gs[0, 0])
        self._plot_a_main_chart(ax_main, a_data)
        ax_vol = fig.add_subplot(gs[1, 0], sharex=ax_main)
        self._plot_a_volume_chart(ax_vol, a_data)
        ax_macd = fig.add_subplot(gs[2, 0], sharex=ax_main)
        self._plot_a_macd_chart(ax_macd, a_data)
        ax_rsi = fig.add_subplot(gs[3, 0], sharex=ax_main)
        self._plot_a_rsi_chart(ax_rsi, a_data)
        if index_data is not None:
            ax_idx = fig.add_subplot(gs[0, 1])
            self._plot_a_index_chart(ax_idx, index_data, a_data)
        ax_panel = fig.add_subplot(gs[0, 2])
        self._plot_a_indicator_panel(ax_panel, a_data)
        if comparison_data:
            ax_cmp = fig.add_subplot(gs[1:, 1:])
            self._plot_market_comparison(ax_cmp, a_data, comparison_data)
        sym = a_data["symbol"].iloc[0] if "symbol" in a_data.columns else "A"
        plt.suptitle(f"A股技术分析 - {sym}", fontsize=16, fontweight="bold")
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
        return fig

    def _plot_a_main_chart(self, ax, a_data: pd.DataFrame):
        """绘制A股主图"""
        style = self.market_styles.get("A股", self.market_styles["港股"])
        ohlcv = ["open", "high", "low", "close", "volume"]
        plot_df = a_data[[c for c in ohlcv if c in a_data.columns]].tail(100).copy()
        if mpf is not None:
            plot_df = plot_df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
            mpf.plot(plot_df, type="candle", ax=ax, style="yahoo")
        else:
            ax.plot(plot_df.index, plot_df["close"], color="gray", label="收盘价", lw=1)
            ax.fill_between(plot_df.index, plot_df["low"], plot_df["high"], alpha=0.2)
        for i, (name, key) in enumerate([("MA10", "MA10"), ("MA20", "MA20"), ("MA50", "MA50")]):
            if key in a_data.columns:
                ax.plot(a_data.index[-100:], a_data[key].tail(100), color=style["ma_colors"][i % len(style["ma_colors"])], label=name, lw=1.5)
        if all(c in a_data.columns for c in ["BB_upper", "BB_lower"]):
            ax.fill_between(a_data.index[-100:], a_data["BB_upper"].tail(100), a_data["BB_lower"].tail(100), alpha=0.2, color="gray")
        ax.set_title("A股价格走势", fontsize=12, fontweight="bold")
        ax.set_ylabel("价格 (CNY)", fontsize=10)
        ax.legend(loc="upper left", fontsize=8)
        ax.grid(True, alpha=0.3)
        cur = a_data["close"].iloc[-1]
        ax.annotate(f"当前: {cur:.2f} CNY", xy=(0.02, 0.95), xycoords="axes fraction", fontsize=9, bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))

    def _plot_a_volume_chart(self, ax, a_data: pd.DataFrame):
        """绘制A股成交量图"""
        v = a_data["volume"].tail(100)
        colors = ["red" if c >= o else "green" for c, o in zip(a_data["close"].tail(100), a_data["open"].tail(100))]
        ax.bar(a_data.index[-100:], v, color=colors, alpha=0.7, width=0.8)
        if "VOL_MA20" in a_data.columns:
            ax.plot(a_data.index[-100:], a_data["VOL_MA20"].tail(100), color="blue", label="VOL_MA20", lw=1.5)
        ax.set_ylabel("成交量", fontsize=10)
        ax.legend(loc="upper left", fontsize=8)
        ax.grid(True, alpha=0.3)
        if v.min() > 0 and v.max() / v.min() > 10:
            ax.set_yscale("log")

    def _plot_a_macd_chart(self, ax, a_data: pd.DataFrame):
        """绘制A股MACD图"""
        if not all(c in a_data.columns for c in ["MACD", "MACD_signal", "MACD_hist"]):
            return
        ax.plot(a_data.index[-100:], a_data["MACD"].tail(100), color="blue", label="MACD", lw=1.5)
        ax.plot(a_data.index[-100:], a_data["MACD_signal"].tail(100), color="red", label="Signal", lw=1.5)
        ax.bar(a_data.index[-100:], a_data["MACD_hist"].tail(100), color=["green" if x >= 0 else "red" for x in a_data["MACD_hist"].tail(100)], alpha=0.5, width=0.8)
        ax.axhline(0, color="black", linestyle="-", lw=0.5)
        ax.set_ylabel("MACD", fontsize=10)
        ax.legend(loc="upper left", fontsize=8)
        ax.grid(True, alpha=0.3)

    def _plot_a_rsi_chart(self, ax, a_data: pd.DataFrame):
        """绘制A股RSI图"""
        if "RSI" not in a_data.columns:
            return
        ax.plot(a_data.index[-100:], a_data["RSI"].tail(100), color="purple", lw=2, label="RSI(14)")
        ax.axhline(70, color="red", linestyle="--", lw=1, label="超买")
        ax.axhline(30, color="green", linestyle="--", lw=1, label="超卖")
        ax.fill_between(a_data.index[-100:], 30, 70, alpha=0.1, color="gray")
        ax.set_ylabel("RSI", fontsize=10)
        ax.set_ylim(0, 100)
        ax.legend(loc="upper left", fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel("日期", fontsize=10)

    def _plot_a_index_chart(self, ax, index_data: pd.DataFrame, a_data: pd.DataFrame):
        """绘制A股指数对比图"""
        ci = index_data.index.intersection(a_data.index)
        if len(ci) == 0:
            return
        ap = a_data.loc[ci, "close"]
        ip = index_data.loc[ci, "close"]
        an = ap / ap.iloc[0] * 100
        inn = ip / ip.iloc[0] * 100
        sym = a_data["symbol"].iloc[0] if "symbol" in a_data.columns else "A"
        index_name = index_data["symbol"].iloc[0] if "symbol" in index_data.columns else "指数"
        ax.plot(ci[-100:], an.tail(100), color=self.colors["a_primary"], label=sym, lw=2)
        ax.plot(ci[-100:], inn.tail(100), color=self.colors["index_color"], label=index_name, lw=2)
        ax.set_title("相对指数表现", fontsize=10)
        ax.set_ylabel("相对表现 (%)", fontsize=9)
        ax.legend(loc="upper left", fontsize=8)
        ax.grid(True, alpha=0.3)

    def _plot_a_indicator_panel(self, ax, a_data: pd.DataFrame):
        """绘制A股指标面板"""
        ax.axis("off")
        latest = a_data.iloc[-1]
        rows = [["价格 (CNY)", f"{latest['close']:.2f}"]]
        if "pct_change" in a_data.columns:
            pct = a_data["pct_change"].iloc[-1]
            tag = "🔴" if pct > 0 else "🟢"
            rows.append(["日涨跌幅", f"{tag} {pct:+.2f}%"])
        if "A_HV_20" in a_data.columns:
            rows.append(["历史波动率", f"{latest['A_HV_20']:.1f}%"])
        if "A_VOL_INDEX" in a_data.columns:
            vi = latest["A_VOL_INDEX"]
            vs = "高" if vi > 70 else "低" if vi < 30 else "中"
            rows.append(["波动率指数", f"{vi:.1f} ({vs})"])
        if "A_MONEY_FLOW" in a_data.columns:
            mf = latest["A_MONEY_FLOW"]
            fs = "流入" if mf > 60 else "流出" if mf < 40 else "平衡"
            rows.append(["资金流向", f"{mf:.1f} ({fs})"])
        if "volume" in a_data.columns:
            vol_ma = a_data["volume"].rolling(20).mean().iloc[-1]
            vr = latest["volume"] / vol_ma if vol_ma and vol_ma > 0 else 1
            vs = "放量" if vr > 1.5 else "缩量" if vr < 0.5 else "正常"
            rows.append(["成交量", f"{vr:.1f}x ({vs})"])
        if rows:
            t = ax.table(cellText=rows, cellLoc="left", loc="center", colWidths=[0.5, 0.5])
            t.auto_set_font_size(False)
            t.set_fontsize(9)
            t.scale(1, 2)
            for i in range(len(rows)):
                t[i, 0].set_facecolor("#F2F3F4")
                t[i, 0].set_text_props(weight="bold")
        ax.set_title("A股特有指标", fontsize=11, fontweight="bold", pad=20)
