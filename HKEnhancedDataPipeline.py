class HKEnhancedDataPipeline:
    """
    港股增强版数据准备流水线
    包含港股特有数据获取、指标计算和可视化
    """
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.market = '港股'
        
        # 初始化各组件
        self.data_system = UnifiedMarketDataSystem(['akshare', 'yfinance'])
        self.hk_calculator = HKMarketIndicatorCalculator()
        self.chart_renderer = MultiMarketChartRenderer()
        self.validator = DataQualityValidator()
        
        self.hk_data = None
        self.index_data = None
        self.comparison_data = {}
        
    def run_complete_analysis(self,
                            start_date: str = '2025-01-01',
                            end_date: str = '2026-01-26',
                            include_index: bool = True,
                            include_comparison: List[str] = None) -> Dict:
        """
        运行完整的港股分析流程
        
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param include_index: 是否包含港股指数
        :param include_comparison: 对比股票列表
        :return: 分析结果字典
        """
        print("="*60)
        print(f"开始港股分析: {self.symbol}")
        print("="*60)
        
        result = {
            'symbol': self.symbol,
            'market': self.market,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # 1. 获取港股数据
            print("1. 获取港股数据...")
            self._fetch_hk_data(start_date, end_date)
            
            # 2. 获取港股指数数据
            if include_index:
                print("2. 获取港股指数数据...")
                self._fetch_hk_index_data(start_date, end_date)
            
            # 3. 获取对比数据
            if include_comparison:
                print("3. 获取对比数据...")
                self._fetch_comparison_data(include_comparison, start_date, end_date)
            
            # 4. 验证数据质量
            print("4. 验证数据质量...")
            quality_report = self._validate_hk_data()
            result['quality_report'] = quality_report
            
            # 5. 计算技术指标
            print("5. 计算港股技术指标...")
            indicators_data = self._calculate_hk_indicators()
            result.update(indicators_data)
            
            # 6. 分析市场特征
            print("6. 分析港股市场特征...")
            market_characteristics = self._analyze_hk_market()
            result['market_characteristics'] = market_characteristics
            
            # 7. 生成港股图表
            print("7. 生成港股分析图表...")
            charts = self._generate_hk_charts()
            result['charts'] = charts
            
            # 8. 准备AI分析数据
            print("8. 准备AI分析数据...")
            ai_data = self._prepare_hk_ai_data(result)
            result['ai_data'] = ai_data
            
            print("\n" + "="*60)
            print("港股分析完成!")
            print(f"数据点数: {len(self.hk_data) if self.hk_data is not None else 0}")
            print(f"数据质量: {quality_report.get('status', 'UNKNOWN')}")
            print(f"生成图表: {len(charts)}张")
            print("="*60)
            
            return result
            
        except Exception as e:
            print(f"港股分析失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _fetch_hk_data(self, start_date: str, end_date: str):
        """获取港股数据"""
        self.hk_data = self.data_system.get_market_data(
            symbol=self.symbol,
            market=self.market,
            start_date=start_date,
            end_date=end_date,
            data_type='daily'
        )
        
        if self.hk_data is None or self.hk_data.empty:
            raise ValueError(f"无法获取港股 {self.symbol} 的数据")
        
        print(f"获取港股数据成功: {len(self.hk_data)} 条记录")
        print(f"日期范围: {self.hk_data.index[0]} 至 {self.hk_data.index[-1]}")
    
    def _fetch_hk_index_data(self, start_date: str, end_date: str):
        """获取港股指数数据"""
        # 获取恒生指数作为基准
        self.index_data = self.data_system.get_hk_index_data(
            index_code='HSI',
            start_date=start_date,
            end_date=end_date
        )
        
        if self.index_data is not None:
            print(f"获取恒生指数数据成功: {len(self.index_data)} 条记录")
    
    def _fetch_comparison_data(self, symbols: List[str], start_date: str, end_date: str):
        """获取对比数据"""
        for symbol in symbols:
            try:
                data = self.data_system.get_market_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    data_type='daily'
                )
                
                if data is not None:
                    self.comparison_data[symbol] = data
                    print(f"获取对比数据 {symbol} 成功")
                    
            except Exception as e:
                print(f"获取对比数据 {symbol} 失败: {e}")
    
    def _validate_hk_data(self) -> Dict:
        """验证港股数据质量"""
        if self.hk_data is None:
            return {'status': 'FAIL', 'message': '没有数据'}
        
        # 基础验证
        base_report = self.validator.validate_ohlcv(self.hk_data)
        
        # 港股特有验证
        hk_report = {
            'status': base_report['status'],
            'completeness': base_report['completeness'],
            'data_points': len(self.hk_data),
            'price_range': {
                'min': float(self.hk_data['low'].min()),
                'max': float(self.hk_data['high'].max()),
                'current': float(self.hk_data['close'].iloc[-1])
            },
            'volume_analysis': {
                'avg_volume': float(self.hk_data['volume'].mean()),
                'max_volume': float(self.hk_data['volume'].max()),
                'recent_volume': float(self.hk_data['volume'].tail(5).mean())
            },
            'hk_specific_checks': self._perform_hk_specific_checks()
        }
        
        return hk_report
    
    def _perform_hk_specific_checks(self) -> Dict:
        """执行港股特有检查"""
        checks = {
            'price_gaps': 0,
            'volume_anomalies': 0,
            'trading_days_check': 'PASS'
        }
        
        if self.hk_data is not None:
            # 检查价格缺口
            price_gaps = abs(self.hk_data['close'].pct_change()) > 0.1  # 10%以上的缺口
            checks['price_gaps'] = int(price_gaps.sum())
            
            # 检查成交量异常
            volume_mean = self.hk_data['volume'].mean()
            volume_std = self.hk_data['volume'].std()
            volume_anomalies = abs(self.hk_data['volume'] - volume_mean) > 3 * volume_std
            checks['volume_anomalies'] = int(volume_anomalies.sum())
            
            # 检查交易日数量（港股每年约250个交易日）
            date_range = (self.hk_data.index[-1] - self.hk_data.index[0]).days
            expected_days = date_range * 250 / 365
            actual_days = len(self.hk_data)
            
            if abs(actual_days - expected_days) / expected_days > 0.2:
                checks['trading_days_check'] = 'WARNING'
        
        return checks
    
    def _calculate_hk_indicators(self) -> Dict:
        """计算港股技术指标"""
        if self.hk_data is None:
            return {}
        
        # 计算港股专用指标
        hk_with_indicators = self.hk_calculator.calculate_hk_indicators(self.hk_data)
        self.hk_data = hk_with_indicators
        
        latest = self.hk_data.iloc[-1]
        
        result = {
            'technical_indicators': {
                'trend_indicators': {
                    'MA10': float(latest.get('MA10', 0)),
                    'MA20': float(latest.get('MA20', 0)),
                    'MA50': float(latest.get('MA50', 0)),
                    'MACD': float(latest.get('MACD', 0)),
                    'MACD_signal': float(latest.get('MACD_signal', 0))
                },
                'momentum_indicators': {
                    'RSI': float(latest.get('RSI', 0)),
                    'RSI_status': 'OVERBOUGHT' if latest.get('RSI', 0) > 70 else 
                                 'OVERSOLD' if latest.get('RSI', 0) < 30 else 'NEUTRAL',
                    'STOCH_K': float(latest.get('STOCH_K', 0)),
                    'STOCH_D': float(latest.get('STOCH_D', 0))
                },
                'hk_specific_indicators': {
                    'HV_20': float(latest.get('HK_HV_20', 0)),
                    'VOL_INDEX': float(latest.get('HK_VOL_INDEX', 0)),
                    'MONEY_FLOW': float(latest.get('HK_MONEY_FLOW', 0))
                }
            },
            'price_data': self._extract_price_history(),
            'volume_analysis': self._analyze_volume_patterns()
        }
        
        return result
    
    def _extract_price_history(self) -> List[Dict]:
        """提取价格历史数据"""
        if self.hk_data is None:
            return []
        
        price_history = []
        for idx, row in self.hk_data.tail(50).iterrows():
            price_history.append({
                'date': idx.strftime('%Y-%m-%d'),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume']),
                'pct_change': float(row.get('pct_change', 0))
            })
        
        return price_history
    
    def _analyze_volume_patterns(self) -> Dict:
        """分析成交量模式"""
        if self.hk_data is None:
            return {}
        
        volume_data = self.hk_data['volume']
        
        analysis = {
            'recent_avg': float(volume_data.tail(20).mean()),
            'historical_avg': float(volume_data.mean()),
            'volume_ratio': float(volume_data.tail(20).mean() / volume_data.mean()),
            'volume_trend': self._determine_volume_trend(volume_data),
            'unusual_volume_days': int((volume_data > volume_data.rolling(20).mean() * 1.5).sum())
        }
        
        return analysis
    
    def _determine_volume_trend(self, volume_series: pd.Series) -> str:
        """判断成交量趋势"""
        recent_mean = volume_series.tail(5).mean()
        prev_mean = volume_series.tail(10).head(5).mean()
        
        if recent_mean > prev_mean * 1.2:
            return 'INCREASING'
        elif recent_mean < prev_mean * 0.8:
            return 'DECREASING'
        else:
            return 'STABLE'
    
    def _analyze_hk_market(self) -> Dict:
        """分析港股市场特征"""
        if self.hk_data is None:
            return {}
        
        return self.hk_calculator.get_hk_market_characteristics(self.hk_data)
    
    def _generate_hk_charts(self) -> Dict:
        """生成港股图表"""
        charts = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # 1. 港股主分析图
            main_chart_path = f"hk_main_chart_{timestamp}.png"
            self.chart_renderer.create_hk_stock_chart(
                hk_data=self.hk_data,
                index_data=self.index_data,
                comparison_data=self.comparison_data,
                save_path=main_chart_path
            )
            charts['main_chart'] = main_chart_path
            
            # 2. 多市场对比图（如果有对比数据）
            if self.comparison_data:
                comparison_chart_path = f"hk_comparison_chart_{timestamp}.png"
                
                # 创建包含港股和对比数据的数据集
                all_market_data = {self.symbol: self.hk_data}
                all_market_data.update(self.comparison_data)
                
                self.chart_renderer.create_multi_market_comparison(
                    market_data=all_market_data,
                    save_path=comparison_chart_path
                )
                charts['comparison_chart'] = comparison_chart_path
            
            # 3. 港股指标趋势图
            indicator_chart_path = f"hk_indicator_chart_{timestamp}.png"
            self._create_hk_indicator_trend_chart(indicator_chart_path)
            charts['indicator_chart'] = indicator_chart_path
            
        except Exception as e:
            print(f"生成图表失败: {e}")
        
        return charts
    
    def _create_hk_indicator_trend_chart(self, save_path: str):
        """创建港股指标趋势图"""
        if self.hk_data is None:
            return
        
        fig, axes = plt.subplots(3, 1, figsize=(15, 10))
        
        # 1. 波动率趋势
        if 'HK_HV_20' in self.hk_data.columns:
            axes[0].plot(self.hk_data.index[-100:], self.hk_data['HK_HV_20'].tail(100),
                       color='orange', linewidth=2)
            axes[0].set_title('港股历史波动率 (20日)', fontsize=12)
            axes[0].set_ylabel('波动率 (%)', fontsize=10)
            axes[0].grid(True, alpha=0.3)
        
        # 2. 资金流向趋势
        if 'HK_MONEY_FLOW' in self.hk_data.columns:
            axes[1].plot(self.hk_data.index[-100:], self.hk_data['HK_MONEY_FLOW'].tail(100),
                       color='blue', linewidth=2)
            axes[1].axhline(y=50, color='gray', linestyle='--', alpha=0.5)
            axes[1].set_title('港股资金流向指标', fontsize=12)
            axes[1].set_ylabel('资金流向 (%)', fontsize=10)
            axes[1].set_ylim(0, 100)
            axes[1].grid(True, alpha=0.3)
        
        # 3. 成交量与价格对比
        if 'close' in self.hk_data.columns and 'volume' in self.hk_data.columns:
            ax2 = axes[2].twinx()
            
            # 价格
            axes[2].plot(self.hk_data.index[-100:], self.hk_data['close'].tail(100),
                        color='green', linewidth=2, label='价格')
            axes[2].set_ylabel('价格 (HKD)', fontsize=10, color='green')
            axes[2].tick_params(axis='y', labelcolor='green')
            
            # 成交量
            volume_normalized = self.hk_data['volume'].tail(100) / self.hk_data['volume'].tail(100).max() * 100
            ax2.bar(self.hk_data.index[-100:], volume_normalized,
                   alpha=0.3, color='gray', label='成交量')
            ax2.set_ylabel('成交量 (%)', fontsize=10, color='gray')
            ax2.tick_params(axis='y', labelcolor='gray')
            
            axes[2].set_title('港股价格与成交量对比', fontsize=12)
            axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _prepare_hk_ai_data(self, analysis_result: Dict) -> Dict:
        """准备港股AI分析数据"""
        ai_data = {
            'metadata': {
                'symbol': self.symbol,
                'market': self.market,
                'analysis_date': analysis_result['analysis_time'],
                'data_points': len(self.hk_data) if self.hk_data is not None else 0
            },
            'current_status': {
                'price': analysis_result.get('market_characteristics', {}).get('price_range', {}).get('current', 0),
                'volume': analysis_result.get('volume_analysis', {}).get('recent_avg', 0),
                'market_trend': self._determine_market_trend()
            },
            'technical_signals': analysis_result.get('technical_indicators', {}),
            'hk_specific_analysis': {
                'volatility': analysis_result.get('market_characteristics', {}).get('volatility', {}),
                'liquidity': analysis_result.get('market_characteristics', {}).get('liquidity', {}),
                'hk_indicators': analysis_result.get('technical_indicators', {}).get('hk_specific_indicators', {})
            },
            'comparison_data': self._prepare_comparison_summary()
        }
        
        # 保存为JSON
        json_path = f"hk_ai_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(ai_data, f, ensure_ascii=False, indent=2)
        
        ai_data['json_path'] = json_path
        return ai_data
    
    def _determine_market_trend(self) -> str:
        """判断市场趋势"""
        if self.hk_data is None or len(self.hk_data) < 20:
            return 'UNKNOWN'
        
        # 使用多个指标判断趋势
        close_prices = self.hk_data['close']
        
        # 短期趋势（5日）
        short_trend = 'UP' if close_prices.iloc[-1] > close_prices.iloc[-5] else 'DOWN'
        
        # 中期趋势（20日）
        ma20 = close_prices.rolling(20).mean()
        mid_trend = 'UP' if close_prices.iloc[-1] > ma20.iloc[-1] else 'DOWN'
        
        # 综合判断
        if short_trend == 'UP' and mid_trend == 'UP':
            return 'STRONG_UP'
        elif short_trend == 'DOWN' and mid_trend == 'DOWN':
            return 'STRONG_DOWN'
        elif short_trend == 'UP':
            return 'UP'
        elif short_trend == 'DOWN':
            return 'DOWN'
        else:
            return 'SIDEWAYS'
    
    def _prepare_comparison_summary(self) -> Dict:
        """准备对比数据摘要"""
        summary = {}
        
        for symbol, data in self.comparison_data.items():
            if data is not None and not data.empty:
                latest = data.iloc[-1]
                summary[symbol] = {
                    'price': float(latest['close']),
                    'pct_change': float(data['close'].pct_change().iloc[-1] * 100),
                    'volume': float(latest['volume'])
                }
        
        return summary