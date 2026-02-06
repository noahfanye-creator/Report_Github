"""
PDF报告生成器 - 生成包含图表和K线图的技术分析报告
"""
from datetime import datetime
from typing import Dict, List, Optional
import os

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

import pandas as pd


class PDFReportGenerator:
    """PDF技术分析报告生成器"""
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab未安装，请运行: pip install reportlab")
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """设置自定义样式"""
        # 标题样式
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=1  # 居中
        )
        
        # 小节标题
        self.section_style = ParagraphStyle(
            'SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#3498DB'),
            spaceBefore=20,
            spaceAfter=10
        )
        
        # 正文样式
        self.normal_style = ParagraphStyle(
            'NormalStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            spaceAfter=12
        )
    
    def generate_report(
        self,
        data: pd.DataFrame,
        symbol: str,
        market: str,
        charts: Dict[str, str],
        output_path: str = "technical_analysis_report.pdf"
    ) -> str:
        """
        生成完整的PDF技术分析报告
        
        Args:
            data: 股票数据DataFrame
            symbol: 股票代码
            market: 市场类型
            charts: 图表文件路径字典 {'kline': 'path', 'indicators': 'path', ...}
            output_path: 输出PDF路径
        
        Returns:
            生成的PDF文件路径
        """
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        # 创建PDF文档
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        # 1. 封面页
        story.extend(self._create_cover_page(data, symbol, market))
        story.append(PageBreak())
        
        # 2. 数据摘要
        story.extend(self._create_summary_section(data, symbol, market))
        story.append(PageBreak())
        
        # 3. K线图
        if 'kline' in charts:
            story.extend(self._create_chart_section("K线图与技术指标", charts['kline']))
        
        # 4. 技术指标图表
        if 'indicators' in charts:
            story.extend(self._create_chart_section("技术指标分析", charts['indicators']))
        
        # 5. 数据表格
        story.append(PageBreak())
        story.extend(self._create_data_table_section(data))
        
        # 生成PDF
        doc.build(story)
        print(f"✅ PDF报告已生成: {output_path}")
        
        return output_path
    
    def _create_cover_page(self, data: pd.DataFrame, symbol: str, market: str) -> List:
        """创建封面页"""
        elements = []
        
        # 标题
        title = Paragraph("股票技术分析报告", self.title_style)
        elements.append(Spacer(1, 2*inch))
        elements.append(title)
        elements.append(Spacer(1, 0.5*inch))
        
        # 股票信息
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#34495E'),
            alignment=1,
            spaceAfter=20
        )
        
        info_text = f"""
        <b>股票代码:</b> {symbol}<br/>
        <b>市场类型:</b> {market}<br/>
        <b>数据范围:</b> {data.index[0].strftime('%Y-%m-%d')} 至 {data.index[-1].strftime('%Y-%m-%d')}<br/>
        <b>数据条数:</b> {len(data)}<br/>
        <b>生成时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        elements.append(Paragraph(info_text, info_style))
        elements.append(Spacer(1, 0.5*inch))
        
        # 最新价格信息
        latest = data.iloc[-1]
        price_info = f"""
        <b>最新收盘价:</b> {latest['close']:.2f}<br/>
        <b>涨跌幅:</b> {latest.get('pct_change', 0):.2f}%<br/>
        <b>成交量:</b> {latest['volume']:,.0f}
        """
        elements.append(Paragraph(price_info, info_style))
        elements.append(Spacer(1, 1*inch))
        
        # 免责声明
        disclaimer_style = ParagraphStyle(
            'DisclaimerStyle',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1,
            spaceBefore=20
        )
        disclaimer = "注: 本报告基于模拟数据生成，仅用于演示和测试目的。实际投资请使用真实市场数据。"
        elements.append(Paragraph(disclaimer, disclaimer_style))
        
        return elements
    
    def _create_summary_section(self, data: pd.DataFrame, symbol: str, market: str) -> List:
        """创建数据摘要部分"""
        elements = []
        
        # 章节标题
        elements.append(Paragraph("一、数据摘要", self.section_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # 最新数据
        latest = data.iloc[-1]
        summary_data = [
            ['项目', '数值'],
            ['最新收盘价', f"{latest['close']:.2f}"],
            ['最新开盘价', f"{latest['open']:.2f}"],
            ['最高价', f"{latest['high']:.2f}"],
            ['最低价', f"{latest['low']:.2f}"],
            ['涨跌幅', f"{latest.get('pct_change', 0):.2f}%"],
            ['成交量', f"{latest['volume']:,.0f}"],
            ['成交额', f"{latest.get('amount', 0):,.0f}"],
        ]
        
        # 技术指标
        if 'MA5' in data.columns:
            summary_data.append(['MA5', f"{latest['MA5']:.2f}"])
        if 'MA20' in data.columns:
            summary_data.append(['MA20', f"{latest['MA20']:.2f}"])
        if 'MA60' in data.columns:
            summary_data.append(['MA60', f"{latest['MA60']:.2f}"])
        if 'RSI' in data.columns:
            summary_data.append(['RSI(14)', f"{latest['RSI']:.1f}"])
        
        table = Table(summary_data, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # 价格统计
        elements.append(Paragraph("二、价格统计", self.section_style))
        elements.append(Spacer(1, 0.2*inch))
        
        stats_data = [
            ['统计项', '数值'],
            ['最高价', f"{data['high'].max():.2f}"],
            ['最低价', f"{data['low'].min():.2f}"],
            ['平均价', f"{data['close'].mean():.2f}"],
            ['波动率', f"{data['pct_change'].std():.2f}%"],
            ['最大涨幅', f"{data['pct_change'].max():.2f}%"],
            ['最大跌幅', f"{data['pct_change'].min():.2f}%"],
        ]
        
        stats_table = Table(stats_data, colWidths=[2*inch, 3*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E74C3C')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        elements.append(stats_table)
        
        return elements
    
    def _create_chart_section(self, title: str, chart_path: str) -> List:
        """创建图表部分"""
        elements = []
        
        if not os.path.exists(chart_path):
            elements.append(Paragraph(f"{title} - 图表文件不存在: {chart_path}", self.normal_style))
            return elements
        
        elements.append(Paragraph(title, self.section_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # 添加图表
        img = Image(chart_path, width=6*inch, height=4*inch)
        elements.append(img)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_data_table_section(self, data: pd.DataFrame) -> List:
        """创建数据表格部分"""
        elements = []
        
        elements.append(Paragraph("三、历史数据", self.section_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # 只显示最近20条数据
        display_data = data.tail(20).copy()
        
        # 准备表格数据
        table_data = [['日期', '开盘', '最高', '最低', '收盘', '成交量', '涨跌幅']]
        
        for idx, row in display_data.iterrows():
            table_data.append([
                idx.strftime('%Y-%m-%d'),
                f"{row['open']:.2f}",
                f"{row['high']:.2f}",
                f"{row['low']:.2f}",
                f"{row['close']:.2f}",
                f"{row['volume']:,.0f}",
                f"{row.get('pct_change', 0):.2f}%"
            ])
        
        table = Table(table_data, colWidths=[1*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27AE60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        elements.append(table)
        
        return elements
