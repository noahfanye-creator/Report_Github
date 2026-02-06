class MultiMarketAnalysisSystem:
    """
    多市场分析系统
    统一管理A股、港股分析
    """
    
    def __init__(self):
        self.data_system = UnifiedMarketDataSystem()
        self.market_pipelines = {}
        
        # 注册不同市场的分析流水线
        self.pipeline_classes = {
            '港股': HKEnhancedDataPipeline,
            'A股': CompleteDataPreparationPipeline  # 之前定义的A股流水线
        }
    
    def analyze_stock(self, 
                     symbol: str, 
                     market: str = None,
                     start_date: str = '2025-01-01',
                     end_date: str = '2026-01-26',
                     **kwargs) -> Dict:
        """
        分析指定股票
        
        :param symbol: 股票代码
        :param market: 市场类型
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param kwargs: 其他参数传递给流水线
        :return: 分析结果
        """
        # 自动检测市场
        if market is None:
            market = self.data_system.detect_market(symbol)
        
        print(f"开始分析 {market} 股票: {symbol}")
        
        # 获取对应的流水线
        pipeline_class = self.pipeline_classes.get(market)
        if pipeline_class is None:
            raise ValueError(f"不支持的市场类型: {market}")
        
        # 创建并运行流水线
        pipeline = pipeline_class(symbol)
        result = pipeline.run_complete_analysis(
            start_date=start_date,
            end_date=end_date,
            **kwargs
        )
        
        # 存储结果
        self.market_pipelines[symbol] = pipeline
        
        return result
    
    def analyze_multiple_stocks(self, 
                              stock_list: List[Tuple[str, str]],
                              start_date: str,
                              end_date: str) -> Dict:
        """
        批量分析多只股票
        
        :param stock_list: 股票列表 [(代码, 市场), ...]
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 分析结果字典
        """
        results = {}
        
        for symbol, market in stock_list:
            try:
                result = self.analyze_stock(
                    symbol=symbol,
                    market=market,
                    start_date=start_date,
                    end_date=end_date
                )
                results[symbol] = result
                
            except Exception as e:
                print(f"分析 {symbol} 失败: {e}")
                results[symbol] = {'error': str(e)}
        
        return results
    
    def compare_markets(self, 
                       hk_symbols: List[str],
                       a_symbols: List[str],
                       start_date: str,
                       end_date: str) -> Dict:
        """
        对比港股和A股市场
        
        :param hk_symbols: 港股代码列表
        :param a_symbols: A股代码列表
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 对比分析结果
        """
        # 分析所有股票
        all_stocks = [(s, '港股') for s in hk_symbols] + [(s, 'A股') for s in a_symbols]
        
        results = self.analyze_multiple_stocks(all_stocks, start_date, end_date)
        
        # 生成对比报告
        comparison_report = self._generate_market_comparison_report(results)
        
        return {
            'individual_results': results,
            'comparison_report': comparison_report
        }
    
    def _generate_market_comparison_report(self, results: Dict) -> Dict:
        """生成市场对比报告"""
        report = {
            '港股': {'count': 0, 'avg_volatility': 0, 'avg_return': 0, 'stocks': []},
            'A股': {'count': 0, 'avg_volatility': 0, 'avg_return': 0, 'stocks': []}
        }
        
        hk_volatilities = []
        hk_returns = []
        a_volatilities = []
        a_returns = []
        
        for symbol, result in results.items():
            if 'error' in result:
                continue
            
            market = result.get('market', '未知')
            
            if market in report:
                report[market]['count'] += 1
                report[market]['stocks'].append(symbol)
                
                # 收集波动率和收益率数据
                volatility = result.get('market_characteristics', {}).get('volatility', {}).get('daily_vol', 0)
                returns = result.get('price_data', [{}])[-1].get('pct_change', 0) if result.get('price_data') else 0
                
                if market == '港股':
                    hk_volatilities.append(volatility)
                    hk_returns.append(returns)
                elif market == 'A股':
                    a_volatilities.append(volatility)
                    a_returns.append(returns)
        
        # 计算平均值
        if hk_volatilities:
            report['港股']['avg_volatility'] = np.mean(hk_volatilities)
            report['港股']['avg_return'] = np.mean(hk_returns)
        
        if a_volatilities:
            report['A股']['avg_volatility'] = np.mean(a_volatilities)
            report['A股']['avg_return'] = np.mean(a_returns)
        
        return report