# 股票技术分析报告系统

## 项目结构

```
Report_gener/
├── main.py                 # 主入口
├── requirements.txt
├── config/                 # 配置
│   ├── config.yaml
│   ├── market_rules.yaml
│   ├── indicators_config.yaml
│   └── capital_flow_config.yaml
├── src/
│   ├── core/               # 核心编排
│   │   ├── main.py         # StockAnalysisSystem
│   │   ├── hk_pipeline.py  # 港股分析流水线
│   │   └── multi_market_analysis_system.py
│   ├── data_sources/       # 数据源
│   │   └── unified_market_data.py
│   ├── market_detector/    # 市场检测（待扩展）
│   ├── indicators/         # 技术指标
│   │   ├── calculator.py
│   │   ├── hk_indicator_calculator.py
│   │   └── formulas/
│   ├── visualizer/         # 图表
│   │   └── multi_market_chart_renderer.py
│   ├── report_generator/   # 报告（待扩展）
│   ├── utils/
│   │   └── data_validator.py
│   ├── capital_flow/       # 资金面模块
│   └── models/
└── outputs/
    ├── reports/
    ├── charts/
    ├── json_data/
    └── logs/
```

## 使用

```bash
pip install -r requirements.txt
python main.py
# 输入股票代码，如 00700（港股）、600519.SH（A股，待支持）
```

## 说明

- 当前支持 **港股** 分析；A 股流水线尚未接入。
- 配置与规范参见 `config/` 及项目说明文档。
