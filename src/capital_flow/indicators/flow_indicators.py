"""
资金流指标
"""


def calculate_net_inflow_ratio(total_inflow, total_outflow):
    if total_inflow + total_outflow == 0:
        return 0
    return (total_inflow - total_outflow) / (total_inflow + total_outflow) * 100


def calculate_main_force_ratio(main_force_inflow, total_inflow):
    if total_inflow == 0:
        return 0
    return main_force_inflow / total_inflow * 100


def calculate_flow_momentum(flow_series, period=5):
    return flow_series.pct_change(period) * 100


def calculate_flow_divergence(price_series, flow_series, window=20):
    return price_series.pct_change(window) - flow_series.pct_change(window)


def calculate_concentration_index(large_order_vol, total_vol):
    if total_vol == 0:
        return 0
    return large_order_vol / total_vol * 100
