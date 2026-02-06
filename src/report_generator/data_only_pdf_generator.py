"""
纯数据PDF报告生成器 - 根据data.11要求
只呈现数据，不做分析解读，所有结论由AI基于数据自行分析得出
"""
from datetime import datetime
from typing import Dict, List, Optional
import os
import json

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, Preformatted
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


class DataOnlyPDFGenerator:
    """纯数据PDF报告生成器（无分析解读）"""
    
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
            # 尝试注册macOS系统字体（PingFang在Supplemental目录）
            font_configs = [
                ('/System/Library/Fonts/Supplemental/PingFang.ttc', 'PingFangSC-Regular', 0),  # PingFang SC Regular
                ('/System/Library/Fonts/Supplemental/PingFang.ttc', 'PingFangSC-Regular', 1),  # 尝试不同索引
                ('/System/Library/Fonts/STHeiti Light.ttc', 'STHeiti', 0),
                ('/Library/Fonts/Arial Unicode.ttf', 'ArialUnicodeMS', 0),
                ('/System/Library/Fonts/PingFang.ttc', 'PingFangSC-Regular', 0),  # 旧路径
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
        
        # 尝试注册字体
        for font_path, font_name, font_index in font_configs:
            try:
                if os.path.exists(font_path):
                    # 对于TTC文件，可能需要指定字体索引
                    if font_path.endswith('.ttc'):
                        # TTC文件包含多个字体，尝试不同的索引
                        try:
                            pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=font_index))
                            chinese_font_name = font_name
                            print(f"✅ 已注册中文字体: {font_name} ({font_path}, index={font_index})")
                            break
                        except:
                            # 如果指定索引失败，尝试不指定索引
                            try:
                                pdfmetrics.registerFont(TTFont(font_name, font_path))
                                chinese_font_name = font_name
                                print(f"✅ 已注册中文字体: {font_name} ({font_path})")
                                break
                            except Exception as e:
                                continue
                    else:
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                        chinese_font_name = font_name
                        print(f"✅ 已注册中文字体: {font_name} ({font_path})")
                        break
            except Exception as e:
                continue
        
        # 如果系统字体都不可用，使用fallback
        if chinese_font_name is None:
            print("⚠️  未找到中文字体文件，将使用Helvetica（中文可能显示为方框）")
            print("   建议：安装中文字体或使用支持中文的字体文件")
            chinese_font_name = 'Helvetica'
        
        self.chinese_font = chinese_font_name
        self.chinese_font_bold = chinese_font_name  # 暂时使用相同字体，后续可以注册粗体版本
        
        # 尝试注册粗体版本
        if chinese_font_name != 'Helvetica':
            try:
                if system == 'Darwin':
                    bold_configs = [
                        ('/System/Library/Fonts/Supplemental/PingFang.ttc', 'PingFangSC-Bold', 2),  # PingFang Bold索引
                        ('/System/Library/Fonts/STHeiti Medium.ttc', 'STHeiti-Bold', 0),
                    ]
                elif system == 'Windows':
                    bold_configs = [
                        ('C:/Windows/Fonts/simhei.ttf', 'SimHei-Bold', 0),
                        ('C:/Windows/Fonts/msyhbd.ttc', 'MicrosoftYaHei-Bold', 0),
                    ]
                else:
                    bold_configs = []
                
                for bold_path, bold_name, bold_index in bold_configs:
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
        """设置自定义样式（使用中文字体）"""
        # 标题样式
        self.title_style = ParagraphStyle(
            'TitleStyle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=20,
            alignment=1,  # 居中
            fontName=self.chinese_font_bold
        )
        
        # 章节标题
        self.chapter_style = ParagraphStyle(
            'ChapterStyle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2C3E50'),
            spaceBefore=15,
            spaceAfter=10,
            fontName=self.chinese_font_bold
        )
        
        # 小节标题
        self.section_style = ParagraphStyle(
            'SectionStyle',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#34495E'),
            spaceBefore=10,
            spaceAfter=8,
            fontName=self.chinese_font_bold
        )
        
        # 正文样式
        self.normal_style = ParagraphStyle(
            'NormalStyle',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            spaceAfter=6,
            fontName=self.chinese_font
        )
        
        # 数据样式
        self.data_style = ParagraphStyle(
            'DataStyle',
            parent=self.styles['Normal'],
            fontSize=8,
            fontName='Courier',  # 数据使用等宽字体
            textColor=colors.black
        )
    
    def generate_report(
        self,
        data: pd.DataFrame,
        symbol: str,
        market: str,
        charts: Dict[str, str] = None,
        output_path: str = "data_report.pdf"
    ) -> str:
        """
        生成纯数据PDF报告
        
        Args:
            data: 股票数据DataFrame
            symbol: 股票代码
            market: 市场类型
            charts: 图表文件路径字典
            output_path: 输出PDF路径
        
        Returns:
            生成的PDF文件路径
        """
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        
        story = []
        
        # 1. 封面页
        story.extend(self._create_cover_page(data, symbol, market))
        story.append(PageBreak())
        
        # 2. 数据摘要表
        story.extend(self._create_summary_table(data, symbol, market))
        story.append(PageBreak())
        
        # 3. 第一章：技术指标数据表
        story.extend(self._create_technical_indicators_chapter(data))
        story.append(PageBreak())
        
        # 4. 第二章：资金面数据表（如果有）
        story.extend(self._create_capital_flow_chapter(data, symbol))
        story.append(PageBreak())
        
        # 5. 第三章：价格与成交量数据
        story.extend(self._create_price_volume_chapter(data))
        story.append(PageBreak())
        
        # 6. 第四章：多时间框架数据对比
        story.extend(self._create_multi_timeframe_chapter(data))
        story.append(PageBreak())
        
        # 7. 第五章：原始数据片段（JSON格式）
        story.extend(self._create_raw_data_chapter(data, symbol, market))
        story.append(PageBreak())
        
        # 8. 附录：图表文件清单
        story.extend(self._create_charts_appendix(charts or {}))
        
        # 生成PDF
        doc.build(story)
        print(f"✅ 纯数据PDF报告已生成: {output_path}")
        
        return output_path
    
    def _create_cover_page(self, data: pd.DataFrame, symbol: str, market: str) -> List:
        """创建封面页（交易状态信息）"""
        elements = []
        
        # 标题
        title = Paragraph("技术分析数据报告<br/>纯数据版本 v1.0", self.title_style)
        elements.append(Spacer(1, 1*inch))
        elements.append(title)
        elements.append(Spacer(1, 0.5*inch))
        
        # 基础信息
        latest = data.iloc[-1]
        info_data = [
            ['【基础信息】', ''],
            ['股票代码', f"{symbol}"],
            ['市场类型', f"{market}"],
            ['报告类型', '实时交易数据报告'],
            ['数据截止', data.index[-1].strftime('%Y-%m-%d %H:%M:%S')],
            ['报告生成', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['', ''],
            ['【当日数据】', ''],
            ['当前价格', f"{latest['close']:.2f}"],
            ['价格变动', f"{latest.get('pct_change', 0):.2f}%"],
            ['今日开盘', f"{latest['open']:.2f}"],
            ['今日最高', f"{latest['high']:.2f}"],
            ['今日最低', f"{latest['low']:.2f}"],
            ['成交数量', f"{latest['volume']:,.0f}"],
            ['成交金额', f"{latest.get('amount', 0)/100000000:.2f} 亿元" if 'amount' in latest else 'N/A'],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font_bold),
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),  # 表格内容使用中文字体
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # 免责声明
        disclaimer = Paragraph(
            "注: 本报告仅提供原始数据，不包含任何分析解读<br/>"
            "所有数据均来自公开市场，可能存在延迟",
            self.normal_style
        )
        elements.append(disclaimer)
        
        return elements
    
    def _create_summary_table(self, data: pd.DataFrame, symbol: str, market: str) -> List:
        """创建数据摘要表"""
        elements = []
        
        elements.append(Paragraph("关键数据摘要表", self.chapter_style))
        elements.append(Spacer(1, 0.2*inch))
        
        latest = data.iloc[-1]
        
        # 技术指标数据
        tech_data = [['指标类别', '指标名称', '数值', '参数', '更新时间']]
        
        if 'MA5' in data.columns:
            tech_data.append(['趋势指标', 'MA5', f"{latest['MA5']:.2f}", '5日', data.index[-1].strftime('%H:%M:%S')])
        if 'MA20' in data.columns:
            tech_data.append(['趋势指标', 'MA20', f"{latest['MA20']:.2f}", '20日', data.index[-1].strftime('%H:%M:%S')])
        if 'MA60' in data.columns:
            tech_data.append(['趋势指标', 'MA60', f"{latest['MA60']:.2f}", '60日', data.index[-1].strftime('%H:%M:%S')])
        if 'MACD' in data.columns:
            tech_data.append(['趋势指标', 'MACD', f"{latest['MACD']:.2f}", '12,26,9', data.index[-1].strftime('%H:%M:%S')])
        if 'RSI' in data.columns:
            tech_data.append(['动量指标', 'RSI(14)', f"{latest['RSI']:.1f}", '14日', data.index[-1].strftime('%H:%M:%S')])
        
        tech_table = Table(tech_data, colWidths=[1*inch, 1*inch, 1*inch, 0.8*inch, 1*inch])
        tech_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font_bold),
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),  # 表格内容使用中文字体
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        elements.append(Paragraph("【技术指标数据】", self.section_style))
        elements.append(tech_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # 价格统计
        price_stats = [['统计周期', '最高价', '最低价', '平均价', '波动率']]
        
        # 5日统计
        recent_5 = data.tail(5)
        price_stats.append([
            '日线(5日)',
            f"{recent_5['high'].max():.2f}",
            f"{recent_5['low'].min():.2f}",
            f"{recent_5['close'].mean():.2f}",
            f"{recent_5['pct_change'].std():.2f}%"
        ])
        
        # 20日统计
        recent_20 = data.tail(20)
        price_stats.append([
            '日线(20日)',
            f"{recent_20['high'].max():.2f}",
            f"{recent_20['low'].min():.2f}",
            f"{recent_20['close'].mean():.2f}",
            f"{recent_20['pct_change'].std():.2f}%"
        ])
        
        stats_table = Table(price_stats, colWidths=[1.2*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E74C3C')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font_bold),
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),  # 表格内容使用中文字体
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        elements.append(Paragraph("【价格统计】", self.section_style))
        elements.append(stats_table)
        
        return elements
    
    def _create_technical_indicators_chapter(self, data: pd.DataFrame) -> List:
        """第一章：完整技术指标数据表"""
        elements = []
        
        elements.append(Paragraph("第一章：技术指标数据（日线级别）", self.chapter_style))
        elements.append(Spacer(1, 0.2*inch))
        
        latest = data.iloc[-1]
        
        # 移动平均线数据
        ma_data = [['周期', '数值', '与现价关系', '排列状态']]
        
        if 'MA5' in data.columns:
            diff = latest['close'] - latest['MA5']
            ma_data.append(['MA5', f"{latest['MA5']:.2f}", f"{diff:+.2f} ({diff/latest['close']*100:+.2f}%)", '多头排列' if latest['close'] > latest['MA5'] else '空头排列'])
        if 'MA20' in data.columns:
            diff = latest['close'] - latest['MA20']
            ma_data.append(['MA20', f"{latest['MA20']:.2f}", f"{diff:+.2f} ({diff/latest['close']*100:+.2f}%)", '多头排列' if latest['close'] > latest['MA20'] else '空头排列'])
        if 'MA60' in data.columns:
            diff = latest['close'] - latest['MA60']
            ma_data.append(['MA60', f"{latest['MA60']:.2f}", f"{diff:+.2f} ({diff/latest['close']*100:+.2f}%)", '多头排列' if latest['close'] > latest['MA60'] else '空头排列'])
        
        ma_table = Table(ma_data, colWidths=[1*inch, 1.5*inch, 2*inch, 1.5*inch])
        ma_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27AE60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font_bold),
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),  # 表格内容使用中文字体
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        elements.append(Paragraph("【移动平均线数据】", self.section_style))
        elements.append(ma_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # MACD指标数据
        if 'MACD' in data.columns:
            macd_data = [['项目', '数值', '状态']]
            macd_data.append(['DIF线', f"{latest['MACD']:.2f}", '正值' if latest['MACD'] > 0 else '负值'])
            if 'MACD_signal' in data.columns:
                macd_data.append(['DEA线', f"{latest['MACD_signal']:.2f}", '正值' if latest['MACD_signal'] > 0 else '负值'])
            if 'MACD_hist' in data.columns:
                macd_data.append(['MACD柱', f"{latest['MACD_hist']:.2f}", '正值扩大' if latest['MACD_hist'] > 0 else '负值缩小'])
            
            macd_table = Table(macd_data, colWidths=[1.5*inch, 1.5*inch, 3*inch])
            macd_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8E44AD')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), self.chinese_font_bold),
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),  # 表格内容使用中文字体
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            ]))
            
            elements.append(Paragraph("【MACD指标数据】", self.section_style))
            elements.append(macd_table)
            elements.append(Spacer(1, 0.2*inch))
        
        # RSI指标数据
        if 'RSI' in data.columns:
            rsi_data = [['周期', '数值', '状态', '超买超卖']]
            rsi_val = latest['RSI']
            status = '上升' if len(data) > 1 and rsi_val > data['RSI'].iloc[-2] else '下降'
            overbought_oversold = '接近超买' if rsi_val > 70 else '接近超卖' if rsi_val < 30 else '正常'
            rsi_data.append(['RSI14', f"{rsi_val:.1f}", status, overbought_oversold])
            
            rsi_table = Table(rsi_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            rsi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E67E22')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), self.chinese_font_bold),
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),  # 表格内容使用中文字体
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            ]))
            
            elements.append(Paragraph("【RSI指标数据】", self.section_style))
            elements.append(rsi_table)
        
        return elements
    
    def _create_capital_flow_chapter(self, data: pd.DataFrame, symbol: str) -> List:
        """第二章：资金面数据表"""
        elements = []
        
        elements.append(Paragraph("第二章：资金面数据", self.chapter_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # 由于是模拟数据，这里只显示占位信息
        capital_data = [['数据类别', '指标名称', '数值', '单位', '数据日期']]
        capital_data.append(['资金流向', '主力净流入', 'N/A', '亿元', data.index[-1].strftime('%Y-%m-%d')])
        capital_data.append(['资金流向', '散户净流入', 'N/A', '亿元', data.index[-1].strftime('%Y-%m-%d')])
        capital_data.append(['融资融券', '融资余额', 'N/A', '亿元', data.index[-1].strftime('%Y-%m-%d')])
        
        capital_table = Table(capital_data, colWidths=[1.2*inch, 1.5*inch, 1.2*inch, 0.8*inch, 1.3*inch])
        capital_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16A085')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font_bold),
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),  # 表格内容使用中文字体
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        elements.append(Paragraph("【资金面数据】", self.section_style))
        elements.append(Paragraph("注: 模拟数据模式下，资金面数据不可用", self.normal_style))
        elements.append(capital_table)
        
        return elements
    
    def _create_price_volume_chapter(self, data: pd.DataFrame) -> List:
        """第三章：价格与成交量数据"""
        elements = []
        
        elements.append(Paragraph("第三章：近期价格与成交量数据（最近20个交易日）", self.chapter_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # 价格数据表（最近20条）
        recent_20 = data.tail(20)
        price_data = [['交易日', '开盘价', '最高价', '最低价', '收盘价', '涨跌幅', '涨跌额']]
        
        for idx, row in recent_20.iterrows():
            change = row.get('pct_change', 0)
            change_amt = row['close'] - row['open'] if len(data) > 1 else 0
            price_data.append([
                idx.strftime('%Y-%m-%d'),
                f"{row['open']:.2f}",
                f"{row['high']:.2f}",
                f"{row['low']:.2f}",
                f"{row['close']:.2f}",
                f"{change:+.2f}%",
                f"{change_amt:+.2f}"
            ])
        
        price_table = Table(price_data, colWidths=[1*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        price_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C0392B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font_bold),
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),  # 表格内容使用中文字体
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        elements.append(Paragraph("【价格数据表】", self.section_style))
        elements.append(price_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # 成交量数据表
        volume_data = [['交易日', '成交量', '成交额', '涨跌幅']]
        for idx, row in recent_20.iterrows():
            volume_data.append([
                idx.strftime('%Y-%m-%d'),
                f"{row['volume']:,.0f}",
                f"{row.get('amount', 0)/100000000:.2f} 亿元" if 'amount' in row else 'N/A',
                f"{row.get('pct_change', 0):+.2f}%"
            ])
        
        volume_table = Table(volume_data, colWidths=[1.2*inch, 1.5*inch, 1.5*inch, 1.2*inch])
        volume_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2980B9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font_bold),
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),  # 表格内容使用中文字体
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        elements.append(Paragraph("【成交量数据表】", self.section_style))
        elements.append(volume_table)
        
        return elements
    
    def _create_multi_timeframe_chapter(self, data: pd.DataFrame) -> List:
        """第四章：多时间框架数据对比"""
        elements = []
        
        elements.append(Paragraph("第四章：多时间框架数据对比（日/周/月）", self.chapter_style))
        elements.append(Spacer(1, 0.2*inch))
        
        latest = data.iloc[-1]
        
        # 各周期关键价位
        levels_data = [['时间框架', '当前值', '支撑位1', '支撑位2', '阻力位1', '阻力位2']]
        
        # 日线
        recent_20 = data.tail(20)
        levels_data.append([
            '日线',
            f"{latest['close']:.2f}",
            f"{recent_20['low'].min():.2f}",
            f"{data.tail(60)['low'].min():.2f}" if len(data) >= 60 else 'N/A',
            f"{recent_20['high'].max():.2f}",
            f"{data.tail(60)['high'].max():.2f}" if len(data) >= 60 else 'N/A'
        ])
        
        levels_table = Table(levels_data, colWidths=[1*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        levels_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7D3C98')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font_bold),
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),  # 表格内容使用中文字体
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        elements.append(Paragraph("【各周期关键价位】", self.section_style))
        elements.append(levels_table)
        
        return elements
    
    def _create_raw_data_chapter(self, data: pd.DataFrame, symbol: str, market: str) -> List:
        """第五章：原始数据片段（JSON格式）"""
        elements = []
        
        elements.append(Paragraph("第五章：原始数据片段（JSON格式，供AI分析使用）", self.chapter_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # 构建JSON数据
        latest = data.iloc[-1]
        recent_20 = data.tail(20)
        
        json_data = {
            "metadata": {
                "symbol": symbol,
                "market": market,
                "report_type": "data_only",
                "data_cutoff": data.index[-1].strftime('%Y-%m-%d %H:%M:%S'),
                "report_generated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "data_source": "mock_data",
                "data_quality": {
                    "completeness": 1.0,
                    "timeliness": "daily",
                    "accuracy": 1.0
                }
            },
            "price_data": {
                "current": {
                    "price": float(latest['close']),
                    "change_pct": float(latest.get('pct_change', 0)),
                    "open": float(latest['open']),
                    "high": float(latest['high']),
                    "low": float(latest['low']),
                    "volume": int(latest['volume']),
                    "amount": float(latest.get('amount', 0))
                },
                "recent_20_days": [
                    {
                        "date": idx.strftime('%Y-%m-%d'),
                        "open": float(row['open']),
                        "high": float(row['high']),
                        "low": float(row['low']),
                        "close": float(row['close']),
                        "volume": int(row['volume'])
                    }
                    for idx, row in recent_20.iterrows()
                ]
            },
            "technical_indicators": {
                "trend": {},
                "momentum": {},
                "volatility": {}
            }
        }
        
        # 添加技术指标
        if 'MA5' in data.columns:
            json_data["technical_indicators"]["trend"]["MA5"] = float(latest['MA5'])
        if 'MA20' in data.columns:
            json_data["technical_indicators"]["trend"]["MA20"] = float(latest['MA20'])
        if 'MA60' in data.columns:
            json_data["technical_indicators"]["trend"]["MA60"] = float(latest['MA60'])
        if 'MACD' in data.columns:
            json_data["technical_indicators"]["trend"]["MACD"] = {
                "DIF": float(latest['MACD']),
                "DEA": float(latest.get('MACD_signal', 0)),
                "histogram": float(latest.get('MACD_hist', 0))
            }
        if 'RSI' in data.columns:
            json_data["technical_indicators"]["momentum"]["RSI14"] = float(latest['RSI'])
        
        # 转换为JSON字符串
        json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
        
        # 使用Preformatted显示JSON
        json_text = Preformatted(json_str, self.data_style, maxLineLength=80)
        elements.append(json_text)
        
        return elements
    
    def _create_charts_appendix(self, charts: Dict[str, str]) -> List:
        """附录：图表文件清单"""
        elements = []
        
        elements.append(Paragraph("附录：生成的技术图表文件清单", self.chapter_style))
        elements.append(Spacer(1, 0.2*inch))
        
        if not charts:
            elements.append(Paragraph("【图表文件清单】", self.section_style))
            elements.append(Paragraph("暂无图表文件", self.normal_style))
            return elements
        
        chart_list = [['序号', '图表类型', '文件路径', '状态']]
        
        idx = 1
        if 'kline' in charts:
            chart_list.append([str(idx), '主K线图', charts['kline'], '已生成'])
            idx += 1
        if 'indicators' in charts:
            chart_list.append([str(idx), '技术指标图', charts['indicators'], '已生成'])
            idx += 1
        
        chart_table = Table(chart_list, colWidths=[0.5*inch, 1.5*inch, 3.5*inch, 1*inch])
        chart_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#95A5A6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font_bold),
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),  # 表格内容使用中文字体
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        elements.append(Paragraph("【图表文件清单】", self.section_style))
        elements.append(chart_table)
        
        return elements
