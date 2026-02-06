"""
图表生成器 - 生成K线图和技术指标图表（根据模板要求）
"""
import os
from datetime import datetime
from typing import Optional
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

try:
    import mplfinance as mpf
    MPLFINANCE_AVAILABLE = True
except ImportError:
    MPLFINANCE_AVAILABLE = False


class ChartGenerator:
    """图表生成器（符合模板要求）"""
    
    def __init__(self):
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 颜色配置（支持黑白打印）
        self.colors = {
            'up': '#00C853',      # 阳线：绿色
            'down': '#D32F2F',    # 阴线：红色
            'ma5': '#2196F3',     # MA5：蓝色
            'ma20': '#FF9800',    # MA20：橙色
            'ma60': '#9C27B0',    # MA60：紫色
            'macd': '#1976D2',    # MACD线：蓝色
            'signal': '#F44336',  # Signal线：红色
            'rsi': '#7B1FA2',     # RSI：紫色
        }
    
    def generate_kline_chart(
        self,
        data: pd.DataFrame,
        symbol: str,
        market: str,
        save_path: str = "kline_chart.png",
        days: int = 20
    ) -> str:
        """
        生成K线图和技术指标图表（根据模板要求）
        
        Args:
            data: 股票数据DataFrame
            symbol: 股票代码
            market: 市场类型
            save_path: 保存路径
            days: 显示最近N个交易日（默认20）
        
        Returns:
            图表文件路径
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        
        # 获取最近N个交易日的数据
        plot_data = data.tail(days).copy()
        
        if plot_data.empty:
            raise ValueError("数据为空，无法生成图表")
        
        # 计算分辨率：1920×1080
        dpi = 100
        fig_width = 1920 / dpi  # 19.2英寸
        fig_height = 1080 / dpi  # 10.8英寸
        
        # 创建图表（主图+副图1+副图2）
        fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi)
        gs = gridspec.GridSpec(3, 1, figure=fig, height_ratios=[3, 1, 1], hspace=0.35, top=0.95, bottom=0.08)
        
        # 1. 主图：K线图 + 移动平均线
        ax1 = fig.add_subplot(gs[0])
        self._plot_kline_enhanced(ax1, plot_data, symbol, market, days)
        
        # 2. 副图1：MACD指标
        ax2 = fig.add_subplot(gs[1], sharex=ax1)
        self._plot_macd_enhanced(ax2, plot_data)
        
        # 3. 副图2：RSI指标
        ax3 = fig.add_subplot(gs[2], sharex=ax1)
        self._plot_rsi_enhanced(ax3, plot_data)
        
        # 设置总标题
        start_date = plot_data.index[0].strftime('%Y-%m-%d')
        end_date = plot_data.index[-1].strftime('%Y-%m-%d')
        title = f"{market} {symbol} - K线图与技术指标\n数据范围: {start_date} 至 {end_date} ({days}个交易日)"
        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
        
        # 添加数据来源和时间戳
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        fig.text(0.99, 0.02, f"数据来源: 模拟数据 | 生成时间: {timestamp}", 
                ha='right', va='bottom', fontsize=8, style='italic', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=dpi, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"✅ K线图已生成: {save_path} (分辨率: 1920×1080)")
        return save_path
    
    def _plot_kline_enhanced(self, ax, data: pd.DataFrame, symbol: str, market: str, days: int):
        """绘制增强版K线图（包含关键价格点和支撑/阻力位）"""
        n = len(data)
        x_positions = np.arange(n)
        
        opens = data['open'].values
        highs = data['high'].values
        lows = data['low'].values
        closes = data['close'].values
        
        # 绘制K线（阳线绿色，阴线红色）
        for i in range(n):
            is_up = closes[i] >= opens[i]
            color = self.colors['up'] if is_up else self.colors['down']
            
            # 实体（矩形）
            body_height = abs(closes[i] - opens[i])
            body_bottom = min(opens[i], closes[i])
            if body_height > 0:
                ax.bar(i, body_height, bottom=body_bottom, 
                       color=color, alpha=0.8, width=0.6, edgecolor='black', linewidth=0.5)
            else:
                # 十字星
                ax.plot([i-0.3, i+0.3], [opens[i], closes[i]], 
                       color=color, linewidth=2)
            
            # 上影线
            top = max(opens[i], closes[i])
            if highs[i] > top:
                ax.plot([i, i], [top, highs[i]], color=color, linewidth=1.5, alpha=0.8)
            
            # 下影线
            bottom = min(opens[i], closes[i])
            if lows[i] < bottom:
                ax.plot([i, i], [bottom, lows[i]], color=color, linewidth=1.5, alpha=0.8)
        
        # 绘制移动平均线
        if 'MA5' in data.columns:
            ma5_values = data['MA5'].dropna().values
            if len(ma5_values) > 0:
                ma5_indices = np.arange(n - len(ma5_values), n)
                ax.plot(ma5_indices, ma5_values, 
                       label='MA5', color=self.colors['ma5'], linewidth=2, alpha=0.8)
        
        if 'MA20' in data.columns:
            ma20_values = data['MA20'].dropna().values
            if len(ma20_values) > 0:
                ma20_indices = np.arange(n - len(ma20_values), n)
                ax.plot(ma20_indices, ma20_values, 
                       label='MA20', color=self.colors['ma20'], linewidth=2, alpha=0.8)
        
        if 'MA60' in data.columns:
            ma60_values = data['MA60'].dropna().values
            if len(ma60_values) > 0:
                ma60_indices = np.arange(n - len(ma60_values), n)
                ax.plot(ma60_indices, ma60_values, 
                       label='MA60', color=self.colors['ma60'], linewidth=2, alpha=0.8)
        
        # 标注关键价格点
        recent_high = highs.max()
        recent_low = lows.min()
        high_idx = np.argmax(highs)
        low_idx = np.argmin(lows)
        
        # 标注最高价
        ax.annotate(f'最高: {recent_high:.2f}', 
                   xy=(high_idx, recent_high), 
                   xytext=(high_idx, recent_high + (highs.max() - lows.min()) * 0.05),
                   arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
                   fontsize=9, ha='center', bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
        
        # 标注最低价
        ax.annotate(f'最低: {recent_low:.2f}', 
                   xy=(low_idx, recent_low), 
                   xytext=(low_idx, recent_low - (highs.max() - lows.min()) * 0.05),
                   arrowprops=dict(arrowstyle='->', color='green', lw=1.5),
                   fontsize=9, ha='center', bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.7))
        
        # 计算并显示支撑位/阻力位（基于最近20日数据）
        support_level = lows.min()
        resistance_level = highs.max()
        
        # 绘制支撑位线
        ax.axhline(support_level, color='green', linestyle='--', linewidth=1.5, alpha=0.6, label=f'支撑位: {support_level:.2f}')
        
        # 绘制阻力位线
        ax.axhline(resistance_level, color='red', linestyle='--', linewidth=1.5, alpha=0.6, label=f'阻力位: {resistance_level:.2f}')
        
        # 设置标题和标签
        ax.set_title(f"{market} {symbol} - K线图与移动平均线", fontsize=14, fontweight='bold', pad=15)
        ax.set_ylabel('价格', fontsize=11, fontweight='bold')
        ax.set_xlabel('交易日', fontsize=11, fontweight='bold')
        
        # 设置坐标轴范围
        price_min = min(lows.min(), support_level)
        price_max = max(highs.max(), resistance_level)
        price_range = price_max - price_min
        ax.set_ylim(price_min - price_range * 0.1, price_max + price_range * 0.1)
        ax.set_xlim(-0.5, n - 0.5)
        
        # 图例
        ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # 设置x轴标签
        step = max(1, n // 10)
        tick_positions = list(range(0, n, step))
        if tick_positions[-1] != n - 1:
            tick_positions.append(n - 1)
        ax.set_xticks(tick_positions)
        ax.set_xticklabels([data.index[i].strftime('%m-%d') for i in tick_positions], 
                          rotation=45, fontsize=9, ha='right')
    
    def _plot_macd_enhanced(self, ax, data: pd.DataFrame):
        """绘制增强版MACD指标"""
        n = len(data)
        x_positions = np.arange(n)
        
        if 'MACD' in data.columns and 'MACD_signal' in data.columns:
            macd_values = data['MACD'].dropna().values
            signal_values = data['MACD_signal'].dropna().values
            
            if len(macd_values) > 0:
                macd_indices = np.arange(n - len(macd_values), n)
                ax.plot(macd_indices, macd_values, 
                       label='DIF线', color=self.colors['macd'], linewidth=2)
            
            if len(signal_values) > 0:
                signal_indices = np.arange(n - len(signal_values), n)
                ax.plot(signal_indices, signal_values, 
                       label='DEA线', color=self.colors['signal'], linewidth=2)
            
            if 'MACD_hist' in data.columns:
                hist_values = data['MACD_hist'].dropna().values
                if len(hist_values) > 0:
                    hist_indices = np.arange(n - len(hist_values), n)
                    colors_hist = [self.colors['up'] if x >= 0 else self.colors['down'] for x in hist_values]
                    ax.bar(hist_indices, hist_values, 
                          color=colors_hist, alpha=0.4, width=0.6, label='MACD柱')
        else:
            # 计算MACD
            macd_data = self._calculate_macd(data)
            if macd_data is not None and len(macd_data) > 0:
                macd_indices = np.arange(n - len(macd_data), n)
                ax.plot(macd_indices, macd_data['MACD'], 
                       label='DIF线', color=self.colors['macd'], linewidth=2)
                ax.plot(macd_indices, macd_data['Signal'], 
                       label='DEA线', color=self.colors['signal'], linewidth=2)
        
        ax.axhline(0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
        ax.set_title('MACD指标', fontsize=12, fontweight='bold', pad=10)
        ax.set_ylabel('MACD', fontsize=10, fontweight='bold')
        ax.set_xlim(-0.5, n - 0.5)
        ax.legend(loc='upper left', fontsize=9)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # 设置x轴标签
        step = max(1, n // 10)
        tick_positions = list(range(0, n, step))
        if tick_positions[-1] != n - 1:
            tick_positions.append(n - 1)
        ax.set_xticks(tick_positions)
        ax.set_xticklabels([data.index[i].strftime('%m-%d') for i in tick_positions], 
                          rotation=45, fontsize=9, ha='right')
    
    def _plot_rsi_enhanced(self, ax, data: pd.DataFrame):
        """绘制增强版RSI指标"""
        n = len(data)
        x_positions = np.arange(n)
        
        if 'RSI' in data.columns:
            rsi_values = data['RSI'].dropna().values
            if len(rsi_values) > 0:
                rsi_indices = np.arange(n - len(rsi_values), n)
                ax.plot(rsi_indices, rsi_values, 
                       label='RSI(14)', color=self.colors['rsi'], linewidth=2)
        else:
            # 计算RSI
            rsi = self._calculate_rsi(data)
            if rsi is not None and len(rsi) > 0:
                rsi_indices = np.arange(n - len(rsi), n)
                ax.plot(rsi_indices, rsi, label='RSI(14)', color=self.colors['rsi'], linewidth=2)
        
        # 超买超卖线
        ax.axhline(70, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='超买线(70)')
        ax.axhline(30, color='green', linestyle='--', linewidth=1.5, alpha=0.7, label='超卖线(30)')
        ax.axhline(50, color='gray', linestyle=':', linewidth=1, alpha=0.5)
        
        # 填充超买超卖区域
        ax.fill_between([0, n], 70, 100, alpha=0.1, color='red')
        ax.fill_between([0, n], 0, 30, alpha=0.1, color='green')
        
        ax.set_ylim(0, 100)
        ax.set_xlim(-0.5, n - 0.5)
        ax.set_title('RSI指标', fontsize=12, fontweight='bold', pad=10)
        ax.set_ylabel('RSI', fontsize=10, fontweight='bold')
        ax.set_xlabel('交易日', fontsize=10, fontweight='bold')
        ax.legend(loc='upper left', fontsize=9)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # 设置x轴标签
        step = max(1, n // 10)
        tick_positions = list(range(0, n, step))
        if tick_positions[-1] != n - 1:
            tick_positions.append(n - 1)
        ax.set_xticks(tick_positions)
        ax.set_xticklabels([data.index[i].strftime('%m-%d') for i in tick_positions], 
                          rotation=45, fontsize=9, ha='right')
    
    def _calculate_macd(self, data: pd.DataFrame, fast=12, slow=26, signal=9):
        """计算MACD指标"""
        try:
            ema_fast = data['close'].ewm(span=fast).mean()
            ema_slow = data['close'].ewm(span=slow).mean()
            macd = ema_fast - ema_slow
            signal_line = macd.ewm(span=signal).mean()
            hist = macd - signal_line
            
            return pd.DataFrame({
                'MACD': macd.values,
                'Signal': signal_line.values,
                'MACD_hist': hist.values
            })
        except Exception:
            return None
    
    def _calculate_rsi(self, data: pd.DataFrame, period=14):
        """计算RSI指标"""
        try:
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.values
        except Exception:
            return None
    
    def generate_indicators_chart(
        self,
        data: pd.DataFrame,
        symbol: str,
        market: str,
        save_path: str = "indicators_chart.png"
    ) -> str:
        """
        生成技术指标趋势图
        
        Args:
            data: 股票数据DataFrame
            symbol: 股票代码
            market: 市场类型
            save_path: 保存路径
        
        Returns:
            图表文件路径
        """
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        
        plot_data = data.tail(100).copy()
        
        fig, axes = plt.subplots(3, 1, figsize=(14, 10))
        
        # 1. 均线系统
        ax1 = axes[0]
        ax1.plot(plot_data.index, plot_data['close'].values, label='收盘价', color='black', linewidth=2)
        if 'MA5' in data.columns:
            ax1.plot(plot_data.index, plot_data['MA5'].values, label='MA5', color=self.colors['ma5'], linewidth=1.5)
        if 'MA20' in data.columns:
            ax1.plot(plot_data.index, plot_data['MA20'].values, label='MA20', color=self.colors['ma20'], linewidth=1.5)
        if 'MA60' in data.columns:
            ax1.plot(plot_data.index, plot_data['MA60'].values, label='MA60', color=self.colors['ma60'], linewidth=1.5)
        ax1.set_title('均线系统', fontsize=12, fontweight='bold')
        ax1.set_ylabel('价格', fontsize=10)
        ax1.legend(loc='upper left', fontsize=9)
        ax1.grid(True, alpha=0.3)
        
        # 2. RSI
        ax2 = axes[1]
        if 'RSI' in data.columns:
            ax2.plot(plot_data.index, plot_data['RSI'].values, label='RSI(14)', color=self.colors['rsi'], linewidth=2)
        ax2.axhline(70, color='red', linestyle='--', linewidth=1, alpha=0.7)
        ax2.axhline(30, color='green', linestyle='--', linewidth=1, alpha=0.7)
        ax2.set_ylim(0, 100)
        ax2.set_title('RSI相对强弱指标', fontsize=12, fontweight='bold')
        ax2.set_ylabel('RSI', fontsize=10)
        ax2.legend(loc='upper left', fontsize=9)
        ax2.grid(True, alpha=0.3)
        
        # 3. 波动率
        ax3 = axes[2]
        if 'pct_change' in data.columns:
            ax3.plot(plot_data.index, plot_data['pct_change'].values, 
                    label='涨跌幅', color=self.colors['macd'], linewidth=1.5, alpha=0.7)
            ax3.axhline(0, color='black', linestyle='-', linewidth=0.5, alpha=0.5)
        ax3.set_title('价格波动率', fontsize=12, fontweight='bold')
        ax3.set_ylabel('涨跌幅 (%)', fontsize=10)
        ax3.set_xlabel('日期', fontsize=10)
        ax3.legend(loc='upper left', fontsize=9)
        ax3.grid(True, alpha=0.3)
        
        plt.suptitle(f"{market} {symbol} - 技术指标分析", fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 技术指标图已生成: {save_path}")
        return save_path
