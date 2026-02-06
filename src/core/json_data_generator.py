"""
JSON数据生成器 - 生成AI分析用结构化数据
"""
import os
import json
import gzip
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


class JSONDataGenerator:
    """JSON数据生成器（AI分析用）"""
    
    def __init__(self, precision_price: int = 4, precision_indicator: int = 4):
        """
        初始化JSON生成器
        
        Args:
            precision_price: 价格小数位数
            precision_indicator: 指标小数位数
        """
        self.precision_price = precision_price
        self.precision_indicator = precision_indicator
    
    def generate_metadata(
        self,
        symbol: str,
        timeframe: str,
        data: pd.DataFrame,
        indicators: List[str] = None
    ) -> Dict:
        """生成元数据"""
        if indicators is None:
            indicators = ['MA5', 'MA20', 'MA60', 'MACD', 'RSI14', 'BB', 'Volume']
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "data_points": len(data),
            "period": [
                data.index[0].strftime('%Y-%m-%d') if len(data) > 0 else None,
                data.index[-1].strftime('%Y-%m-%d') if len(data) > 0 else None
            ],
            "indicators": indicators,
            "generated_at": datetime.now().isoformat(),
            "data_source": "mock_data"
        }
    
    def generate_kline_json(
        self,
        data: pd.DataFrame,
        symbol: str,
        timeframe: str,
        index_data: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        生成K线JSON数据
        
        Args:
            data: K线数据（已包含技术指标）
            symbol: 股票代码
            timeframe: 周期
            index_data: 指数数据（用于计算相对强度）
        
        Returns:
            JSON格式的字典
        """
        metadata = self.generate_metadata(symbol, timeframe, data)
        
        kline_data = []
        
        for idx, row in data.iterrows():
            # 基础OHLCV数据
            ohlcv = [
                round(float(row['open']), self.precision_price),
                round(float(row['high']), self.precision_price),
                round(float(row['low']), self.precision_price),
                round(float(row['close']), self.precision_price),
                int(row['volume']) if pd.notna(row['volume']) else 0
            ]
            
            # 技术指标
            indicators = {}
            
            # 移动平均线
            if 'MA5' in data.columns and pd.notna(row.get('MA5')):
                indicators['MA'] = {}
                if 'MA5' in data.columns:
                    indicators['MA']['MA5'] = round(float(row['MA5']), self.precision_indicator)
                if 'MA20' in data.columns and pd.notna(row.get('MA20')):
                    indicators['MA']['MA20'] = round(float(row['MA20']), self.precision_indicator)
                if 'MA60' in data.columns and pd.notna(row.get('MA60')):
                    indicators['MA']['MA60'] = round(float(row['MA60']), self.precision_indicator)
            
            # MACD
            if 'MACD_DIF' in data.columns and pd.notna(row.get('MACD_DIF')):
                indicators['MACD'] = {
                    "DIF": round(float(row['MACD_DIF']), self.precision_indicator),
                    "DEA": round(float(row.get('MACD_DEA', 0)), self.precision_indicator),
                    "histogram": round(float(row.get('MACD_hist', 0)), self.precision_indicator)
                }
            
            # RSI
            if 'RSI14' in data.columns and pd.notna(row.get('RSI14')):
                indicators['RSI'] = {
                    "RSI14": round(float(row['RSI14']), self.precision_indicator)
                }
            
            # 布林带
            if 'BB_upper' in data.columns and pd.notna(row.get('BB_upper')):
                indicators['BB'] = {
                    "upper": round(float(row['BB_upper']), self.precision_indicator),
                    "middle": round(float(row.get('BB_middle', 0)), self.precision_indicator),
                    "lower": round(float(row.get('BB_lower', 0)), self.precision_indicator)
                }
            
            # 市场对比（相对强度）
            market_context = {}
            if index_data is not None and idx in index_data.index:
                index_close = index_data.loc[idx, 'close']
                stock_close = row['close']
                relative_strength = stock_close / index_close if index_close > 0 else 1.0
                market_context['index_price'] = round(float(index_close), self.precision_price)
                market_context['relative_strength'] = round(float(relative_strength), self.precision_indicator)
            
            kline_item = {
                "timestamp": idx.isoformat() if isinstance(idx, pd.Timestamp) else str(idx),
                "ohlcv": ohlcv,
                "indicators": indicators,
            }
            
            if market_context:
                kline_item["market_context"] = market_context
            
            kline_data.append(kline_item)
        
        return {
            "metadata": metadata,
            "kline_data": kline_data
        }
    
    def save_json(
        self,
        data: Dict,
        filepath: str,
        compress: bool = False
    ) -> str:
        """
        保存JSON文件
        
        Args:
            data: JSON数据字典
            filepath: 文件路径
            compress: 是否压缩为gzip
        
        Returns:
            实际保存的文件路径
        """
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        
        if compress:
            filepath = filepath + '.gz'
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                f.write(json_str)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        return filepath
    
    def generate_stock_json_files(
        self,
        processed_data: Dict[str, pd.DataFrame],
        symbol: str,
        output_dir: str,
        index_data: Optional[Dict[str, pd.DataFrame]] = None
    ) -> Dict[str, str]:
        """
        生成股票的所有周期JSON文件
        
        Args:
            processed_data: 处理后的多周期数据字典
            symbol: 股票代码
            output_dir: 输出目录
            index_data: 指数数据字典（可选）
        
        Returns:
            文件路径字典
        """
        files = {}
        
        # 创建股票目录
        stock_dir = os.path.join(output_dir, symbol.replace('.', '_'))
        os.makedirs(stock_dir, exist_ok=True)
        
        # 生成元数据文件
        metadata = {
            "symbol": symbol,
            "generated_at": datetime.now().isoformat(),
            "timeframes": list(processed_data.keys()),
            "data_source": "mock_data"
        }
        metadata_path = os.path.join(stock_dir, "metadata.json")
        self.save_json(metadata, metadata_path)
        files['metadata'] = metadata_path
        
        # 生成各周期JSON文件
        for timeframe, data in processed_data.items():
            if data.empty:
                continue
            
            # 获取对应的指数数据
            index_tf_data = None
            if index_data and timeframe in index_data:
                index_tf_data = index_data[timeframe]
            
            # 生成JSON数据
            json_data = self.generate_kline_json(data, symbol, timeframe, index_tf_data)
            
            # 保存文件
            filename = f"{timeframe}_100.json"
            filepath = os.path.join(stock_dir, filename)
            self.save_json(json_data, filepath)
            files[timeframe] = filepath
        
        return files
    
    def generate_relative_strength_matrix(
        self,
        stocks_data: Dict[str, pd.DataFrame],
        indices_data: Dict[str, pd.DataFrame],
        output_path: str
    ) -> str:
        """
        生成相对强度矩阵JSON
        
        Args:
            stocks_data: 多只股票数据字典
            indices_data: 多个指数数据字典
            output_path: 输出文件路径
        
        Returns:
            文件路径
        """
        matrix = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "stocks": list(stocks_data.keys()),
                "indices": list(indices_data.keys())
            },
            "relative_strength": {}
        }
        
        # 计算每只股票相对于每个指数的相对强度
        for stock_symbol, stock_data in stocks_data.items():
            if stock_data.empty:
                continue
            
            matrix["relative_strength"][stock_symbol] = {}
            
            for index_symbol, index_data in indices_data.items():
                if index_data.empty:
                    continue
                
                # 对齐时间
                common_dates = stock_data.index.intersection(index_data.index)
                if len(common_dates) == 0:
                    continue
                
                # 计算相对强度
                stock_returns = stock_data.loc[common_dates, 'close'].pct_change().fillna(0)
                index_returns = index_data.loc[common_dates, 'close'].pct_change().fillna(0)
                
                relative_strength = (1 + stock_returns) / (1 + index_returns)
                cumulative_rs = relative_strength.cumprod()
                
                matrix["relative_strength"][stock_symbol][index_symbol] = {
                    "latest": round(float(cumulative_rs.iloc[-1]), self.precision_indicator),
                    "average": round(float(cumulative_rs.mean()), self.precision_indicator),
                    "max": round(float(cumulative_rs.max()), self.precision_indicator),
                    "min": round(float(cumulative_rs.min()), self.precision_indicator)
                }
        
        return self.save_json(matrix, output_path)
