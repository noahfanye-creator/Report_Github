"""
资金面数据模型
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class CapitalFlowData:
    """资金流向数据模型"""
    symbol: str
    date: datetime
    inflow_total: float
    outflow_total: float
    net_inflow: float
    main_force_inflow: float
    main_force_outflow: float
    retail_inflow: float
    retail_outflow: float
    northbound_flow: Optional[float] = None
    southbound_flow: Optional[float] = None
    large_order_volume: float = 0
    medium_order_volume: float = 0
    small_order_volume: float = 0


@dataclass
class MarginTradingData:
    """融资融券数据模型"""
    symbol: str
    date: datetime
    margin_balance: float
    margin_buy_amount: float
    margin_repay_amount: float
    short_balance: float
    short_sell_amount: float
    short_cover_amount: float
    margin_ratio: float
    short_ratio: float


@dataclass
class CapitalSentiment:
    """资金情绪数据模型"""
    symbol: str
    date: datetime
    overall_sentiment: float
    main_force_sentiment: float
    retail_sentiment: float
    institution_sentiment: float
    sentiment_trend: str
    trend_strength: float
    sentiment_state: str
    confidence_level: float


@dataclass
class CapitalFlowSignal:
    """资金面信号模型"""
    symbol: str
    signal_type: str
    signal_strength: float
    trigger_date: datetime
    description: str = ""
