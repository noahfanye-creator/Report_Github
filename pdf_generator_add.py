# 修改 src/report/pdf_generator.py
class EnhancedPDFGenerator(PDFGenerator):
    """增强版PDF生成器（包含资金面章节）"""
    
    def _add_capital_flow_section(self, story, analysis_data):
        """添加资金面分析章节"""
        # 获取资金面分析器
        capital_analyzer = CapitalFlowAnalyzer()
        
        # 生成资金面分析
        capital_analysis = capital_analyzer.analyze(analysis_data['capital_flow'])
        
        # 生成章节内容
        section_generator = CapitalFlowReportSection()
        section_content = section_generator.generate_section(
            symbol=analysis_data['symbol'],
            market_type=analysis_data['market'],
            analysis_data=capital_analysis
        )
        
        # 添加到报告
        story.append(Paragraph("第四章：资金面分析", self.section_style))
        story.append(section_content)
        
        # 添加资金面图表
        chart_generator = CapitalFlowChartGenerator()
        charts = chart_generator.generate_charts(capital_analysis)
        
        for chart in charts:
            story.append(Image(chart, width=6*inch, height=4*inch))
            story.append(Spacer(1, 10))