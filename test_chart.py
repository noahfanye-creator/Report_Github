#!/usr/bin/env python3
"""
测试K线图生成
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from src.data_sources.unified_market_data import UnifiedMarketDataSystem
from src.report_generator.chart_generator import ChartGenerator

# 生成测试数据
print("=" * 60)
print("测试K线图生成")
print("=" * 60)

data_system = UnifiedMarketDataSystem()
end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")

print(f"\n1. 获取数据...")
data = data_system.get_market_data(
    symbol="600519",
    start_date=start_date,
    end_date=end_date,
    market="A股",
    use_mock_on_failure=True
)

if data is None or data.empty:
    print("❌ 无法获取数据")
    sys.exit(1)

print(f"✅ 获取数据成功: {len(data)} 条")

# 计算技术指标
print("\n2. 计算技术指标...")
data['MA5'] = data['close'].rolling(5).mean()
data['MA20'] = data['close'].rolling(20).mean()
data['MA60'] = data['close'].rolling(60).mean()

delta = data['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
data['RSI'] = 100 - (100 / (1 + rs))

ema12 = data['close'].ewm(span=12).mean()
ema26 = data['close'].ewm(span=26).mean()
data['MACD'] = ema12 - ema26
data['MACD_signal'] = data['MACD'].ewm(span=9).mean()
data['MACD_hist'] = data['MACD'] - data['MACD_signal']

print("✅ 技术指标计算完成")
print(f"   数据列: {list(data.columns)}")
print(f"   数据范围: {data.index[0]} 至 {data.index[-1]}")
print(f"   最新收盘价: {data['close'].iloc[-1]:.2f}")

# 生成K线图（根据模板要求：最近20个交易日，1920×1080分辨率）
print("\n3. 生成K线图（符合模板要求）...")
chart_gen = ChartGenerator()
import os
os.makedirs("outputs/charts", exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
kline_path = f"outputs/charts/test_kline_{timestamp}.png"

try:
    # 根据模板要求：最近20个交易日，1920×1080分辨率
    chart_gen.generate_kline_chart(data, "600519", "A股", kline_path, days=20)
    print(f"✅ K线图已生成: {kline_path}")
    print(f"   文件大小: {os.path.getsize(kline_path) / 1024:.1f} KB")
    print(f"   分辨率: 1920×1080")
    print(f"   包含: K线图 + MA5/MA20/MA60 + MACD + RSI")
    print(f"   标注: 最高价/最低价、支撑位/阻力位")
except Exception as e:
    print(f"❌ K线图生成失败: {e}")
    import traceback
    traceback.print_exc()

# 生成技术指标图
print("\n4. 生成技术指标图...")
indicators_path = f"outputs/charts/test_indicators_{timestamp}.png"

try:
    chart_gen.generate_indicators_chart(data, "600519", "A股", indicators_path)
    print(f"✅ 技术指标图已生成: {indicators_path}")
    print(f"   文件大小: {os.path.getsize(indicators_path) / 1024:.1f} KB")
except Exception as e:
    print(f"❌ 技术指标图生成失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ 测试完成！")
print("=" * 60)
