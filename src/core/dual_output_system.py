"""
双输出系统 - 同时生成JSON数据和可视化图表
确保两套输出基于同一数据源和计算逻辑
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

from .data_processing_engine import DataProcessingEngine
from .json_data_generator import JSONDataGenerator
from ..report_generator.chart_generator import ChartGenerator
from .consistency_validator import ConsistencyValidator


class DualOutputSystem:
    """双输出系统（JSON + 图表）"""
    
    def __init__(self, config: Dict = None):
        """
        初始化双输出系统
        
        Args:
            config: 配置字典（可选）
        """
        self.config = config or {}
        self.data_engine = DataProcessingEngine()
        self.json_generator = JSONDataGenerator(
            precision_price=self.config.get('ai_data', {}).get('precision', {}).get('price', 4),
            precision_indicator=self.config.get('ai_data', {}).get('precision', {}).get('indicator', 4)
        )
        self.chart_generator = ChartGenerator()
        self.validator = ConsistencyValidator()
    
    def process_stock(
        self,
        data: pd.DataFrame,
        symbol: str,
        market: str = "A股",
        index_data: Optional[pd.DataFrame] = None,
        output_base_dir: str = "outputs"
    ) -> Dict:
        """
        处理单只股票，生成JSON和图表
        
        Args:
            data: 原始日线数据
            symbol: 股票代码
            market: 市场类型
            index_data: 指数数据（可选）
            output_base_dir: 输出基础目录
        
        Returns:
            处理结果字典
        """
        results = {
            'symbol': symbol,
            'json_files': {},
            'chart_files': {},
            'validation': {}
        }
        
        # 1. 数据处理：生成多周期K线和指标
        print(f"\n处理 {symbol} 数据...")
        timeframes = self.config.get('data_processing', {}).get('timeframes', 
            ['monthly', 'weekly', 'daily', '60min', '30min', '5min'])
        
        processed_data = self.data_engine.process_stock_data(data, symbol, timeframes)
        
        # 处理指数数据（如果有）
        processed_index_data = None
        if index_data is not None:
            processed_index_data = {}
            for tf in timeframes:
                tf_index = self.data_engine.convert_to_timeframe(index_data, tf)
                if not tf_index.empty:
                    processed_index_data[tf] = tf_index
        
        # 2. 生成JSON文件
        print(f"生成 {symbol} 的JSON数据...")
        json_dir = os.path.join(output_base_dir, 'ai_data_output')
        json_files = self.json_generator.generate_stock_json_files(
            processed_data,
            symbol,
            json_dir,
            processed_index_data
        )
        results['json_files'] = json_files
        
        # 3. 生成图表文件
        print(f"生成 {symbol} 的图表...")
        chart_dir = os.path.join(output_base_dir, 'chart_output')
        chart_files = self._generate_charts(
            processed_data,
            symbol,
            market,
            chart_dir
        )
        results['chart_files'] = chart_files
        
        # 4. 一致性验证
        print(f"验证 {symbol} 的数据一致性...")
        validation_results = {}
        for timeframe, tf_data in processed_data.items():
            if timeframe in json_files and not tf_data.empty:
                # 读取JSON文件
                json_file = json_files[timeframe]
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # 验证一致性
                validation = self.validator.validate_json_vs_dataframe(json_data, tf_data)
                validation_results[timeframe] = validation
        
        results['validation'] = validation_results
        
        return results
    
    def _generate_charts(
        self,
        processed_data: Dict[str, pd.DataFrame],
        symbol: str,
        market: str,
        chart_dir: str
    ) -> Dict[str, str]:
        """生成图表文件"""
        files = {}
        
        # 创建股票目录
        stock_chart_dir = os.path.join(chart_dir, symbol.replace('.', '_'))
        os.makedirs(stock_chart_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 生成日线图（核心图表）
        if 'daily' in processed_data and not processed_data['daily'].empty:
            daily_path = os.path.join(stock_chart_dir, f"daily_chart_{timestamp}.png")
            self.chart_generator.generate_kline_chart(
                processed_data['daily'],
                symbol,
                market,
                daily_path,
                days=20
            )
            files['daily'] = daily_path
        
        # 生成其他周期图表
        for timeframe in ['weekly', 'monthly', '60min', '30min', '5min']:
            if timeframe in processed_data and not processed_data[timeframe].empty:
                tf_path = os.path.join(stock_chart_dir, f"{timeframe}_chart_{timestamp}.png")
                # 对于非日线，使用全部数据
                days = len(processed_data[timeframe])
                self.chart_generator.generate_kline_chart(
                    processed_data[timeframe],
                    symbol,
                    market,
                    tf_path,
                    days=min(days, 100)
                )
                files[timeframe] = tf_path
        
        # 生成综合仪表盘（如果有日线数据）
        if 'daily' in processed_data and not processed_data['daily'].empty:
            dashboard_path = os.path.join(stock_chart_dir, f"overview_dashboard_{timestamp}.png")
            self._generate_dashboard(processed_data, symbol, market, dashboard_path)
            files['dashboard'] = dashboard_path
        
        return files
    
    def _generate_dashboard(
        self,
        processed_data: Dict[str, pd.DataFrame],
        symbol: str,
        market: str,
        save_path: str
    ):
        """生成综合仪表盘"""
        # 简化版仪表盘：使用日线数据
        if 'daily' not in processed_data or processed_data['daily'].empty:
            return
        
        data = processed_data['daily'].tail(20)
        self.chart_generator.generate_kline_chart(data, symbol, market, save_path, days=20)
    
    def batch_process(
        self,
        stocks_data: Dict[str, pd.DataFrame],
        market: str = "A股",
        indices_data: Optional[Dict[str, pd.DataFrame]] = None,
        output_base_dir: str = "outputs"
    ) -> Dict:
        """
        批量处理多只股票
        
        Args:
            stocks_data: 股票数据字典（key为股票代码）
            market: 市场类型
            indices_data: 指数数据字典（可选）
            output_base_dir: 输出基础目录
        
        Returns:
            处理结果字典
        """
        all_results = {}
        validation_all = {}
        
        for symbol, data in stocks_data.items():
            index_data = indices_data.get(symbol) if indices_data else None
            result = self.process_stock(data, symbol, market, index_data, output_base_dir)
            all_results[symbol] = result
            validation_all[symbol] = result['validation']
        
        # 生成一致性验证报告
        report_path = os.path.join(output_base_dir, 'consistency_report.txt')
        report = self.validator.generate_consistency_report(validation_all)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n✅ 一致性验证报告已生成: {report_path}")
        
        return all_results
