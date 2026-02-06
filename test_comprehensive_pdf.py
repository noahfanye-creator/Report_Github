#!/usr/bin/env python3
"""
测试综合PDF生成（包含所有图表）
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from src.data_sources.unified_market_data import UnifiedMarketDataSystem
from src.core.data_processing_engine import DataProcessingEngine
from src.report_generator.chart_generator import ChartGenerator
from src.report_generator.comprehensive_pdf_generator import ComprehensivePDFGenerator


def test_comprehensive_pdf():
    """测试综合PDF生成"""
    print("=" * 60)
    print("测试综合PDF生成（包含所有图表）")
    print("=" * 60)
    
    symbol = "600519"
    market = "A股"
    days = 500  # 生成足够的数据
    
    # 1. 获取数据
    print(f"\n1. 获取 {symbol} 数据（{days}天）...")
    data_system = UnifiedMarketDataSystem()
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    data = data_system.get_market_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        market=market,
        use_mock_on_failure=True
    )
    
    if data is None or data.empty:
        print("❌ 无法获取数据")
        return
    
    print(f"✅ 数据获取成功: {len(data)} 条")
    print(f"   日期范围: {data.index[0].date()} 至 {data.index[-1].date()}")
    
    # 2. 计算技术指标
    print("\n2. 计算技术指标...")
    data_engine = DataProcessingEngine()
    data = data_engine.calculate_indicators(data)
    print("✅ 技术指标计算完成")
    
    # 3. 处理多周期数据
    print("\n3. 处理多周期数据...")
    timeframes = ['daily', 'weekly', 'monthly']
    processed_data = {}
    
    for timeframe in timeframes:
        try:
            tf_data = data_engine.convert_to_timeframe(data, timeframe)
            if not tf_data.empty:
                tf_data = data_engine.calculate_indicators(tf_data)
                if len(tf_data) > 100:
                    tf_data = tf_data.tail(100)
                processed_data[timeframe] = tf_data
                print(f"   ✅ {timeframe}: {len(tf_data)} 条")
        except Exception as e:
            print(f"   ⚠️  {timeframe}: {e}")
    
    # 4. 生成所有图表
    print("\n4. 生成所有图表...")
    chart_gen = ChartGenerator()
    os.makedirs("outputs/charts", exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    charts = {}
    
    # 日线K线图
    if 'daily' in processed_data:
        daily_path = f"outputs/charts/daily_{symbol}_{timestamp}.png"
        chart_gen.generate_kline_chart(processed_data['daily'], symbol, market, daily_path, days=20)
        charts['daily'] = daily_path
        print(f"   ✅ 日线K线图")
    
    # 周线K线图
    if 'weekly' in processed_data:
        weekly_path = f"outputs/charts/weekly_{symbol}_{timestamp}.png"
        weekly_data = processed_data['weekly']
        days_weekly = min(len(weekly_data), 20)
        chart_gen.generate_kline_chart(weekly_data, symbol, market, weekly_path, days=days_weekly)
        charts['weekly'] = weekly_path
        print(f"   ✅ 周线K线图")
    
    # 月线K线图
    if 'monthly' in processed_data:
        monthly_path = f"outputs/charts/monthly_{symbol}_{timestamp}.png"
        monthly_data = processed_data['monthly']
        days_monthly = min(len(monthly_data), 20)
        chart_gen.generate_kline_chart(monthly_data, symbol, market, monthly_path, days=days_monthly)
        charts['monthly'] = monthly_path
        print(f"   ✅ 月线K线图")
    
    # 技术指标图
    indicators_path = f"outputs/charts/indicators_{symbol}_{timestamp}.png"
    chart_gen.generate_indicators_chart(data, symbol, market, indicators_path)
    charts['indicators'] = indicators_path
    print(f"   ✅ 技术指标图")
    
    # 综合仪表盘
    if 'daily' in processed_data:
        dashboard_path = f"outputs/charts/dashboard_{symbol}_{timestamp}.png"
        chart_gen.generate_kline_chart(processed_data['daily'], symbol, market, dashboard_path, days=20)
        charts['dashboard'] = dashboard_path
        print(f"   ✅ 综合仪表盘")
    
    # 5. 生成综合PDF
    print("\n5. 生成综合PDF（整合所有图表）...")
    pdf_gen = ComprehensivePDFGenerator()
    os.makedirs("outputs/reports", exist_ok=True)
    
    pdf_path = f"outputs/reports/comprehensive_{symbol}_{timestamp}.pdf"
    
    pdf_gen.generate_comprehensive_report(
        data=data,
        symbol=symbol,
        market=market,
        charts=charts,
        processed_data=processed_data,
        output_path=pdf_path
    )
    
    print(f"\n✅ 综合PDF已生成: {pdf_path}")
    
    # 检查文件
    if os.path.exists(pdf_path):
        size = os.path.getsize(pdf_path) / 1024 / 1024
        print(f"   文件大小: {size:.2f} MB")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_comprehensive_pdf()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
