# src/capital_flow/indicators/flow_indicators.py
"""
资金流指标计算公式
"""

def calculate_net_inflow_ratio(total_inflow, total_outflow):
    """计算资金净流入率"""
    if total_inflow + total_outflow == 0:
        return 0
    return (total_inflow - total_outflow) / (total_inflow + total_outflow) * 100

def calculate_main_force_ratio(main_force_inflow, total_inflow):
    """计算主力资金占比"""
    if total_inflow == 0:
        return 0
    return main_force_inflow / total_inflow * 100

def calculate_flow_momentum(flow_series, period=5):
    """计算资金流动量"""
    # 使用价格动量公式计算资金流动量
    return flow_series.pct_change(period) * 100

def calculate_flow_divergence(price_series, flow_series, window=20):
    """计算资金流与价格背离度"""
    price_return = price_series.pct_change(window)
    flow_return = flow_series.pct_change(window)
    return price_return - flow_return

def calculate_concentration_index(large_order_vol, total_vol):
    """计算资金集中度"""
    if total_vol == 0:
        return 0
    return large_order_vol / total_vol * 100