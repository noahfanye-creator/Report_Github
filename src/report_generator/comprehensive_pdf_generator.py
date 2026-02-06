"""
综合PDF报告生成器 - 整合所有图表到PDF文档中
"""
from datetime import datetime
from typing import Dict, List, Optional
import os
import json

try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

import pandas as pd
import numpy as np
import platform


class ComprehensivePDFGenerator:
    """综合PDF报告生成器（包含所有图表）"""
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab未安装，请运行: pip install reportlab")
        
        # 注册中文字体
        self._register_chinese_fonts()
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _register_chinese_fonts(self):
        """注册中文字体"""
        system = platform.system()
        chinese_font_name = None
        
        if system == 'Darwin':  # macOS
            font_configs = [
                ('/System/Library/Fonts/Supplemental/PingFang.ttc', 'PingFangSC-Regular', 0),
                ('/System/Library/Fonts/STHeiti Light.ttc', 'STHeiti', 0),
                ('/Library/Fonts/Arial Unicode.ttf', 'ArialUnicodeMS', 0),
            ]
        elif system == 'Windows':
            font_configs = [
                ('C:/Windows/Fonts/simsun.ttc', 'SimSun', 0),
                ('C:/Windows/Fonts/simhei.ttf', 'SimHei', 0),
                ('C:/Windows/Fonts/msyh.ttc', 'MicrosoftYaHei', 0),
            ]
        else:  # Linux
            font_configs = [
                ('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 'WQY', 0),
                ('/usr/share/fonts/truetype/arphic/uming.ttc', 'ARPLUMing', 0),
            ]
        
        for font_path, font_name, font_index in font_configs:
            try:
                if os.path.exists(font_path):
                    if font_path.endswith('.ttc'):
                        try:
                            pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=font_index))
                            chinese_font_name = font_name
                            print(f"✅ 已注册中文字体: {font_name}")
                            break
                        except:
                            try:
                                pdfmetrics.registerFont(TTFont(font_name, font_path))
                                chinese_font_name = font_name
                                print(f"✅ 已注册中文字体: {font_name}")
                                break
                            except:
                                continue
                    else:
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                        chinese_font_name = font_name
                        print(f"✅ 已注册中文字体: {font_name}")
                        break
            except:
                continue
        
        if chinese_font_name is None:
            print("⚠️  未找到中文字体文件，将使用Helvetica")
            chinese_font_name = 'Helvetica'
        
        self.chinese_font = chinese_font_name
        self.chinese_font_bold = chinese_font_name
        
        # 尝试注册粗体
        if chinese_font_name != 'Helvetica':
            try:
                if system == 'Darwin':
                    bold_paths = [
                        ('/System/Library/Fonts/STHeiti Medium.ttc', 'STHeiti-Bold', 0),
                    ]
                elif system == 'Windows':
                    bold_paths = [
                        ('C:/Windows/Fonts/simhei.ttf', 'SimHei-Bold', 0),
                    ]
                else:
                    bold_paths = []
                
                for bold_path, bold_name, bold_index in bold_paths:
                    if os.path.exists(bold_path):
                        try:
                            if bold_path.endswith('.ttc'):
                                pdfmetrics.registerFont(TTFont(bold_name, bold_path, subfontIndex=bold_index))
                            else:
                                pdfmetrics.registerFont(TTFont(bold_name, bold_path))
                            self.chinese_font_bold = bold_name
                            print(f"✅ 已注册中文字体粗体: {bold_name}")
                            break
                        except:
                            continue
            except:
                pass
    
    def _setup_custom_styles(self):
        """设置自定义样式"""
        self.title_style = ParagraphStyle(
            'TitleStyle',
            parent=self.styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=20,
            alignment=1,
            fontName=self.chinese_font_bold
        )
        
        self.chapter_style = ParagraphStyle(
            'ChapterStyle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2C3E50'),
            spaceBefore=15,
            spaceAfter=10,
            fontName=self.chinese_font_bold
        )
        
        self.section_style = ParagraphStyle(
            'SectionStyle',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#34495E'),
            spaceBefore=10,
            spaceAfter=8,
            fontName=self.chinese_font_bold
        )
        
        self.normal_style = ParagraphStyle(
            'NormalStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            spaceAfter=6,
            fontName=self.chinese_font
        )
    
    def generate_comprehensive_report(
        self,
        data: pd.DataFrame,
        symbol: str,
        market: str,
        charts: Dict[str, str],
        processed_data: Optional[Dict[str, pd.DataFrame]] = None,
        output_path: str = "comprehensive_report.pdf"
    ) -> str:
        """
        生成综合PDF报告（包含所有图表和数据）
        
        Args:
            data: 日线数据
            symbol: 股票代码
            market: 市场类型
            charts: 图表文件路径字典
            processed_data: 多周期处理后的数据（可选）
            output_path: 输出PDF路径
        
        Returns:
            生成的PDF文件路径
        """
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )
        
        story = []
        
        # 1. 封面页
        story.extend(self._create_cover_page(data, symbol, market))
        story.append(PageBreak())
        
        # 2. 数据摘要
        story.extend(self._create_summary_section(data, symbol, market))
        story.append(PageBreak())
        
        # 3. 日线K线图（核心图表）
        if 'daily' in charts or 'kline' in charts:
            chart_path = charts.get('daily') or charts.get('kline')
            if chart_path and os.path.exists(chart_path):
                story.extend(self._create_chart_page("日线K线图与技术指标", chart_path, landscape_mode=True))
                story.append(PageBreak())
        
        # 4. 多周期K线图
        if processed_data:
            story.extend(self._create_multi_timeframe_charts(processed_data, symbol, market, charts))
        
        # 5. 技术指标图表
        if 'indicators' in charts and os.path.exists(charts['indicators']):
            story.extend(self._create_chart_page("技术指标分析图", charts['indicators']))
            story.append(PageBreak())
        
        # 6. 综合仪表盘（如果有）
        if 'dashboard' in charts and os.path.exists(charts['dashboard']):
            story.extend(self._create_chart_page("综合仪表盘", charts['dashboard'], landscape_mode=True))
            story.append(PageBreak())
        
        # 7. 数据表格章节
        story.extend(self._create_data_tables_section(data, symbol, market))
        story.append(PageBreak())
        
        # 8. 原始数据（JSON格式）
        story.extend(self._create_json_data_section(data, symbol, market))
        
        # 生成PDF
        doc.build(story)
        print(f"✅ 综合PDF报告已生成: {output_path}")
        
        return output_path
    
    def _create_cover_page(self, data: pd.DataFrame, symbol: str, market: str) -> List:
        """创建封面页"""
        elements = []
        
        title = Paragraph("股票技术分析综合报告", self.title_style)
        elements.append(Spacer(1, 1.5*inch))
        elements.append(title)
        elements.append(Spacer(1, 0.5*inch))
        
        latest = data.iloc[-1] if not data.empty else None
        
        info_data = [
            ['股票代码', symbol],
            ['市场类型', market],
            ['数据范围', f"{data.index[0].strftime('%Y-%m-%d')} 至 {data.index[-1].strftime('%Y-%m-%d')}" if not data.empty else 'N/A'],
            ['数据条数', f"{len(data)}"],
            ['生成时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        ]
        
        if latest is not None:
            info_data.extend([
                ['', ''],
                ['最新收盘价', f"{latest['close']:.2f}"],
                ['最新涨跌幅', f"{latest.get('pct_change', 0):.2f}%"],
            ])
        
        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 0.5*inch))
        
        disclaimer = Paragraph(
            "注: 本报告包含完整的技术分析数据和图表<br/>"
            "所有数据均来自模拟数据，仅用于演示和测试目的",
            self.normal_style
        )
        elements.append(disclaimer)
        
        return elements
    
    def _create_summary_section(self, data: pd.DataFrame, symbol: str, market: str) -> List:
        """创建数据摘要部分"""
        elements = []
        
        elements.append(Paragraph("数据摘要", self.chapter_style))
        elements.append(Spacer(1, 0.2*inch))
        
        latest = data.iloc[-1]
        
        summary_data = [
            ['项目', '数值'],
            ['最新收盘价', f"{latest['close']:.2f}"],
            ['最新开盘价', f"{latest['open']:.2f}"],
            ['最高价', f"{latest['high']:.2f}"],
            ['最低价', f"{latest['low']:.2f}"],
            ['涨跌幅', f"{latest.get('pct_change', 0):.2f}%"],
            ['成交量', f"{latest['volume']:,.0f}"],
        ]
        
        if 'MA5' in data.columns:
            summary_data.append(['MA5', f"{latest['MA5']:.2f}"])
        if 'MA20' in data.columns:
            summary_data.append(['MA20', f"{latest['MA20']:.2f}"])
        if 'MA60' in data.columns:
            summary_data.append(['MA60', f"{latest['MA60']:.2f}"])
        if 'RSI' in data.columns or 'RSI14' in data.columns:
            rsi_val = latest.get('RSI') or latest.get('RSI14', 0)
            summary_data.append(['RSI(14)', f"{rsi_val:.1f}"])
        
        table = Table(summary_data, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font_bold),
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_chart_page(
        self,
        title: str,
        chart_path: str,
        landscape_mode: bool = False
    ) -> List:
        """创建图表页面"""
        elements = []
        
        elements.append(Paragraph(title, self.chapter_style))
        elements.append(Spacer(1, 0.2*inch))
        
        if not os.path.exists(chart_path):
            elements.append(Paragraph(f"图表文件不存在: {chart_path}", self.normal_style))
            return elements
        
        try:
            # 根据是否横向模式调整图片大小
            if landscape_mode:
                # 横向模式：图片更大
                img = Image(chart_path, width=10*inch, height=6*inch)
            else:
                # 纵向模式：标准大小
                img = Image(chart_path, width=7*inch, height=5*inch)
            
            elements.append(img)
            elements.append(Spacer(1, 0.2*inch))
        except Exception as e:
            elements.append(Paragraph(f"无法加载图表: {str(e)}", self.normal_style))
        
        return elements
    
    def _create_multi_timeframe_charts(
        self,
        processed_data: Dict[str, pd.DataFrame],
        symbol: str,
        market: str,
        charts: Dict[str, str]
    ) -> List:
        """创建多周期图表页面"""
        elements = []
        
        elements.append(Paragraph("多周期K线图", self.chapter_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # 按优先级显示：日线、周线、月线
        timeframes_order = ['daily', 'weekly', 'monthly', '60min', '30min', '5min']
        timeframe_names = {
            'daily': '日线',
            'weekly': '周线',
            'monthly': '月线',
            '60min': '60分钟线',
            '30min': '30分钟线',
            '5min': '5分钟线'
        }
        
        chart_count = 0
        for timeframe in timeframes_order:
            if timeframe in charts and os.path.exists(charts[timeframe]):
                chart_count += 1
                elements.append(Paragraph(
                    f"{timeframe_names.get(timeframe, timeframe)}K线图",
                    self.section_style
                ))
                elements.append(Spacer(1, 0.1*inch))
                
                try:
                    img = Image(charts[timeframe], width=7*inch, height=5*inch)
                    elements.append(img)
                    elements.append(Spacer(1, 0.3*inch))
                except Exception as e:
                    elements.append(Paragraph(f"无法加载图表: {str(e)}", self.normal_style))
                
                # 每两个图表换页，或者最后一个图表后换页
                if chart_count % 2 == 0 or timeframe == timeframes_order[-1]:
                    elements.append(PageBreak())
        
        return elements
    
    def _create_data_tables_section(
        self,
        data: pd.DataFrame,
        symbol: str,
        market: str
    ) -> List:
        """创建数据表格章节"""
        elements = []
        
        elements.append(Paragraph("历史数据表格", self.chapter_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # 显示最近20条数据
        display_data = data.tail(20).copy()
        
        table_data = [['日期', '开盘', '最高', '最低', '收盘', '成交量', '涨跌幅']]
        
        for idx, row in display_data.iterrows():
            table_data.append([
                idx.strftime('%Y-%m-%d'),
                f"{row['open']:.2f}",
                f"{row['high']:.2f}",
                f"{row['low']:.2f}",
                f"{row['close']:.2f}",
                f"{row['volume']:,.0f}",
                f"{row.get('pct_change', 0):+.2f}%"
            ])
        
        table = Table(table_data, colWidths=[1*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27AE60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font_bold),
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_json_data_section(
        self,
        data: pd.DataFrame,
        symbol: str,
        market: str
    ) -> List:
        """创建JSON数据部分"""
        elements = []
        
        elements.append(Paragraph("原始数据（JSON格式）", self.chapter_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # 生成简化的JSON数据
        json_data = {
            "metadata": {
                "symbol": symbol,
                "market": market,
                "data_points": len(data),
                "period": [
                    data.index[0].strftime('%Y-%m-%d') if len(data) > 0 else None,
                    data.index[-1].strftime('%Y-%m-%d') if len(data) > 0 else None
                ]
            },
            "sample_data": []
        }
        
        # 只包含最近5条数据作为示例
        for idx, row in data.tail(5).iterrows():
            json_data["sample_data"].append({
                "date": idx.strftime('%Y-%m-%d'),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": int(row['volume'])
            })
        
        json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
        
        from reportlab.platypus import Preformatted
        json_text = Preformatted(json_str, self.normal_style, maxLineLength=80)
        elements.append(json_text)
        
        return elements
