"""
数据一致性验证器 - 验证JSON数据和图表数据的一致性
"""
from typing import Dict, List, Tuple
import json
import pandas as pd
import numpy as np


class ConsistencyValidator:
    """数据一致性验证器"""
    
    def __init__(self, tolerance: float = 0.0001):
        """
        初始化验证器
        
        Args:
            tolerance: 允许的误差范围（0.01% = 0.0001）
        """
        self.tolerance = tolerance
    
    def validate_json_vs_dataframe(
        self,
        json_data: Dict,
        dataframe: pd.DataFrame
    ) -> Dict[str, bool]:
        """
        验证JSON数据与DataFrame数据的一致性
        
        Args:
            json_data: JSON数据字典
            dataframe: DataFrame数据
        
        Returns:
            验证结果字典
        """
        results = {
            'ohlcv_match': True,
            'indicators_match': True,
            'timestamp_match': True,
            'errors': []
        }
        
        if len(json_data['kline_data']) != len(dataframe):
            results['errors'].append(f"数据条数不匹配: JSON={len(json_data['kline_data'])}, DataFrame={len(dataframe)}")
            results['ohlcv_match'] = False
            return results
        
        # 验证每条数据
        for i, json_item in enumerate(json_data['kline_data']):
            df_row = dataframe.iloc[i]
            
            # 验证时间戳
            json_timestamp = pd.to_datetime(json_item['timestamp'])
            if abs((json_timestamp - dataframe.index[i]).total_seconds()) > 1:
                results['errors'].append(f"第{i}条时间戳不匹配")
                results['timestamp_match'] = False
            
            # 验证OHLCV
            json_ohlcv = json_item['ohlcv']
            if not self._compare_values(json_ohlcv[0], df_row['open'], 'open', i, results):
                results['ohlcv_match'] = False
            if not self._compare_values(json_ohlcv[1], df_row['high'], 'high', i, results):
                results['ohlcv_match'] = False
            if not self._compare_values(json_ohlcv[2], df_row['low'], 'low', i, results):
                results['ohlcv_match'] = False
            if not self._compare_values(json_ohlcv[3], df_row['close'], 'close', i, results):
                results['ohlcv_match'] = False
            if not self._compare_values(json_ohlcv[4], df_row['volume'], 'volume', i, results):
                results['ohlcv_match'] = False
            
            # 验证技术指标
            if 'indicators' in json_item:
                indicators = json_item['indicators']
                
                # MA指标
                if 'MA' in indicators:
                    if 'MA5' in indicators['MA']:
                        if 'MA5' in dataframe.columns:
                            if not self._compare_values(
                                indicators['MA']['MA5'], 
                                df_row['MA5'], 
                                'MA5', i, results
                            ):
                                results['indicators_match'] = False
                
                # MACD指标
                if 'MACD' in indicators:
                    if 'MACD_DIF' in dataframe.columns:
                        if not self._compare_values(
                            indicators['MACD']['DIF'],
                            df_row['MACD_DIF'],
                            'MACD_DIF', i, results
                        ):
                            results['indicators_match'] = False
                
                # RSI指标
                if 'RSI' in indicators:
                    if 'RSI14' in dataframe.columns:
                        if not self._compare_values(
                            indicators['RSI']['RSI14'],
                            df_row['RSI14'],
                            'RSI14', i, results
                        ):
                            results['indicators_match'] = False
        
        return results
    
    def _compare_values(
        self,
        json_value: float,
        df_value: float,
        field_name: str,
        index: int,
        results: Dict
    ) -> bool:
        """比较两个值是否在误差范围内"""
        if pd.isna(df_value):
            if json_value == 0 or json_value is None:
                return True
            else:
                results['errors'].append(f"第{index}条 {field_name}: JSON={json_value}, DataFrame=NaN")
                return False
        
        diff = abs(json_value - df_value)
        relative_diff = diff / abs(df_value) if df_value != 0 else diff
        
        if relative_diff > self.tolerance:
            results['errors'].append(
                f"第{index}条 {field_name}: JSON={json_value}, DataFrame={df_value}, "
                f"差异={relative_diff*100:.4f}%"
            )
            return False
        
        return True
    
    def generate_consistency_report(
        self,
        validation_results: Dict[str, Dict]
    ) -> str:
        """
        生成一致性验证报告
        
        Args:
            validation_results: 验证结果字典（key为股票代码，value为验证结果）
        
        Returns:
            报告文本
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("数据一致性验证报告")
        report_lines.append("=" * 60)
        report_lines.append(f"生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        total_stocks = len(validation_results)
        passed_stocks = 0
        
        for symbol, results in validation_results.items():
            report_lines.append(f"股票: {symbol}")
            report_lines.append("-" * 40)
            
            all_passed = (
                results.get('ohlcv_match', False) and
                results.get('indicators_match', False) and
                results.get('timestamp_match', False)
            )
            
            if all_passed:
                report_lines.append("✅ 所有数据一致性检查通过")
                passed_stocks += 1
            else:
                report_lines.append("❌ 发现不一致项:")
                if not results.get('ohlcv_match', True):
                    report_lines.append("  - OHLCV数据不匹配")
                if not results.get('indicators_match', True):
                    report_lines.append("  - 技术指标数据不匹配")
                if not results.get('timestamp_match', True):
                    report_lines.append("  - 时间戳不匹配")
            
            # 显示错误详情（最多显示前5个）
            errors = results.get('errors', [])
            if errors:
                report_lines.append(f"  错误详情（显示前5个）:")
                for error in errors[:5]:
                    report_lines.append(f"    - {error}")
                if len(errors) > 5:
                    report_lines.append(f"    ... 还有 {len(errors) - 5} 个错误")
            
            report_lines.append("")
        
        # 总结
        report_lines.append("=" * 60)
        report_lines.append("验证总结")
        report_lines.append("=" * 60)
        report_lines.append(f"总股票数: {total_stocks}")
        report_lines.append(f"通过验证: {passed_stocks}")
        report_lines.append(f"未通过: {total_stocks - passed_stocks}")
        report_lines.append(f"通过率: {passed_stocks/total_stocks*100:.1f}%")
        
        return "\n".join(report_lines)
