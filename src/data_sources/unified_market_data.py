"""
统一市场数据采集系统 - 支持A股、港股、美股
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

import numpy as np
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

try:
    import akshare as ak
except ImportError:
    ak = None
try:
    import yfinance as yf
except ImportError:
    yf = None
try:
    import tushare as ts
except ImportError:
    ts = None
try:
    import baostock as bs
except ImportError:
    bs = None
try:
    import requests
except ImportError:
    requests = None


class UnifiedMarketDataSystem:
    """统一市场数据采集系统（A股 + 港股 + 美股）"""

    def __init__(self, data_sources: Optional[List[str]] = None):
        # 参考stock-analysis-bot项目，优先使用新浪财经（更稳定）
        # 数据源顺序：sina（最稳定） -> akshare -> yfinance -> tushare -> baostock
        self.data_sources = data_sources or ["sina", "akshare", "yfinance", "tushare", "baostock"]
        self.ts_pro = None
        self.bs_login = False
        self._init_sources()

    def _init_sources(self):
        try:
            if "tushare" in self.data_sources and ts is not None:
                ts.set_token("")
                self.ts_pro = ts.pro_api()
            if "baostock" in self.data_sources and bs is not None:
                lg = bs.login()
                self.bs_login = lg.error_code == "0"
        except Exception:
            pass

    def get_market_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        market: Optional[str] = None,
        data_type: str = "daily",
        adjust: str = "hfq",
        use_mock_on_failure: bool = False,
    ) -> pd.DataFrame:
        if market is None:
            market = self.detect_market(symbol)
        data = None
        try:
            if market == "A股":
                data = self._get_a_share_data(symbol, start_date, end_date, data_type, adjust)
            elif market == "港股":
                data = self._get_hk_share_data(symbol, start_date, end_date, data_type, adjust)
            elif market == "美股":
                data = self._get_us_share_data(symbol, start_date, end_date, data_type)
            else:
                raise ValueError(f"不支持的市场: {market}")
        except Exception as e:
            # 对于港股，尝试yfinance作为备用
            if market == "港股" and yf is not None:
                try:
                    print("尝试使用yfinance作为备用数据源...")
                    data = self._get_hk_from_yfinance(
                        self._clean_hk_symbol(symbol), start_date, end_date, data_type
                    )
                except Exception:
                    pass
            # 对于A股，如果akshare失败，yfinance已经在重试逻辑中尝试了
        
        if data is None or data.empty:
            if use_mock_on_failure:
                print("⚠️  所有数据源失败，使用模拟数据（仅用于测试）")
                data = self._generate_mock_data(symbol, start_date, end_date, market)
                if data is not None and not data.empty:
                    return self._standardize_data(data, symbol, market)
            
            error_msg = f"无法获取 {market} {symbol} 数据"
            error_msg += "\n可能的原因："
            error_msg += "\n1. 网络连接问题（代理、防火墙等）"
            error_msg += "\n2. 数据源限流或暂时不可用"
            error_msg += "\n3. 股票代码不正确或已退市"
            error_msg += "\n建议：稍后重试或检查网络连接"
            if not use_mock_on_failure:
                error_msg += "\n提示：可以设置 use_mock_on_failure=True 使用模拟数据进行测试"
            raise ValueError(error_msg)
        return self._standardize_data(data, symbol, market)

    def detect_market(self, symbol: str) -> str:
        s = symbol.upper().strip().replace(".", "").replace(" ", "")
        if "HK" in symbol.upper():
            return "港股"
        if any(p in symbol.upper() for p in [".SH", ".SZ", ".BJ", "SH", "SZ", "BJ"]):
            return "A股"
        dig = "".join(c for c in s if c.isdigit())
        if len(dig) == 5:
            return "港股"
        if len(dig) == 6 and dig.startswith(("6", "0", "3", "9", "8")):
            return "A股"
        if any(p in symbol.upper() for p in [".US", ".NASDAQ", ".NYSE", "US"]):
            return "美股"
        if yf is not None:
            try:
                info = yf.Ticker(symbol).info
                c = info.get("country", "")
                if c == "Hong Kong":
                    return "港股"
                if c == "United States":
                    return "美股"
                if c == "China":
                    return "A股"
            except Exception:
                pass
        return "港股"

    def _get_a_share_data(
        self, symbol: str, start: str, end: str, data_type: str, adjust: str
    ) -> pd.DataFrame:
        errors = []
        # 重试逻辑：最多尝试3次，每次间隔2秒
        max_retries = 3
        retry_delay = 2
        
        for src in self.data_sources:
            # 检查数据源是否可用
            if src == "akshare" and ak is None:
                print(f"⏭️  跳过数据源 {src} (未安装)")
                continue
            elif src == "tushare" and self.ts_pro is None:
                print(f"⏭️  跳过数据源 {src} (未配置)")
                continue
            elif src == "baostock" and (not self.bs_login or bs is None):
                print(f"⏭️  跳过数据源 {src} (未登录)")
                continue
            elif src == "sina" and requests is None:
                print(f"⏭️  跳过数据源 {src} (requests未安装)")
                continue
            elif src == "yfinance" and yf is None:
                print(f"⏭️  跳过数据源 {src} (未安装)")
                continue
            
            print(f"尝试数据源: {src}...")
            for attempt in range(max_retries):
                try:
                    if src == "akshare":
                        out = self._get_a_from_akshare(symbol, start, end, data_type, adjust)
                    elif src == "tushare":
                        out = self._get_a_from_tushare(symbol, start, end, data_type, adjust)
                    elif src == "baostock":
                        out = self._get_a_from_baostock(symbol, start, end, data_type, adjust)
                    elif src == "sina":
                        # 新浪财经作为备用数据源，通常更稳定
                        out = self._get_a_from_sina(symbol, start, end, data_type)
                    elif src == "yfinance":
                        # yfinance需要延迟以避免限流
                        if attempt > 0:
                            time.sleep(retry_delay * (attempt + 1))
                        out = self._get_a_from_yfinance(symbol, start, end, data_type)
                    else:
                        break
                    
                    if out is not None and not out.empty:
                        print(f"✅ 数据源 {src} 获取成功: {len(out)} 条数据")
                        return out
                    elif attempt < max_retries - 1:
                        print(f"⚠️  数据源 {src} 返回空数据，重试中... ({attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                except Exception as e:
                    error_msg = str(e)
                    # 检查是否是网络相关错误
                    if any(keyword in error_msg.lower() for keyword in ['timeout', 'connection', 'proxy', 'rate limit', 'too many']):
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (attempt + 1)
                            print(f"⚠️  网络错误，等待 {wait_time} 秒后重试 ({attempt + 1}/{max_retries})...")
                            time.sleep(wait_time)
                            continue
                    print(f"❌ 数据源 {src} 失败: {error_msg[:100]}")
                    errors.append(f"{src}: {error_msg[:100]}")
                    break
        
        if errors:
            print(f"\n所有数据源均失败，最后错误: {errors[-1] if errors else '未知错误'}")
            print("提示: 可能是网络连接问题，请检查网络或稍后重试")
        return None

    def _get_a_from_akshare(
        self, symbol: str, start: str, end: str, data_type: str, adjust: str
    ) -> Optional[pd.DataFrame]:
        if ak is None:
            return None
        code = symbol.replace(".SH", "").replace(".SZ", "").replace(".BJ", "").strip()
        if data_type != "daily":
            return None
        
        try:
            # 添加小延迟避免请求过快
            time.sleep(0.5)
            
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start.replace("-", ""),
                end_date=end.replace("-", ""),
                adjust=adjust,
            )
            if df is None or df.empty:
                return None
            
            # 检查返回的列名，akshare可能返回不同的列名
            column_mapping = {
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
                "涨跌幅": "pct_change",
            }
            
            # 只重命名存在的列
            rename_dict = {k: v for k, v in column_mapping.items() if k in df.columns}
            df = df.rename(columns=rename_dict)
            
            # 确保必要的列存在
            if "date" not in df.columns:
                if "日期" in df.columns:
                    df["date"] = df["日期"]
                else:
                    return None
            
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
            
            # 确保必要的OHLCV列存在
            required_cols = ["open", "high", "low", "close", "volume"]
            missing_cols = [c for c in required_cols if c not in df.columns]
            if missing_cols:
                return None
            
            return df
        except Exception as e:
            error_msg = str(e)
            raise Exception(f"akshare获取失败: {error_msg}")

    def _get_a_from_tushare(
        self, symbol: str, start: str, end: str, data_type: str, adjust: str
    ) -> Optional[pd.DataFrame]:
        return None

    def _get_a_from_baostock(
        self, symbol: str, start: str, end: str, data_type: str, adjust: str
    ) -> Optional[pd.DataFrame]:
        return None

    def _normalize_code_for_sina(self, symbol: str) -> str:
        """将股票代码转换为新浪财经格式（参考stock-analysis-bot项目）"""
        code = symbol.replace(".SH", "").replace(".SZ", "").replace(".BJ", "").strip()
        
        # 如果已经是sh/sz格式，直接返回
        if code.startswith(("sh", "sz", "SH", "SZ")):
            return code.lower()
        
        # 根据代码判断交易所（参考code_normalizer.py）
        if code.startswith("6") or code.startswith("9") or code.startswith("688") or code.startswith("689"):
            return f"sh{code}"  # 上海交易所（包括科创板688）
        elif code.startswith("0") or code.startswith("3"):
            return f"sz{code}"  # 深圳交易所
        elif code.startswith("8") or code.startswith("4"):
            return f"bj{code}"  # 北京交易所（新浪可能不支持，但先尝试）
        else:
            return f"sh{code}"  # 默认上海

    def _get_a_from_sina(
        self, symbol: str, start: str, end: str, data_type: str
    ) -> Optional[pd.DataFrame]:
        """从新浪财经获取A股数据（参考stock-analysis-bot项目的fetch_kline_data）"""
        if requests is None:
            raise Exception("requests库未安装")
        
        if data_type != "daily":
            # 新浪财经主要支持日线，其他周期可能需要调整
            return None
        
        try:
            # 转换为新浪财经格式（参考code_normalizer.py）
            sina_code = self._normalize_code_for_sina(symbol)
            
            # 计算需要的数据条数（参考stock-analysis-bot，使用240表示日线）
            start_date = pd.to_datetime(start)
            end_date = pd.to_datetime(end)
            days = (end_date - start_date).days
            datalen = min(max(days + 30, 100), 500)  # 至少100条，最多500条
            
            # 新浪财经API（完全按照参考项目的实现）
            url = (
                f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
                f"CN_MarketData.getKLineData?symbol={sina_code}&scale=240&ma=no&datalen={datalen}"
            )
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
            
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code != 200:
                return None
            
            data = resp.json()
            if not data:
                return None
            
            df = pd.DataFrame(data)
            if df.empty:
                return None
            
            # 重命名列（参考参考项目的列名）
            df.rename(
                columns={
                    "day": "date",
                    "open": "open",
                    "high": "high",
                    "low": "low",
                    "close": "close",
                    "volume": "volume"
                },
                inplace=True,
            )
            
            # 转换数据类型
            cols = ["open", "high", "low", "close", "volume"]
            for col in cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            
            # 转换日期
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
            df.sort_index(inplace=True)
            
            # 过滤日期范围
            if len(df) > 0:
                df = df[(df.index >= start_date) & (df.index <= end_date)]
            
            if df.empty:
                return None
            
            # 添加必要列
            if "amount" not in df.columns:
                df["amount"] = df["close"] * df["volume"]
            if "pct_change" not in df.columns:
                df["pct_change"] = df["close"].pct_change() * 100
            
            return df
            
        except Exception as e:
            raise Exception(f"sina获取失败: {str(e)}")

    def _get_a_from_yfinance(
        self, symbol: str, start: str, end: str, data_type: str
    ) -> Optional[pd.DataFrame]:
        if yf is None:
            return None
        code = symbol.replace(".SH", "").replace(".SZ", "").replace(".BJ", "").strip()
        
        # 根据代码判断交易所
        if code.startswith(("6", "9", "688", "689")):
            suf = ".SS"  # 上海交易所（包括科创板688）
        elif code.startswith(("0", "3")):
            suf = ".SZ"  # 深圳交易所
        elif code.startswith(("8", "4")):
            suf = ".BJ"  # 北京交易所
        else:
            suf = ".SS"  # 默认上海
        
        sym = code + suf
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(start=start, end=end, interval="1d")
            if hist is None or hist.empty:
                return None
            hist = hist.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
            hist["amount"] = hist["close"] * hist["volume"]
            hist["pct_change"] = hist["close"].pct_change() * 100
            return hist[["open", "high", "low", "close", "volume", "amount", "pct_change"]]
        except Exception as e:
            raise Exception(f"yfinance获取失败: {str(e)}")

    def _get_us_share_data(
        self, symbol: str, start: str, end: str, data_type: str
    ) -> Optional[pd.DataFrame]:
        if yf is None:
            return None
        sym = symbol if "." in symbol else f"{symbol}"
        t = yf.Ticker(sym)
        iv = "1d" if data_type == "daily" else "1wk" if data_type == "weekly" else "1mo"
        h = t.history(start=start, end=end, interval=iv)
        if h is None or h.empty:
            return None
        h = h.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
        h["amount"] = h["close"] * h["volume"]
        h["pct_change"] = h["close"].pct_change() * 100
        return h[["open", "high", "low", "close", "volume", "amount", "pct_change"]]

    def _get_hk_share_data(
        self, symbol: str, start: str, end: str, data_type: str, adjust: str
    ) -> pd.DataFrame:
        hk = self._clean_hk_symbol(symbol)
        for src in self.data_sources:
            try:
                if src == "akshare" and ak is not None:
                    out = self._get_hk_from_akshare(hk, start, end, data_type)
                elif src == "yfinance" and yf is not None:
                    out = self._get_hk_from_yfinance(hk, start, end, data_type)
                elif src == "tushare" and self.ts_pro is not None:
                    out = self._get_hk_from_tushare(hk, start, end, data_type)
                else:
                    continue
                if out is not None and not out.empty:
                    return out
            except Exception:
                continue
        return None

    def _clean_hk_symbol(self, symbol: str) -> str:
        s = symbol.strip().replace(".", "").upper()
        if s.endswith("HK"):
            s = s[:-2]
        if s.isdigit() and len(s) < 5:
            s = s.zfill(5)
        return s

    def _get_hk_from_akshare(
        self, symbol: str, start: str, end: str, data_type: str
    ) -> Optional[pd.DataFrame]:
        if ak is None or data_type != "daily":
            return None
        df = ak.stock_hk_hist(
            symbol=symbol,
            period="daily",
            start_date=start.replace("-", ""),
            end_date=end.replace("-", ""),
            adjust="",
        )
        df = df.rename(columns={
            "日期": "date", "开盘": "open", "收盘": "close", "最高": "high",
            "最低": "low", "成交量": "volume", "成交额": "amount", "涨跌幅": "pct_change",
        })
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        return df

    def _get_hk_from_yfinance(
        self, symbol: str, start: str, end: str, data_type: str
    ) -> Optional[pd.DataFrame]:
        if yf is None:
            return None
        sym = f"{symbol}.HK"
        t = yf.Ticker(sym)
        iv = "1d" if data_type == "daily" else "1wk" if data_type == "weekly" else "1mo"
        df = t.history(start=start, end=end, interval=iv)
        if df is None or df.empty:
            return None
        df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
        df["amount"] = df["close"] * df["volume"]
        return df

    def _get_hk_from_tushare(
        self, symbol: str, start: str, end: str, data_type: str
    ) -> Optional[pd.DataFrame]:
        return None

    def _standardize_data(self, df: pd.DataFrame, symbol: str, market: str) -> pd.DataFrame:
        req = ["open", "high", "low", "close", "volume"]
        for c in req:
            if c not in df.columns:
                raise ValueError(f"缺少列: {c}")
        for c in ["open", "high", "low", "close", "volume"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        if "amount" not in df.columns:
            df["amount"] = df["close"] * df["volume"]
        if "pct_change" not in df.columns:
            df["pct_change"] = df["close"].pct_change() * 100
        df["symbol"] = symbol
        df["market"] = market
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        df = df[~df.index.duplicated(keep="first")]
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.dropna(subset=req, how="all")
        for c in req:
            if df[c].isnull().any():
                df[c] = df[c].ffill().bfill()
        return df

    def get_multi_market_data(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        data_type: str = "daily",
    ) -> Dict[str, Optional[pd.DataFrame]]:
        out = {}
        for s in symbols:
            try:
                out[s] = self.get_market_data(s, start_date, end_date, data_type=data_type)
            except Exception:
                out[s] = None
        return out

    def get_hk_index_data(
        self,
        index_code: str = "HSI",
        start_date: str = "2020-01-01",
        end_date: str = "2026-01-26",
    ) -> Optional[pd.DataFrame]:
        if yf is None:
            return None
        m = {"HSI": "^HSI", "HSCEI": "^HSCE", "HSTECH": "^HSTECH"}
        sym = m.get(index_code, "^HSI")
        df = yf.Ticker(sym).history(start=start_date, end=end_date)
        if df is None or df.empty:
            return None
        df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
        df["symbol"] = index_code
        df["market"] = "港股指数"
        return df

    def _generate_mock_data(
        self, symbol: str, start_date: str, end_date: str, market: str
    ) -> Optional[pd.DataFrame]:
        """
        生成模拟股票数据（用于测试和开发）
        基于几何布朗运动模型生成价格序列
        """
        try:
            # 解析日期范围
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            # 生成交易日日期范围（排除周末）
            dates = pd.date_range(start=start_dt, end=end_dt, freq='B')
            n = len(dates)
            
            if n == 0:
                return None
            
            # 使用股票代码作为随机种子，确保相同代码生成相同数据
            np.random.seed(hash(symbol) % 10000)
            
            # 生成价格序列（几何布朗运动）
            # 每日收益率：均值0.0003（年化约7.5%），标准差0.018（年化约28%）
            returns = np.random.normal(0.0003, 0.018, n)
            
            # 根据股票代码调整初始价格，使不同股票有不同的价格水平
            price_base = 50 + (hash(symbol) % 200)  # 50-250之间的价格
            initial_price = float(price_base)
            price = initial_price * np.exp(np.cumsum(returns))
            
            # 确保价格不会太低或太高
            price = np.clip(price, initial_price * 0.3, initial_price * 3.0)
            
            # 创建DataFrame
            df = pd.DataFrame(index=dates)
            df['close'] = price
            
            # 生成开盘价（基于前一收盘价，有小的跳空）
            df['open'] = df['close'].shift(1) * (1 + np.random.normal(0, 0.005, n))
            df.loc[dates[0], 'open'] = initial_price
            
            # 初始化 high 和 low 列
            df['high'] = 0.0
            df['low'] = 0.0
            
            # 生成最高价和最低价
            for i in range(n):
                close_price = df.iloc[i]['close']
                open_price = df.iloc[i]['open']
                
                # 计算当日波动范围
                daily_range = abs(close_price - open_price) * (1.5 + np.random.rand())
                high = max(open_price, close_price) + daily_range * 0.3 * np.random.rand()
                low = min(open_price, close_price) - daily_range * 0.3 * np.random.rand()
                
                # 确保 high >= max(open, close) 和 low <= min(open, close)
                high = max(high, open_price, close_price)
                low = min(low, open_price, close_price)
                
                df.iloc[i, df.columns.get_loc('high')] = high
                df.iloc[i, df.columns.get_loc('low')] = low
            
            # 初始化 volume 列
            df['volume'] = 0.0
            
            # 生成成交量（对数正态分布，与价格波动相关）
            base_volume = 1000000
            for i in range(n):
                volume_variation = 0.5 + np.random.rand()
                price_change = abs(df['close'].pct_change().iloc[i]) if i > 0 else 0
                # 价格波动大时，成交量也大
                volume = base_volume * volume_variation * (1 + price_change * 10)
                df.iloc[i, df.columns.get_loc('volume')] = max(volume, 1000)  # 最小成交量
            
            # 计算成交额和涨跌幅
            df['amount'] = df['close'] * df['volume']
            df['pct_change'] = df['close'].pct_change() * 100
            
            # 移除NaN值
            df = df.dropna()
            
            if df.empty:
                return None
            
            return df
            
        except Exception as e:
            print(f"生成模拟数据失败: {e}")
            return None
