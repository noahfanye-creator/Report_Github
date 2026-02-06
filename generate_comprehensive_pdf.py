#!/usr/bin/env python3
"""
生成综合PDF报告 - 包含所有图表和数据
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


def generate_comprehensive_pdf(symbol="600519", market="A股", days=500):
    """生成综合PDF报告"""
    print("=" * 60)
    print("生成综合PDF报告（包含所有图表）")
    print("=" * 60)
    
    # 1. 获取数据
    print(f"\n1. 获取 {symbol} ({market}) 数据...")
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
    
    print(f"✅ 获取数据成功: {len(data)} 条")
    
    # 2. 计算技术指标
    print("\n2. 计算技术指标...")
    data['MA5'] = data['close'].rolling(5).mean()
    data['MA20'] = data['close'].rolling(20).mean()
    data['MA60'] = data['close'].rolling(60).mean()
    
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI14'] = 100 - (100 / (1 + rs))
    
    ema12 = data['close'].ewm(span=12).mean()
    ema26 = data['close'].ewm(span=26).mean()
    data['MACD_DIF'] = ema12 - ema26
    data['MACD_DEA'] = data['MACD_DIF'].ewm(span=9).mean()
    data['MACD_hist'] = data['MACD_DIF'] - data['MACD_DEA']
    
    # 布林带
    data['BB_middle'] = data['close'].rolling(window=20).mean()
    bb_std = data['close'].rolling(window=20).std()
    data['BB_upper'] = data['BB_middle'] + (bb_std * 2)
    data['BB_lower'] = data['BB_middle'] - (bb_std * 2)
    
    print("✅ 技术指标计算完成")
    
    # 3. 处理多周期数据
    print("\n3. 处理多周期数据...")
    data_engine = DataProcessingEngine()
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
                print(f"   ✅ {timeframe}: {len(tf_data)} 条数据")
        except Exception as e:
            print(f"   ⚠️  {timeframe} 处理失败: {e}")
    
    # 4. 生成所有图表
    print("\n4. 生成图表...")
    chart_gen = ChartGenerator()
    os.makedirs("outputs/charts", exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    charts = {}
    
    # 日线K线图（核心）
    if 'daily' in processed_data:
        daily_path = f"outputs/charts/daily_{symbol}_{timestamp}.png"
        chart_gen.generate_kline_chart(
            processed_data['daily'],
            symbol,
            market,
            daily_path,
            days=20
        )
        charts['daily'] = daily_path
        print(f"   ✅ 日线K线图: {daily_path}")
    
    # 周线K线图
    if 'weekly' in processed_data:
        weekly_path = f"outputs/charts/weekly_{symbol}_{timestamp}.png"
        weekly_data = processed_data['weekly']
        days_weekly = min(len(weekly_data), 20)
        chart_gen.generate_kline_chart(
            weekly_data,
            symbol,
            market,
            weekly_path,
            days=days_weekly
        )
        charts['weekly'] = weekly_path
        print(f"   ✅ 周线K线图: {weekly_path}")
    
    # 月线K线图
    if 'monthly' in processed_data:
        monthly_path = f"outputs/charts/monthly_{symbol}_{timestamp}.png"
        monthly_data = processed_data['monthly']
        days_monthly = min(len(monthly_data), 20)
        chart_gen.generate_kline_chart(
            monthly_data,
            symbol,
            market,
            monthly_path,
            days=days_monthly
        )
        charts['monthly'] = monthly_path
        print(f"   ✅ 月线K线图: {monthly_path}")
    
    # 技术指标图
    if not data.empty:
        indicators_path = f"outputs/charts/indicators_{symbol}_{timestamp}.png"
        chart_gen.generate_indicators_chart(data, symbol, market, indicators_path)
        charts['indicators'] = indicators_path
        print(f"   ✅ 技术指标图: {indicators_path}")
    
    # 综合仪表盘（使用日线数据）
    if 'daily' in processed_data:
        dashboard_path = f"outputs/charts/dashboard_{symbol}_{timestamp}.png"
        chart_gen.generate_kline_chart(
            processed_data['daily'],
            symbol,
            market,
            dashboard_path,
            days=20
        )
        charts['dashboard'] = dashboard_path
        print(f"   ✅ 综合仪表盘: {dashboard_path}")
    
    # 5. 生成综合PDF
    print("\n5. 生成综合PDF报告...")
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
    
    print(f"\n✅ 综合PDF报告已生成: {pdf_path}")
    print(f"\n📄 报告包含:")
    print(f"   - 封面页")
    print(f"   - 数据摘要")
    print(f"   - 日线K线图")
    if 'weekly' in charts:
        print(f"   - 周线K线图")
    if 'monthly' in charts:
        print(f"   - 月线K线图")
    print(f"   - 技术指标图")
    if 'dashboard' in charts:
        print(f"   - 综合仪表盘")
    print(f"   - 历史数据表格")
    print(f"   - 原始数据（JSON格式）")
    
    print("\n" + "=" * 60)
    print("✅ 所有图表已整合到PDF文档中！")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='生成综合PDF报告')
    parser.add_argument('--symbol', type=str, default='600519', help='股票代码')
    parser.add_argument('--market', type=str, default='A股', help='市场类型')
    parser.add_argument('--days', type=int, default=500, help='数据天数')
    
    args = parser.parse_args()
    
    try:
        generate_comprehensive_pdf(symbol=args.symbol, market=args.market, days=args.days)
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
