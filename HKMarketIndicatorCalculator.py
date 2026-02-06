class HKMarketIndicatorCalculator:
    """
    港股市场技术指标计算器
    包含港股特有指标和调整
    """
    
    def __init__(self):
        # 港股特有参数
        self.hk_specific_params = {
            'trading_days_per_year': 250,  # 港股年交易日
            'market_hours': {
                'pre_market': '09:00-09:30',
                'main_session': '09:30-12:00,13:00-16:00',
                'post_market': '16:00-17:00'
            }
        }
    
    def calculate_hk_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算港股专用技术指标
        
        :param data: 港股数据
        :return: 包含港股指标的数据
        """
        df = data.copy()
        
        # 基础技术指标（与A股共享）
        base_calculator = TechnicalIndicatorCalculator(df)
        df = base_calculator.calculate_all_indicators()
        
        # 港股特有指标
        df = self._add_hk_specific_indicators(df)
        
        return df
    
    def _add_hk_specific_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加港股特有指标"""
        
        # 1. 港股波动率指标（考虑港股波动特点）
        if 'close' in df.columns:
            returns = df['close'].pct_change()
            
            # 港股历史波动率（年化）
            df['HK_HV_20'] = returns.rolling(20).std() * np.sqrt(self.hk_specific_params['trading_days_per_year'])
            df['HK_HV_60'] = returns.rolling(60).std() * np.sqrt(self.hk_specific_params['trading_days_per_year'])
            
            # 港股波动率指数（模拟）
            df['HK_VOL_INDEX'] = self._calculate_hk_volatility_index(returns)
        
        # 2. 港股资金流向指标
        if all(col in df.columns for col in ['close', 'volume', 'amount']):
            # 港股资金净流入（简化版）
            df['HK_MONEY_FLOW'] = self._calculate_hk_money_flow(df)
            
            # 港股大单成交比例
            df['HK_BLOCK_TRADE_RATIO'] = self._estimate_block_trade_ratio(df)
        
        # 3. 港股与A股关联指标（如果是A+H股）
        df['HK_A_PREMIUM'] = np.nan  # A+H溢价率（需要A股数据对比）
        
        # 4. 港股通资金流向（需要额外数据）
        df['HK_CONNECT_NORTH'] = np.nan  # 北向资金
        df['HK_CONNECT_SOUTH'] = np.nan  # 南向资金
        
        return df
    
    def _calculate_hk_volatility_index(self, returns: pd.Series) -> pd.Series:
        """计算港股波动率指数（模拟）"""
        # 基于历史波动率的波动率指数
        hv_20 = returns.rolling(20).std() * np.sqrt(250)
        hv_60 = returns.rolling(60).std() * np.sqrt(250)
        
        # 加权平均
        vol_index = 0.7 * hv_20 + 0.3 * hv_60
        
        # 归一化到0-100范围
        if vol_index.max() > 0:
            vol_index = (vol_index / vol_index.rolling(100).max()) * 100
        
        return vol_index
    
    def _calculate_hk_money_flow(self, df: pd.DataFrame) -> pd.Series:
        """计算港股资金流向（简化版）"""
        # 基于价格和成交量的资金流向计算
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        money_flow = typical_price * df['volume']
        
        # 资金流正负判断
        money_flow_positive = money_flow.copy()
        money_flow_negative = money_flow.copy()
        
        # 价格上涨为正资金流，反之为负
        price_change = df['close'].diff()
        money_flow_positive[price_change <= 0] = 0
        money_flow_negative[price_change > 0] = 0
        
        # 资金流比率
        money_flow_ratio = money_flow_positive.rolling(20).sum() / (
            money_flow_positive.rolling(20).sum() + money_flow_negative.rolling(20).sum()
        )
        
        return money_flow_ratio.fillna(0.5) * 100  # 0-100范围
    
    def _estimate_block_trade_ratio(self, df: pd.DataFrame) -> pd.Series:
        """估计大单成交比例（基于异常成交量）"""
        # 计算成交量异常值
        volume_ma = df['volume'].rolling(20).mean()
        volume_std = df['volume'].rolling(20).std()
        
        # 大单定义为超过2倍标准差的成交量
        block_trade_threshold = volume_ma + 2 * volume_std
        block_trade_volume = df['volume'].copy()
        block_trade_volume[df['volume'] < block_trade_threshold] = 0
        
        # 大单比例
        block_trade_ratio = block_trade_volume / df['volume']
        
        return block_trade_ratio.fillna(0)
    
    def get_hk_market_characteristics(self, data: pd.DataFrame) -> Dict:
        """
        获取港股市场特征
        
        :param data: 港股数据
        :return: 市场特征字典
        """
        if data.empty:
            return {}
        
        characteristics = {
            'market_type': '港股',
            'trading_currency': 'HKD',
            'data_points': len(data),
            'price_range': {
                'min': float(data['close'].min()),
                'max': float(data['close'].max()),
                'current': float(data['close'].iloc[-1])
            },
            'volatility': {
                'daily_vol': float(data['close'].pct_change().std()),
                'annual_vol': float(data['close'].pct_change().std() * np.sqrt(250))
            },
            'liquidity': {
                'avg_volume': float(data['volume'].mean()),
                'avg_amount': float(data['amount'].mean())
            }
        }
        
        # 计算港股特有统计
        if 'HK_HV_20' in data.columns:
            characteristics['hk_specific'] = {
                'hv_20': float(data['HK_HV_20'].iloc[-1]),
                'vol_index': float(data.get('HK_VOL_INDEX', pd.Series([0])).iloc[-1]),
                'money_flow': float(data.get('HK_MONEY_FLOW', pd.Series([50])).iloc[-1])
            }
        
        return characteristics