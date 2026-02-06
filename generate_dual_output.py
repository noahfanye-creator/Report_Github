#!/usr/bin/env python3
"""
双输出系统主程序 - 生成JSON数据和可视化图表
"""
import sys
import os
import yaml
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from src.data_sources.unified_market_data import UnifiedMarketDataSystem
from src.core.dual_output_system import DualOutputSystem


def load_config(config_path: str = "config/chart_config.yaml") -> dict:
    """加载配置文件"""
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


def main():
    """主函数"""
    print("=" * 60)
    print("双输出系统 - JSON数据 + 可视化图表")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    
    # 初始化系统
    dual_system = DualOutputSystem(config)
    data_system = UnifiedMarketDataSystem()
    
    # 测试股票
    symbol = "600519"
    market = "A股"
    days = 500
    
    print(f"\n1. 获取 {symbol} ({market}) 数据...")
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
    
    # 处理股票（生成JSON和图表）
    print(f"\n2. 处理 {symbol}，生成JSON和图表...")
    result = dual_system.process_stock(
        data=data,
        symbol=symbol,
        market=market,
        output_base_dir="outputs"
    )
    
    # 显示结果
    print("\n" + "=" * 60)
    print("处理结果")
    print("=" * 60)
    print(f"\n📄 JSON文件:")
    for tf, path in result['json_files'].items():
        if os.path.exists(path):
            size = os.path.getsize(path) / 1024
            print(f"   {tf}: {path} ({size:.1f} KB)")
    
    print(f"\n📊 图表文件:")
    for tf, path in result['chart_files'].items():
        if os.path.exists(path):
            size = os.path.getsize(path) / 1024
            print(f"   {tf}: {path} ({size:.1f} KB)")
    
    print(f"\n✅ 验证结果:")
    all_passed = True
    for tf, validation in result['validation'].items():
        passed = (
            validation.get('ohlcv_match', False) and
            validation.get('indicators_match', False) and
            validation.get('timestamp_match', False)
        )
        status = "✅" if passed else "❌"
        print(f"   {tf}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✅ 所有数据一致性检查通过！")
    else:
        print("\n⚠️  部分数据一致性检查未通过，请查看详细报告")
    
    print("\n" + "=" * 60)
    print("✅ 处理完成！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
