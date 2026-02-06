#!/usr/bin/env python3
"""
生成完整的技术分析报告（PDF + K线图 + 技术指标图）
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.data_sources.unified_market_data import UnifiedMarketDataSystem
import pandas as pd


def generate_full_report(symbol="600519", market="A股", days=500):
    """生成完整报告"""
    print("=" * 60)
    print("生成完整技术分析报告")
    print("=" * 60)
    
    # 1. 获取数据
    print(f"\n1. 获取 {symbol} ({market}) 的模拟数据...")
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
    
    # RSI
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema12 = data['close'].ewm(span=12).mean()
    ema26 = data['close'].ewm(span=26).mean()
    data['MACD'] = ema12 - ema26
    data['MACD_signal'] = data['MACD'].ewm(span=9).mean()
    data['MACD_hist'] = data['MACD'] - data['MACD_signal']
    
    print("✅ 技术指标计算完成")
    
    # 3. 生成图表
    print("\n3. 生成图表...")
    charts = {}
    
    try:
        from src.report_generator.chart_generator import ChartGenerator
        
        chart_gen = ChartGenerator()
        os.makedirs("outputs/charts", exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # K线图（根据模板要求：最近20个交易日，1920×1080分辨率）
        kline_path = f"outputs/charts/kline_{symbol}_{timestamp}.png"
        print(f"   生成K线图: {kline_path} (最近20个交易日，1920×1080)")
        chart_gen.generate_kline_chart(data, symbol, market, kline_path, days=20)
        charts['kline'] = kline_path
        
        # 技术指标图
        indicators_path = f"outputs/charts/indicators_{symbol}_{timestamp}.png"
        print(f"   生成技术指标图: {indicators_path}")
        chart_gen.generate_indicators_chart(data, symbol, market, indicators_path)
        charts['indicators'] = indicators_path
        
        print("✅ 图表生成完成")
        
    except Exception as e:
        print(f"⚠️  图表生成失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. 生成PDF报告（纯数据版本，根据data.11要求）
    print("\n4. 生成PDF报告（纯数据版本）...")
    
    try:
        from src.report_generator.data_only_pdf_generator import DataOnlyPDFGenerator
        
        pdf_gen = DataOnlyPDFGenerator()
        os.makedirs("outputs/reports", exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        pdf_path = f"outputs/reports/data_report_{symbol}_{timestamp}.pdf"
        print(f"   生成PDF: {pdf_path}")
        
        pdf_gen.generate_report(
            data=data,
            symbol=symbol,
            market=market,
            charts=charts,
            output_path=pdf_path
        )
        
        print(f"✅ PDF报告已生成: {pdf_path}")
        print(f"\n📄 报告文件:")
        print(f"   - PDF报告（纯数据版）: {pdf_path}")
        if 'kline' in charts:
            print(f"   - K线图: {charts['kline']}")
        if 'indicators' in charts:
            print(f"   - 技术指标图: {charts['indicators']}")
        
    except ImportError as e:
        print(f"⚠️  PDF生成失败（reportlab未安装）: {e}")
        print("   请运行: pip install reportlab")
    except Exception as e:
        print(f"⚠️  PDF生成失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ 报告生成完成！")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='生成技术分析报告')
    parser.add_argument('--symbol', type=str, default='600519', help='股票代码')
    parser.add_argument('--market', type=str, default='A股', help='市场类型 (A股/港股/美股)')
    parser.add_argument('--days', type=int, default=500, help='数据天数')
    
    args = parser.parse_args()
    
    try:
        generate_full_report(symbol=args.symbol, market=args.market, days=args.days)
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
