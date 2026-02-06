"""
统一市场数据采集系统 - 支持A股、港股、美股
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import akshare as ak
import tushare as ts
import yfinance as yf
import baostock as bs
from typing import Dict, List, Tuple, Optional, Union
import warnings
warnings.filterwarnings('ignore')

class UnifiedMarketDataSystem:
    """统一市场数据采集系统（A股 + 港股 + 美股）"""
    
    def __init__(self, data_sources: List[str] = ['akshare', 'yfinance', 'tushare']):
        """
        初始化多市场数据源
        
        :param data_sources: 数据源优先级列表
        """
        self.data_sources = data_sources
        self.ts_pro = None  # Tushare Pro实例
        self.bs_login = False  # Baostock登录状态
        
        # 市场代码映射
        self.market_mapping = {
            'A股': ['SH', 'SZ', 'BJ', 'sh', 'sz', 'bj'],
            '港股': ['HK', 'hk', '.HK'],
            '美股': ['US', 'us', '.US']
        }
        
        self._initialize_data_sources()
    
    def _initialize_data_sources(self):
        """初始化各数据源API"""
        try:
            # Tushare Pro
            if 'tushare' in self.data_sources:
                ts.set_token('你的tushare token')  # 需要申请
                self.ts_pro = ts.pro_api()
            
            # Baostock
            if 'baostock' in self.data_sources:
                lg = bs.login()
                if lg.error_code == '0':
                    self.bs_login = True
                    print("Baostock登录成功")
                else:
                    print(f"Baostock登录失败: {lg.error_msg}")
                    
        except Exception as e:
            print(f"数据源初始化失败: {e}")
    
    def get_market_data(self, 
                       symbol: str, 
                       start_date: str, 
                       end_date: str,
                       market: str = None,
                       data_type: str = 'daily',
                       adjust: str = 'hfq') -> pd.DataFrame:
        """
        获取多市场股票数据
        
        :param symbol: 股票代码
        :param market: 市场类型 ('A股', '港股', '美股')，自动检测
        :param start_date: 开始日期 'YYYY-MM-DD'
        :param end_date: 结束日期 'YYYY-MM-DD'
        :param data_type: 数据类型 'daily', 'weekly', 'monthly', '5min', '15min', '60min'
        :param adjust: 复权类型 'hfq'(后复权), 'qfq'(前复权), None(不复权)
        :return: 标准化的DataFrame
        """
        # 自动检测市场类型
        if market is None:
            market = self.detect_market(symbol)
        
        print(f"获取 {market} {symbol} 数据 ({start_date} 至 {end_date})")
        
        data = None
        
        # 根据不同市场使用不同数据源
        try:
            if market == 'A股':
                data = self._get_a_share_data(symbol, start_date, end_date, data_type, adjust)
            elif market == '港股':
                data = self._get_hk_share_data(symbol, start_date, end_date, data_type, adjust)
            elif market == '美股':
                data = self._get_us_share_data(symbol, start_date, end_date, data_type)
            else:
                raise ValueError(f"不支持的市场类型: {market}")
                
        except Exception as e:
            print(f"获取{market}数据失败: {e}")
            
            # 尝试备用数据源
            if market == '港股':
                print("尝试使用yfinance作为备用数据源...")
                data = self._get_hk_data_yfinance(symbol, start_date, end_date, data_type)
        
        if data is None or data.empty:
            raise ValueError(f"无法获取 {market} {symbol} 的数据")
        
        # 数据标准化处理
        data = self._standardize_data(data, symbol, market)
        
        return data
    
    def detect_market(self, symbol: str) -> str:
        """
        自动检测市场类型
        
        :param symbol: 股票代码
        :return: 市场类型 ('A股', '港股', '美股')
        """
        symbol_upper = symbol.upper()
        
        # 检测港股（常见模式）
        hk_patterns = ['.HK', 'HK', '0', '1', '2', '3', '6', '8']  # 港股代码通常以0-9开头
        if any(pattern in symbol_upper for pattern in ['.HK', 'HK']):
            return '港股'
        
        # 检测A股
        if any(pattern in symbol_upper for pattern in ['.SH', '.SZ', '.BJ', 'SH', 'SZ', 'BJ']):
            return 'A股'
        if symbol_upper.startswith(('6', '0', '3', '688', '689', '8')):
            return 'A股'
        
        # 检测美股
        if any(pattern in symbol_upper for pattern in ['.US', '.NASDAQ', '.NYSE', 'US']):
            return '美股'
        
        # 默认使用yfinance检测
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            if 'country' in info:
                if info['country'] == 'Hong Kong':
                    return '港股'
                elif info['country'] == 'United States':
                    return '美股'
                elif info['country'] == 'China':
                    return 'A股'
        except:
            pass
        
        # 默认认为是港股（因为港股代码格式多样）
        print(f"无法自动检测市场，默认视为港股: {symbol}")
        return '港股'
    
    def _get_a_share_data(self, symbol: str, start_date: str, end_date: str,
                         data_type: str, adjust: str) -> pd.DataFrame:
        """获取A股数据"""
        data = None
        
        for source in self.data_sources:
            try:
                if source == 'akshare':
                    data = self._get_a_from_akshare(symbol, start_date, end_date, data_type, adjust)
                elif source == 'tushare' and self.ts_pro is not None:
                    data = self._get_a_from_tushare(symbol, start_date, end_date, data_type, adjust)
                elif source == 'baostock' and self.bs_login:
                    data = self._get_a_from_baostock(symbol, start_date, end_date, data_type, adjust)
                elif source == 'yfinance':
                    data = self._get_a_from_yfinance(symbol, start_date, end_date, data_type)
                
                if data is not None and not data.empty:
                    break
            except Exception as e:
                print(f"A股数据源 {source} 失败: {e}")
                continue
        
        return data
    
    def _get_hk_share_data(self, symbol: str, start_date: str, end_date: str,
                          data_type: str, adjust: str) -> pd.DataFrame:
        """获取港股数据"""
        data = None
        
        # 清理港股代码格式
        hk_symbol = self._clean_hk_symbol(symbol)
        print(f"获取港股数据，代码: {hk_symbol}")
        
        for source in self.data_sources:
            try:
                if source == 'akshare':
                    data = self._get_hk_from_akshare(hk_symbol, start_date, end_date, data_type)
                elif source == 'yfinance':
                    data = self._get_hk_from_yfinance(hk_symbol, start_date, end_date, data_type)
                elif source == 'tushare' and self.ts_pro is not None:
                    data = self._get_hk_from_tushare(hk_symbol, start_date, end_date, data_type)
                
                if data is not None and not data.empty:
                    break
            except Exception as e:
                print(f"港股数据源 {source} 失败: {e}")
                continue
        
        return data
    
    def _clean_hk_symbol(self, symbol: str) -> str:
        """清理港股代码格式"""
        # 移除空格和点
        symbol = symbol.strip().replace('.', '').upper()
        
        # 移除HK后缀（如果有）
        if symbol.endswith('HK'):
            symbol = symbol[:-2]
        
        # 港股代码通常是5位数字，不足5位前面补0
        if symbol.isdigit() and len(symbol) < 5:
            symbol = symbol.zfill(5)
        
        return symbol
    
    def _get_hk_from_akshare(self, symbol: str, start_date: str, end_date: str,
                           data_type: str) -> pd.DataFrame:
        """从AKShare获取港股数据"""
        try:
            # AKShare港股日线数据
            if data_type == 'daily':
                df = ak.stock_hk_hist(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', ''),
                    adjust=""
                )
                
                # 重命名列
                df = df.rename(columns={
                    '日期': 'date',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount',
                    '涨跌幅': 'pct_change'
                })
                
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                return df
                
        except Exception as e:
            print(f"AKShare港股数据获取失败: {e}")
            return None
    
    def _get_hk_from_yfinance(self, symbol: str, start_date: str, end_date: str,
                            data_type: str) -> pd.DataFrame:
        """从Yahoo Finance获取港股数据"""
        try:
            # 添加.HK后缀
            yf_symbol = f"{symbol}.HK"
            
            stock = yf.Ticker(yf_symbol)
            
            if data_type == 'daily':
                df = stock.history(start=start_date, end=end_date, interval='1d')
            elif data_type == 'weekly':
                df = stock.history(start=start_date, end=end_date, interval='1wk')
            elif data_type == 'monthly':
                df = stock.history(start=start_date, end=end_date, interval='1mo')
            elif data_type == '60min':
                # 获取最近60天的60分钟数据
                recent_start = (datetime.strptime(end_date, '%Y-%m-%d') - 
                              timedelta(days=60)).strftime('%Y-%m-%d')
                df = stock.history(start=recent_start, end=end_date, interval='60m')
            else:
                return None
            
            # 重命名列
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # 计算成交额（港币）
            if 'amount' not in df.columns:
                df['amount'] = df['close'] * df['volume']
            
            return df
            
        except Exception as e:
            print(f"Yahoo Finance港股数据获取失败: {e}")
            return None
    
    def _get_hk_data_yfinance(self, symbol: str, start_date: str, end_date: str,
                            data_type: str) -> pd.DataFrame:
        """使用Yahoo Finance作为港股备用数据源"""
        return self._get_hk_from_yfinance(symbol, start_date, end_date, data_type)
    
    def _get_hk_from_tushare(self, symbol: str, start_date: str, end_date: str,
                           data_type: str) -> pd.DataFrame:
        """从Tushare获取港股数据（需要Pro版）"""
        if self.ts_pro is None:
            return None
        
        try:
            # Tushare港股代码格式：股票代码.HK
            ts_code = f"{symbol}.HK"
            
            if data_type == 'daily':
                df = self.ts_pro.hk_daily(
                    ts_code=ts_code,
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', '')
                )
                
                if df is not None and not df.empty:
                    df = df.rename(columns={
                        'trade_date': 'date',
                        'open': 'open',
                        'close': 'close',
                        'high': 'high',
                        'low': 'low',
                        'vol': 'volume',
                        'amount': 'amount'
                    })
                    
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    df.sort_index(inplace=True)
                    
                    return df
                    
        except Exception as e:
            print(f"Tushare港股数据获取失败: {e}")
            return None
        
        return None
    
    def _standardize_data(self, df: pd.DataFrame, symbol: str, market: str) -> pd.DataFrame:
        """
        标准化数据格式（多市场统一）
        
        :param df: 原始数据
        :param symbol: 股票代码
        :param market: 市场类型
        :return: 标准化的DataFrame
        """
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        
        # 检查必要列
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"数据缺少必要列: {col}")
        
        # 确保数据类型正确
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 计算成交额（如果没有）
        if 'amount' not in df.columns:
            df['amount'] = df['close'] * df['volume']
        
        # 计算涨跌幅
        if 'pct_change' not in df.columns:
            df['pct_change'] = df['close'].pct_change() * 100
        
        # 添加元数据
        df['symbol'] = symbol
        df['market'] = market
        
        # 确保索引是日期时间类型
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # 排序
        df.sort_index(inplace=True)
        
        # 去除重复和无效数据
        df = df[~df.index.duplicated(keep='first')]
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.dropna(subset=required_columns, how='all')
        
        # 填充缺失值
        for col in required_columns:
            if df[col].isnull().any():
                df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
        
        return df
    
    def get_multi_market_data(self, 
                            symbols: List[str],
                            start_date: str,
                            end_date: str,
                            data_type: str = 'daily') -> Dict[str, pd.DataFrame]:
        """
        批量获取多市场数据
        
        :param symbols: 股票代码列表
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param data_type: 数据类型
        :return: 字典 {股票代码: DataFrame}
        """
        results = {}
        
        for symbol in symbols:
            try:
                data = self.get_market_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    data_type=data_type
                )
                results[symbol] = data
                print(f"✓ 已获取 {symbol}")
                
            except Exception as e:
                print(f"✗ 获取 {symbol} 失败: {e}")
                results[symbol] = None
        
        return results
    
    def get_hk_index_data(self, index_code: str = 'HSI',
                         start_date: str = '2020-01-01',
                         end_date: str = '2026-01-26') -> pd.DataFrame:
        """
        获取港股指数数据
        
        :param index_code: 指数代码
            HSI: 恒生指数
            HSCEI: 恒生中国企业指数
            HSTECH: 恒生科技指数
        :return: 指数数据DataFrame
        """
        index_map = {
            'HSI': '^HSI',      # 恒生指数
            'HSCEI': '^HSCE',   # 恒生国企指数
            'HSTECH': '^HSTECH' # 恒生科技指数
        }
        
        yf_symbol = index_map.get(index_code, '^HSI')
        
        try:
            stock = yf.Ticker(yf_symbol)
            df = stock.history(start=start_date, end=end_date)
            
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            df['symbol'] = index_code
            df['market'] = '港股指数'
            
            return df
            
        except Exception as e:
            print(f"获取港股指数数据失败: {e}")
            return None