#!/usr/bin/env python3
"""
测试模拟数据生成功能
根据 data10.txt 中的解决方案实现
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.data_sources.unified_market_data import UnifiedMarketDataSystem
import pandas as pd


def test_mock_data_generation():
    """测试模拟数据生成"""
    print("=" * 60)
    print("测试模拟数据生成功能")
    print("=" * 60)
    
    # 创建数据系统实例
    data_system = UnifiedMarketDataSystem()
    
    # 测试用例
    test_cases = [
        ("600519", "A股", "贵州茅台"),
        ("000001", "A股", "平安银行"),
        ("00700", "港股", "腾讯控股"),
        ("AAPL", "美股", "苹果"),
    ]
    
    # 设置日期范围（最近1年）
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    print(f"\n日期范围: {start_date} 至 {end_date}\n")
    
    results = []
    
    for symbol, market, name in test_cases:
        print(f"\n{'='*60}")
        print(f"测试 {name} ({symbol}) - {market}")
        print(f"{'='*60}")
        
        try:
            # 使用模拟数据模式
            data = data_system.get_market_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                market=market,
                use_mock_on_failure=True  # 启用模拟数据降级
            )
            
            if data is not None and not data.empty:
                print(f"✅ 成功生成模拟数据")
                print(f"   数据条数: {len(data)}")
                print(f"   日期范围: {data.index[0].date()} 至 {data.index[-1].date()}")
                print(f"   最新数据:")
                print(f"     收盘价: {data['close'].iloc[-1]:.2f}")
                print(f"     涨跌幅: {data['pct_change'].iloc[-1]:.2f}%")
                print(f"     成交量: {data['volume'].iloc[-1]:,.0f}")
                print(f"     成交额: {data['amount'].iloc[-1]:,.0f}")
                
                # 检查数据完整性
                required_cols = ['open', 'high', 'low', 'close', 'volume', 'amount', 'pct_change']
                missing_cols = [col for col in required_cols if col not in data.columns]
                if missing_cols:
                    print(f"   ⚠️  缺少列: {missing_cols}")
                else:
                    print(f"   ✅ 数据列完整")
                
                # 检查数据合理性
                if data['high'].iloc[-1] >= data['low'].iloc[-1] >= 0:
                    print(f"   ✅ 价格数据合理")
                else:
                    print(f"   ⚠️  价格数据异常")
                
                if data['volume'].iloc[-1] > 0:
                    print(f"   ✅ 成交量数据合理")
                else:
                    print(f"   ⚠️  成交量数据异常")
                
                results.append(True)
            else:
                print(f"❌ 生成失败：数据为空")
                results.append(False)
                
        except Exception as e:
            print(f"❌ 生成失败：{e}")
            results.append(False)
    
    # 总结
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")
    success_count = sum(results)
    total_count = len(results)
    success_rate = success_count / total_count * 100 if total_count > 0 else 0
    print(f"成功率: {success_rate:.1f}% ({success_count}/{total_count})")
    
    if success_rate == 100:
        print("✅ 所有测试通过！")
    elif success_rate >= 50:
        print("⚠️  部分测试通过，请检查失败的用例")
    else:
        print("❌ 大部分测试失败，请检查代码")
    
    return success_rate == 100


def test_mock_data_consistency():
    """测试模拟数据的一致性（相同代码应生成相同数据）"""
    print("\n" + "=" * 60)
    print("测试模拟数据一致性")
    print("=" * 60)
    
    data_system = UnifiedMarketDataSystem()
    
    symbol = "600519"
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")
    
    # 生成两次数据
    print(f"\n生成 {symbol} 的模拟数据（第一次）...")
    data1 = data_system.get_market_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        use_mock_on_failure=True
    )
    
    print(f"生成 {symbol} 的模拟数据（第二次）...")
    data2 = data_system.get_market_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        use_mock_on_failure=True
    )
    
    if data1 is not None and data2 is not None:
        # 比较数据
        if len(data1) == len(data2):
            print(f"✅ 数据条数一致: {len(data1)}")
        else:
            print(f"⚠️  数据条数不一致: {len(data1)} vs {len(data2)}")
        
        # 比较收盘价（应该完全相同）
        if data1['close'].equals(data2['close']):
            print(f"✅ 价格数据一致（相同代码生成相同数据）")
        else:
            print(f"⚠️  价格数据不一致")
            diff = (data1['close'] - data2['close']).abs().max()
            print(f"   最大差异: {diff:.6f}")
        
        return True
    else:
        print("❌ 数据生成失败")
        return False


def generate_sample_report():
    """生成样本技术分析报告（使用模拟数据）- 包含PDF和图表"""
    print("\n" + "=" * 60)
    print("生成完整技术分析报告（PDF + 图表）")
    print("=" * 60)
    
    data_system = UnifiedMarketDataSystem()
    
    symbol = "600519"
    market = "A股"
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=500)).strftime("%Y-%m-%d")
    
    print(f"\n获取 {symbol} 的模拟数据...")
    data = data_system.get_market_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        market=market,
        use_mock_on_failure=True
    )
    
    if data is None or data.empty:
        print("无法获取数据，跳过报告生成")
        return
    
    # 计算技术指标
    print("计算技术指标...")
    data['MA5'] = data['close'].rolling(5).mean()
    data['MA20'] = data['close'].rolling(20).mean()
    data['MA60'] = data['close'].rolling(60).mean()
    
    # 计算RSI
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # 计算MACD
    ema12 = data['close'].ewm(span=12).mean()
    ema26 = data['close'].ewm(span=26).mean()
    data['MACD'] = ema12 - ema26
    data['MACD_signal'] = data['MACD'].ewm(span=9).mean()
    data['MACD_hist'] = data['MACD'] - data['MACD_signal']
    
    # 生成图表
    print("\n生成图表...")
    try:
        from src.report_generator.chart_generator import ChartGenerator
        
        chart_gen = ChartGenerator()
        os.makedirs("outputs/charts", exist_ok=True)
        
        # 生成K线图
        kline_path = f"outputs/charts/kline_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        chart_gen.generate_kline_chart(data, symbol, market, kline_path)
        
        # 生成技术指标图
        indicators_path = f"outputs/charts/indicators_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        chart_gen.generate_indicators_chart(data, symbol, market, indicators_path)
        
        charts = {
            'kline': kline_path,
            'indicators': indicators_path
        }
        
        print(f"✅ 图表生成完成")
        
    except Exception as e:
        print(f"⚠️  图表生成失败: {e}")
        charts = {}
    
    # 生成PDF报告
    print("\n生成PDF报告...")
    try:
        from src.report_generator.pdf_report_generator import PDFReportGenerator
        
        pdf_gen = PDFReportGenerator()
        os.makedirs("outputs/reports", exist_ok=True)
        
        pdf_path = f"outputs/reports/report_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_gen.generate_report(
            data=data,
            symbol=symbol,
            market=market,
            charts=charts,
            output_path=pdf_path
        )
        
        print(f"✅ PDF报告已生成: {pdf_path}")
        
    except ImportError as e:
        print(f"⚠️  PDF生成失败（reportlab未安装）: {e}")
        print("   请运行: pip install reportlab")
    except Exception as e:
        print(f"⚠️  PDF生成失败: {e}")
    
    # 同时生成文本报告
    report = f"""
