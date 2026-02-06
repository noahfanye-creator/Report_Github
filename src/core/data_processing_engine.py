"""
数据处理引擎 - 计算K线 + 技术指标 + 市场对比
支持多周期转换和指标计算
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np


class DataProcessingEngine:
    """数据处理引擎"""
    
    def __init__(self):
        self.indicators_config = {
            'MA': [5, 20, 60],
            'MACD': {'fast': 12, 'slow': 26, 'signal': 9},
            'RSI': {'period': 14},
            'BB': {'period': 20, 'std': 2},
        }
    
    def convert_to_timeframe(
        self, 
        data: pd.DataFrame, 
        timeframe: str
    ) -> pd.DataFrame:
        """
        将日线数据转换为指定周期
        
        Args:
            data: 日线数据DataFrame
            timeframe: 周期类型 ('monthly', 'weekly', 'daily', '60min', '30min', '5min')
        
        Returns:
            转换后的K线数据
        """
        if timeframe == 'daily':
            return data.copy()
        
        if data.empty:
            return pd.DataFrame()
        
        # 确保索引是DatetimeIndex
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
        
        # 重采样规则
        resample_rules = {
            'monthly': 'M',
            'weekly': 'W',
            '60min': '60min',
            '30min': '30min',
            '5min': '5min',
        }
        
        if timeframe not in resample_rules:
            raise ValueError(f"不支持的时间周期: {timeframe}")
        
        rule = resample_rules[timeframe]
        
        # 重采样聚合
        resampled = data.resample(rule).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
        })
        
        # 计算成交额（如果有）
        if 'amount' in data.columns:
            resampled['amount'] = data.resample(rule)['amount'].sum()
        
        # 计算涨跌幅
        if 'pct_change' not in resampled.columns:
            resampled['pct_change'] = resampled['close'].pct_change() * 100
        
        # 移除NaN值
        resampled = resampled.dropna()
        
        # 保留最近100根
        if len(resampled) > 100:
            resampled = resampled.tail(100)
        
        return resampled
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标
        
        Args:
            data: K线数据DataFrame
        
        Returns:
            包含所有技术指标的DataFrame
        """
        result = data.copy()
        
        # 移动平均线
        for period in self.indicators_config['MA']:
            result[f'MA{period}'] = result['close'].rolling(window=period).mean()
        
        # MACD
        macd_config = self.indicators_config['MACD']
        ema_fast = result['close'].ewm(span=macd_config['fast']).mean()
        ema_slow = result['close'].ewm(span=macd_config['slow']).mean()
        result['MACD_DIF'] = ema_fast - ema_slow
        result['MACD_DEA'] = result['MACD_DIF'].ewm(span=macd_config['signal']).mean()
        result['MACD_hist'] = result['MACD_DIF'] - result['MACD_DEA']
        
        # RSI
        rsi_config = self.indicators_config['RSI']
        delta = result['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_config['period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_config['period']).mean()
        rs = gain / loss
        result['RSI14'] = 100 - (100 / (1 + rs))
        
        # 布林带
        bb_config = self.indicators_config['BB']
        result['BB_middle'] = result['close'].rolling(window=bb_config['period']).mean()
        bb_std = result['close'].rolling(window=bb_config['period']).std()
        result['BB_upper'] = result['BB_middle'] + (bb_std * bb_config['std'])
        result['BB_lower'] = result['BB_middle'] - (bb_std * bb_config['std'])
        
        # 成交量均线
        result['Volume_MA5'] = result['volume'].rolling(window=5).mean()
        
        return result
    
    def calculate_relative_strength(
        self, 
        stock_data: pd.DataFrame, 
        index_data: pd.DataFrame
    ) -> pd.Series:
        """
        计算相对强度（个股 vs 指数）
        
        Args:
            stock_data: 个股数据
            index_data: 指数数据
        
        Returns:
            相对强度序列
        """
        # 对齐时间索引
        common_dates = stock_data.index.intersection(index_data.index)
        
        if len(common_dates) == 0:
            return pd.Series()
        
        stock_returns = stock_data.loc[common_dates, 'close'].pct_change()
        index_returns = index_data.loc[common_dates, 'close'].pct_change()
        
        # 相对强度 = (1 + 个股收益率) / (1 + 指数收益率)
        relative_strength = (1 + stock_returns) / (1 + index_returns)
        relative_strength = relative_strength.cumprod()
        
        return relative_strength
    
    def detect_signals(self, data: pd.DataFrame) -> Dict:
        """
        检测技术信号（金叉、死叉、突破等）
        
        Args:
            data: 包含技术指标的数据
        
        Returns:
            信号字典
        """
        signals = {
            'golden_cross': [],
            'death_cross': [],
            'volume_spikes': [],
            'breakouts': [],
        }
        
        if len(data) < 2:
            return signals
        
        latest = data.iloc[-1]
        prev = data.iloc[-2]
        
        # 检测金叉/死叉（MA5与MA20）
        if 'MA5' in data.columns and 'MA20' in data.columns:
            if prev['MA5'] <= prev['MA20'] and latest['MA5'] > latest['MA20']:
                signals['golden_cross'].append({
                    'date': latest.name,
                    'type': 'MA5_MA20',
                    'price': latest['close']
                })
            elif prev['MA5'] >= prev['MA20'] and latest['MA5'] < latest['MA20']:
                signals['death_cross'].append({
                    'date': latest.name,
                    'type': 'MA5_MA20',
                    'price': latest['close']
                })
        
        # 检测放量
        if 'Volume_MA5' in data.columns:
            volume_ratio = latest['volume'] / latest['Volume_MA5'] if latest['Volume_MA5'] > 0 else 0
            if volume_ratio > 2.0:  # 成交量是均量的2倍以上
                signals['volume_spikes'].append({
                    'date': latest.name,
                    'volume_ratio': volume_ratio,
                    'price': latest['close']
                })
        
        # 检测突破（突破布林带上轨或下轨）
        if 'BB_upper' in data.columns and 'BB_lower' in data.columns:
            if prev['close'] <= prev['BB_upper'] and latest['close'] > latest['BB_upper']:
                signals['breakouts'].append({
                    'date': latest.name,
                    'type': 'upper_breakout',
                    'price': latest['close']
                })
            elif prev['close'] >= prev['BB_lower'] and latest['close'] < latest['BB_lower']:
                signals['breakouts'].append({
                    'date': latest.name,
                    'type': 'lower_breakout',
                    'price': latest['close']
                })
        
        return signals
    
    def process_stock_data(
        self,
        data: pd.DataFrame,
        symbol: str,
        timeframes: List[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        处理股票数据，生成多周期K线和指标
        
        Args:
            data: 原始日线数据
            symbol: 股票代码
            timeframes: 需要生成的周期列表
        
        Returns:
            字典，key为周期，value为处理后的数据
        """
        if timeframes is None:
            timeframes = ['monthly', 'weekly', 'daily', '60min', '30min', '5min']
        
        result = {}
        
        for timeframe in timeframes:
            # 转换周期
            tf_data = self.convert_to_timeframe(data, timeframe)
            
            if not tf_data.empty:
                # 计算指标
                tf_data = self.calculate_indicators(tf_data)
                
                # 保留最近100根
                if len(tf_data) > 100:
                    tf_data = tf_data.tail(100)
                
                result[timeframe] = tf_data
        
        return result
