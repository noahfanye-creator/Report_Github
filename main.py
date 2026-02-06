#!/usr/bin/env python3
# main.py - 股票技术分析报告系统主入口

import sys
import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
os.chdir(_ROOT)

from core.main import StockAnalysisSystem

def _parse_symbols(raw: str) -> list[str]:
    """从一行字符串解析出多个股票代码（支持空格、逗号、中文逗号分隔）"""
    for sep in (",", "，", "\t"):
        raw = raw.replace(sep, " ")
    return [s.strip() for s in raw.split() if s.strip()]


def main():
    """主函数"""
    print("=" * 60)
    print("股票技术分析报告系统")
    print("=" * 60)
    
    # 获取股票代码（支持多个：命令行多个参数，或输入时用空格/逗号分隔）
    if len(sys.argv) > 1:
        symbols = _parse_symbols(" ".join(sys.argv[1:]))
    else:
        line = input("请输入股票代码，多个请用空格或逗号分隔（如：00700 600519.SH）: ").strip()
        symbols = _parse_symbols(line)
    
    if not symbols:
        print("错误：未提供股票代码")
        return
    
    # 创建系统实例
    system = StockAnalysisSystem()
    
    results = []
    for i, symbol in enumerate(symbols, 1):
        try:
            print(f"\n[{i}/{len(symbols)}] 正在分析: {symbol}")
            result = system.analyze_stock(symbol)
            results.append((symbol, result))
            print(f"  完成 -> 报告: {result.get('report_path', 'N/A')}")
        except Exception as e:
            print(f"  分析失败: {e}")
            results.append((symbol, {"error": str(e)}))
    
    # 汇总
    print("\n" + "=" * 60)
    print("全部完成！")
    print("=" * 60)
    for symbol, result in results:
        if "error" in result:
            print(f"  {symbol}: 失败 - {result['error']}")
        else:
            print(f"  {symbol}: {result.get('market', 'N/A')} -> {result.get('report_path', 'N/A')}")
    print("=" * 60)

if __name__ == "__main__":
    main()
