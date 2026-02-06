class MultiMarketChartRenderer:
    """
    多市场图表渲染器
    支持A股、港股等不同市场的可视化需求
    """
    
    def __init__(self):
        self.colors = {
            'hk_primary': '#E74C3C',     # 港股主色（红色）
            'hk_secondary': '#C0392B',   # 港股辅助色
            'a_primary': '#2E86AB',      # A股主色（蓝色）
            'a_secondary': '#1A5276',    # A股辅助色
            'us_primary': '#27AE60',     # 美股主色（绿色）
            'index_color': '#8E44AD'     # 指数颜色
        }
        
        self.market_styles = {
            '港股': {
                'candle_up': '#E74C3C',  # 上涨颜色
                'candle_down': '#27AE60', # 下跌颜色
                'ma_colors': ['#FF6B6B', '#FF8E53', '#FFAA64', '#FFC785']
            },
            'A股': {
                'candle_up': '#E74C3C',
                'candle_down': '#27AE60',
                'ma_colors': ['#2E86AB', '#45B7D1', '#73C6B6', '#95A5A6']
            },
            '美股': {
                'candle_up': '#27AE60',
                'candle_down': '#E74C3C',
                'ma_colors': ['#27AE60', '#2ECC71', '#58D68D', '#82E0AA']
            }
        }
    
    def create_hk_stock_chart(self, 
                            hk_data: pd.DataFrame,
                            index_data: pd.DataFrame = None,
                            comparison_data: Dict = None,
                            save_path: str = 'hk_chart.png') -> plt.Figure:
        """
        创建港股专业分析图表
        
        :param hk_data: 港股数据
        :param index_data: 港股指数数据（如恒生指数）
        :param comparison_data: 对比数据（如A股对标股票）
        :param save_path: 保存路径
        :return: Matplotlib Figure对象
        """
        fig = plt.figure(figsize=(18, 12))
        
        # 创建网格布局
        gs = gridspec.GridSpec(4, 3, figure=fig, 
                              height_ratios=[3, 1, 1, 1],
                              width_ratios=[3, 1, 1])
        
        # 1. 港股主图（K线 + 指标）
        ax_main = fig.add_subplot(gs[0, 0])
        self._plot_hk_main_chart(ax_main, hk_data)
        
        # 2. 港股成交量
        ax_volume = fig.add_subplot(gs[1, 0], sharex=ax_main)
        self._plot_hk_volume_chart(ax_volume, hk_data)
        
        # 3. 港股技术指标（MACD）
        ax_macd = fig.add_subplot(gs[2, 0], sharex=ax_main)
        self._plot_hk_macd_chart(ax_macd, hk_data)
        
        # 4. 港股技术指标（RSI）
        ax_rsi = fig.add_subplot(gs[3, 0], sharex=ax_main)
        self._plot_hk_rsi_chart(ax_rsi, hk_data)
        
        # 5. 港股指数对比（如果有）
        if index_data is not None:
            ax_index = fig.add_subplot(gs[0, 1])
            self._plot_hk_index_chart(ax_index, index_data, hk_data)
        
        # 6. 港股特有指标面板
        ax_hk_panel = fig.add_subplot(gs[0, 2])
        self._plot_hk_indicator_panel(ax_hk_panel, hk_data)
        
        # 7. 多市场对比（如果有）
        if comparison_data:
            ax_comparison = fig.add_subplot(gs[1:, 1:])
            self._plot_market_comparison(ax_comparison, hk_data, comparison_data)
        
        plt.suptitle(f"港股技术分析 - {hk_data['symbol'].iloc[0]}", fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def _plot_hk_main_chart(self, ax, hk_data: pd.DataFrame):
        """绘制港股主图"""
        # 使用港股特有的颜色方案
        style = self.market_styles.get('港股', self.market_styles['A股'])
        
        # 绘制K线图
        mpf.plot(hk_data.tail(100), type='candle', ax=ax, style='yahoo')
        
        # 添加均线（港股常用均线）
        if 'MA10' in hk_data.columns:
            ax.plot(hk_data.index[-100:], hk_data['MA10'].tail(100), 
                   color=style['ma_colors'][0], label='MA10', linewidth=1.5)
        if 'MA20' in hk_data.columns:
            ax.plot(hk_data.index[-100:], hk_data['MA20'].tail(100), 
                   color=style['ma_colors'][1], label='MA20', linewidth=1.5)
        if 'MA50' in hk_data.columns:
            ax.plot(hk_data.index[-100:], hk_data['MA50'].tail(100), 
                   color=style['ma_colors'][2], label='MA50', linewidth=1.5)
        
        # 布林带
        if all(col in hk_data.columns for col in ['BB_upper', 'BB_lower']):
            ax.fill_between(hk_data.index[-100:], 
                          hk_data['BB_upper'].tail(100), 
                          hk_data['BB_lower'].tail(100),
                          alpha=0.2, color='gray', label='Bollinger Bands')
        
        ax.set_title('港股价格走势', fontsize=12, fontweight='bold')
        ax.set_ylabel('价格 (HKD)', fontsize=10)
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        # 添加港股特有标注
        current_price = hk_data['close'].iloc[-1]
        ax.annotate(f'当前: {current_price:.2f} HKD', 
                   xy=(0.02, 0.95), xycoords='axes fraction',
                   fontsize=9, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    def _plot_hk_volume_chart(self, ax, hk_data: pd.DataFrame):
        """绘制港股成交量图"""
        # 港股成交量通常较大，使用对数坐标
        volume_data = hk_data['volume'].tail(100)
        
        # 成交量颜色（涨红跌绿）
        colors = ['red' if close >= open_ else 'green' 
                 for close, open_ in zip(hk_data['close'].tail(100), 
                                        hk_data['open'].tail(100))]
        
        ax.bar(hk_data.index[-100:], volume_data, color=colors, alpha=0.7, width=0.8)
        
        # 添加成交量均线
        if 'VOL_MA20' in hk_data.columns:
            ax.plot(hk_data.index[-100:], hk_data['VOL_MA20'].tail(100), 
                   color='blue', label='VOL_MA20', linewidth=1.5)
        
        ax.set_ylabel('成交量', fontsize=10)
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        # 使用对数坐标（如果成交量变化大）
        if volume_data.max() / volume_data.min() > 10:
            ax.set_yscale('log')
    
    def _plot_hk_macd_chart(self, ax, hk_data: pd.DataFrame):
        """绘制港股MACD图"""
        if all(col in hk_data.columns for col in ['MACD', 'MACD_signal', 'MACD_hist']):
            ax.plot(hk_data.index[-100:], hk_data['MACD'].tail(100), 
                   color='blue', label='MACD', linewidth=1.5)
            ax.plot(hk_data.index[-100:], hk_data['MACD_signal'].tail(100), 
                   color='red', label='Signal', linewidth=1.5)
            
            # MACD柱状图
            ax.bar(hk_data.index[-100:], hk_data['MACD_hist'].tail(100),
                  color=['green' if x >= 0 else 'red' 
                         for x in hk_data['MACD_hist'].tail(100)],
                  alpha=0.5, width=0.8)
            
            ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax.set_ylabel('MACD', fontsize=10)
            ax.legend(loc='upper left', fontsize=8)
            ax.grid(True, alpha=0.3)
    
    def _plot_hk_rsi_chart(self, ax, hk_data: pd.DataFrame):
        """绘制港股RSI图"""
        if 'RSI' in hk_data.columns:
            ax.plot(hk_data.index[-100:], hk_data['RSI'].tail(100), 
                   color='purple', linewidth=2, label='RSI(14)')
            
            ax.axhline(y=70, color='red', linestyle='--', linewidth=1, label='超买')
            ax.axhline(y=30, color='green', linestyle='--', linewidth=1, label='超卖')
            ax.fill_between(hk_data.index[-100:], 30, 70, alpha=0.1, color='gray')
            
            ax.set_ylabel('RSI', fontsize=10)
            ax.set_ylim(0, 100)
            ax.legend(loc='upper left', fontsize=8)
            ax.grid(True, alpha=0.3)
            ax.set_xlabel('日期', fontsize=10)
    
    def _plot_hk_index_chart(self, ax, index_data: pd.DataFrame, hk_data: pd.DataFrame):
        """绘制港股指数对比图"""
        # 对齐时间索引
        common_index = index_data.index.intersection(hk_data.index)
        
        if len(common_index) > 0:
            # 计算相对表现
            hk_price = hk_data.loc[common_index, 'close']
            index_price = index_data.loc[common_index, 'close']
            
            # 归一化（从100开始）
            hk_normalized = hk_price / hk_price.iloc[0] * 100
            index_normalized = index_price / index_price.iloc[0] * 100
            
            ax.plot(common_index[-100:], hk_normalized.tail(100), 
                   color=self.colors['hk_primary'], label=hk_data['symbol'].iloc[0], linewidth=2)
            ax.plot(common_index[-100:], index_normalized.tail(100), 
                   color=self.colors['index_color'], label='恒生指数', linewidth=2)
            
            ax.set_title('相对恒生指数表现', fontsize=10)
            ax.set_ylabel('相对表现 (%)', fontsize=9)
            ax.legend(loc='upper left', fontsize=8)
            ax.grid(True, alpha=0.3)
    
    def _plot_hk_indicator_panel(self, ax, hk_data: pd.DataFrame):
        """绘制港股特有指标面板"""
        ax.axis('off')
        
        latest = hk_data.iloc[-1]
        
        # 港股特有指标
        indicator_data = []
        
        # 基础指标
        indicator_data.append(["价格 (HKD)", f"{latest['close']:.2f}"])
        
        if 'pct_change' in hk_data.columns:
            pct_change = hk_data['pct_change'].iloc[-1]
            color_tag = "🔴" if pct_change > 0 else "🟢"
            indicator_data.append(["日涨跌幅", f"{color_tag} {pct_change:+.2f}%"])
        
        # 港股特有指标
        if 'HK_HV_20' in hk_data.columns:
            indicator_data.append(["历史波动率", f"{latest['HK_HV_20']:.1f}%"])
        
        if 'HK_VOL_INDEX' in hk_data.columns:
            vol_index = latest['HK_VOL_INDEX']
            vol_status = "高" if vol_index > 70 else "低" if vol_index < 30 else "中"
            indicator_data.append(["波动率指数", f"{vol_index:.1f} ({vol_status})"])
        
        if 'HK_MONEY_FLOW' in hk_data.columns:
            money_flow = latest['HK_MONEY_FLOW']
            flow_status = "流入" if money_flow > 60 else "流出" if money_flow < 40 else "平衡"
            indicator_data.append(["资金流向", f"{money_flow:.1f} ({flow_status})"])
        
        # 成交量相关
        if 'volume' in hk_data.columns:
            volume_ratio = latest['volume'] / hk_data['volume'].rolling(20).mean().iloc[-1]
            volume_status = "放量" if volume_ratio > 1.5 else "缩量" if volume_ratio < 0.5 else "正常"
            indicator_data.append(["成交量", f"{volume_ratio:.1f}x ({volume_status})"])
        
        # 创建表格
        if indicator_data:
            table = ax.table(cellText=indicator_data,
                           cellLoc='left',
                           loc='center',
                           colWidths=[0.5, 0.5])
            
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 2)
            
            # 设置样式
            for i in range(len(indicator_data)):
                cell = table[i, 0]
                cell.set_facecolor('#F2F3F4')
                cell.set_text_props(weight='bold')
        
        ax.set_title('港股特有指标', fontsize=11, fontweight='bold', pad=20)
    
    def create_multi_market_comparison(self, 
                                     market_data: Dict[str, pd.DataFrame],
                                     save_path: str = 'market_comparison.png') -> plt.Figure:
        """
        创建多市场对比图
        
        :param market_data: 字典 {市场标签: DataFrame}
        :param save_path: 保存路径
        :return: Matplotlib Figure对象
        """
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. 价格走势对比（归一化）
        ax1 = axes[0, 0]
        self._plot_price_comparison(ax1, market_data)
        
        # 2. 波动率对比
        ax2 = axes[0, 1]
        self._plot_volatility_comparison(ax2, market_data)
        
        # 3. 相关性分析
        ax3 = axes[1, 0]
        self._plot_correlation_analysis(ax3, market_data)
        
        # 4. 相对强度指标
        ax4 = axes[1, 1]
        self._plot_relative_strength(ax4, market_data)
        
        plt.suptitle('多市场对比分析', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def _plot_price_comparison(self, ax, market_data: Dict):
        """绘制价格走势对比"""
        for label, data in market_data.items():
            if data is not None and 'close' in data.columns:
                # 归一化到100
                normalized = data['close'] / data['close'].iloc[0] * 100
                ax.plot(data.index, normalized, label=label, linewidth=2)
        
        ax.set_title('价格走势对比 (归一化)', fontsize=12)
        ax.set_ylabel('相对价格 (%)', fontsize=10)
        ax.legend(loc='upper left', fontsize=9)
        ax.grid(True, alpha=0.3)