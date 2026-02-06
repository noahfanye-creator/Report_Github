#!/usr/bin/env python3
"""
测试PDF中文字体
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from src.data_sources.unified_market_data import UnifiedMarketDataSystem
from src.report_generator.data_only_pdf_generator import DataOnlyPDFGenerator

# 生成测试数据
print("生成测试数据...")
data_system = UnifiedMarketDataSystem()
end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")

data = data_system.get_market_data(
    symbol="600519",
    start_date=start_date,
    end_date=end_date,
    market="A股",
    use_mock_on_failure=True
)

# 计算技术指标
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

# 生成PDF
print("\n生成PDF报告（测试中文字体）...")
pdf_gen = DataOnlyPDFGenerator()
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
pdf_path = f"outputs/reports/test_font_{timestamp}.pdf"

pdf_gen.generate_report(
    data=data,
    symbol="600519",
    market="A股",
    charts={},
    output_path=pdf_path
)

print(f"\n✅ PDF已生成: {pdf_path}")
print("请打开PDF文件检查中文字体是否正确显示")