==========================================
股票技术分析报告（模拟数据）
==========================================
股票: {symbol} (模拟数据)
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
数据范围: {data.index[0].date()} 至 {data.index[-1].date()}
数据条数: {len(data)}
==========================================

最新数据摘要:
  收盘价: {data['close'].iloc[-1]:.2f}
  开盘价: {data['open'].iloc[-1]:.2f}
  最高价: {data['high'].iloc[-1]:.2f}
  最低价: {data['low'].iloc[-1]:.2f}
  涨跌幅: {data['pct_change'].iloc[-1]:.2f}%
  成交量: {data['volume'].iloc[-1]:,.0f}
  成交额: {data['amount'].iloc[-1]:,.0f}

技术指标:
  MA5: {data['MA5'].iloc[-1]:.2f}
  MA20: {data['MA20'].iloc[-1]:.2f}
  MA60: {data['MA60'].iloc[-1]:.2f}
  RSI(14): {data['RSI'].iloc[-1]:.1f}

趋势分析:
  {'多头排列' if data['MA5'].iloc[-1] > data['MA20'].iloc[-1] > data['MA60'].iloc[-1] else '空头排列' if data['MA5'].iloc[-1] < data['MA20'].iloc[-1] < data['MA60'].iloc[-1] else '震荡'}
  {'RSI超买' if data['RSI'].iloc[-1] > 70 else 'RSI超卖' if data['RSI'].iloc[-1] < 30 else 'RSI正常'}

价格统计:
  最高价: {data['high'].max():.2f}
  最低价: {data['low'].min():.2f}
  平均价: {data['close'].mean():.2f}
  波动率: {data['pct_change'].std():.2f}%
  最大涨幅: {data['pct_change'].max():.2f}%
  最大跌幅: {data['pct_change'].min():.2f}%

==========================================
注: 此报告基于模拟数据生成，仅用于演示和测试目的
    实际投资请使用真实市场数据
==========================================
"""
    
    report_file = "sample_report_mock.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"✅ 文本报告已保存到: {report_file}")


if __name__ == "__main__":
    try:
        # 测试模拟数据生成
        success = test_mock_data_generation()
        
        # 测试数据一致性
        test_mock_data_consistency()
        
        # 生成样本报告
        generate_sample_report()
        
        print("\n" + "=" * 60)
        if success:
            print("✅ 所有测试完成！模拟数据功能正常工作。")
        else:
            print("⚠️  测试完成，但部分测试未通过。")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
