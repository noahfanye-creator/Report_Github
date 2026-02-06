# src/models/capital_flow_models.py
"""
资金面数据模型定义
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd

@dataclass
class CapitalFlowData:
    """资金流向数据模型"""
    symbol: str
    date: datetime
    # 资金流入流出
    inflow_total: float  # 总流入
    outflow_total: float  # 总流出
    net_inflow: float  # 净流入
    
    # 分类型资金流
    main_force_inflow: float  # 主力资金流入
    main_force_outflow: float  # 主力资金流出
    retail_inflow: float  # 散户资金流入
    retail_outflow: float  # 散户资金流出
    
    # 北向/南向资金
    northbound_flow: Optional[float] = None  # 北向资金
    southbound_flow: Optional[float] = None  # 南向资金
    
    # 成交明细
    large_order_volume: float  # 大单成交量
    medium_order_volume: float  # 中单成交量
    small_order_volume: float  # 小单成交量

@dataclass
class MarginTradingData:
    """融资融券数据模型"""
    symbol: str
    date: datetime
    # 融资数据
    margin_balance: float  # 融资余额
    margin_buy_amount: float  # 融资买入额
    margin_repay_amount: float  # 融资偿还额
    
    # 融券数据
    short_balance: float  # 融券余额
    short_sell_amount: float  # 融券卖出量
    short_cover_amount: float  # 融券偿还量
    
    # 比例指标
    margin_ratio: float  # 融资余额占流通市值比例
    short_ratio: float  # 融券余额占流通市值比例

@dataclass
class CapitalSentiment:
    """资金情绪数据模型"""
    symbol: str
    date: datetime
    # 情绪指数（0-100）
    overall_sentiment: float  # 总体情绪
    main_force_sentiment: float  # 主力情绪
    retail_sentiment: float  # 散户情绪
    institution_sentiment: float  # 机构情绪
    
    # 情绪趋势
    sentiment_trend: str  # 上升/下降/平稳
    trend_strength: float  # 趋势强度
    
    # 情绪状态
    sentiment_state: str  # 极度乐观/乐观/中性/悲观/极度悲观
    confidence_level: float  # 置信度

@dataclass
class CapitalFlowSignal:
    """资金面信号模型"""
    symbol: str
    signal_type: str  # 信号类型
    signal_strength: float  # 信号强度（0-100）
    trigger_date: datetime
    description: str
    confidence: float  # 置信度
    related_indicators: List[str]  # 相关指标
    recommendation: Optional[str] = None  # 操作建议