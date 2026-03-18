#!/usr/bin/env python3
"""
ClassAutoAI Business Plan PDF Generator
========================================
Generates a professional, consulting-quality business plan PDF
using ReportLab, styled after Perplexity Computer's report format.

Usage:
    python3 generate_bizplan_pdf.py [input.md] [output.pdf]

Defaults:
    input:  /mnt/c/Users/daniel/Desktop/사업계획서/workspace/사업계획서_최종_v3.md
    output: /mnt/c/Users/daniel/Desktop/사업계획서/output/클래스오토AI_사업계획서_v3_pro.pdf
"""

import sys
import os
import re
import glob
import array
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

from reportlab.platypus import (
    BaseDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether, Flowable, Frame, PageTemplate,
    NextPageTemplate
)

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Design Constants
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TEAL         = HexColor('#01696F')
TEAL_LIGHT   = HexColor('#E8F5F5')
TEAL_DARK    = HexColor('#015258')
TEXT_COLOR   = HexColor('#28251D')
GRAY_TEXT    = HexColor('#666666')
LIGHT_GRAY   = HexColor('#F5F5F5')
MID_GRAY     = HexColor('#E0E0E0')
BORDER_GRAY  = HexColor('#DDDDDD')
CAPTION_GRAY = HexColor('#888888')
WHITE        = white
BLACK        = black

PAGE_W, PAGE_H = A4   # 595.27 x 841.89 pt
MARGIN = 2.5 * cm
CONTENT_WIDTH = PAGE_W - 2 * MARGIN

DOC_TITLE  = '클래스오토AI 사업계획서'
DOC_DATE   = datetime.now().strftime('%Y년 %m월 %d일')

DEFAULT_INPUT  = '/mnt/c/Users/daniel/Desktop/사업계획서/workspace/사업계획서_최종_v3.md'
DEFAULT_OUTPUT = '/mnt/c/Users/daniel/Desktop/사업계획서/output/클래스오토AI_사업계획서_v3_pro.pdf'
CHARTS_DIR = None  # 입력 파일 기준으로 자동 탐색

COVER_HIGHLIGHTS = [
    ('아이템',   '클래스오토AI - AI 기반 교육콘텐츠 자동화 SaaS'),
    ('목표시장', '사이버대학 22개교, SOM 13~44억 원 -> 확장 SOM 850~1,900억 원'),
    ('핵심가치', '강의 제작 비용 70~85% 절감, 제작 기간 1~2개월 -> 1~3일'),
    ('팀 구성',  '교육공학 석사(대표) + 컴퓨터공학 SW 개발자(공동창업)'),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Font Registration  (OTF -> TTF conversion for ReportLab)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _convert_otf_to_ttf(otf_path, ttf_path, max_err=1.0):
    """Convert CFF-based OTF to TrueType TTF using fontTools + cu2qu."""
    from fontTools.ttLib import TTFont as FTFont, newTable
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib.tables._g_l_y_f import Glyph as TTGlyph
    from fontTools.ttLib.tables import _g_l_y_f, _l_o_c_a, ttProgram

    font = FTFont(otf_path)
    cs = font['CFF '].cff.topDictIndex[0].CharStrings
    order = font.getGlyphOrder()

    gt = _g_l_y_f.table__g_l_y_f()
    gt.glyphs, gt.glyphOrder = {}, order

    for gn in order:
        pen = TTGlyphPen(None)
        try:
            cs[gn].draw(Cu2QuPen(pen, max_err, reverse_direction=True))
            gt.glyphs[gn] = pen.glyph()
        except Exception:
            gt.glyphs[gn] = TTGlyph()

    del font['CFF ']
    font['glyf'] = gt
    font['loca'] = _l_o_c_a.table__l_o_c_a()
    font['head'].flags |= (1 << 3)

    mx = font['maxp']
    mx.tableVersion = 0x00010000
    mx.numGlyphs = len(order)
    mp = mc = 0
    for gn in order:
        g = gt.glyphs[gn]
        if hasattr(g, 'numberOfContours') and g.numberOfContours > 0:
            if hasattr(g, 'coordinates'):
                mp = max(mp, len(g.coordinates))
            mc = max(mc, g.numberOfContours)
    for attr, val in [('maxPoints', max(mp, 1)), ('maxContours', max(mc, 1)),
                      ('maxCompositePoints', 0), ('maxCompositeContours', 0),
                      ('maxZones', 2), ('maxTwilightPoints', 0), ('maxStorage', 0),
                      ('maxFunctionDefs', 0), ('maxInstructionDefs', 0),
                      ('maxStackElements', 0), ('maxSizeOfInstructions', 0),
                      ('maxComponentElements', 0), ('maxComponentDepth', 0)]:
        setattr(mx, attr, val)

    ct = newTable('cvt ')
    ct.values = array.array('h')
    font['cvt '] = ct
    for tag in ['prep', 'fpgm']:
        t = newTable(tag)
        t.program = ttProgram.Program()
        t.program.fromBytecode(b'')
        font[tag] = t

    font.sfntVersion = '\x00\x01\x00\x00'
    font.save(ttf_path)
    font.close()


def register_fonts():
    """Register Pretendard font family (auto-converts OTF to TTF)."""
    # 여러 경로에서 폰트 탐색: ~/.fonts, 프로젝트/fonts/, /app/fonts/
    font_dir = None
    for candidate in [
        os.path.expanduser('~/.fonts'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts'),
        '/app/fonts',
    ]:
        if os.path.isdir(candidate) and any('Pretendard' in f for f in os.listdir(candidate)):
            font_dir = candidate
            break
    if not font_dir:
        print("  Warning: Pretendard font directory not found")
        return
    font_map = {
        'Pretendard':          'Pretendard-Regular',
        'Pretendard-Bold':     'Pretendard-Bold',
        'Pretendard-SemiBold': 'Pretendard-SemiBold',
        'Pretendard-Medium':   'Pretendard-Medium',
    }
    for reg_name, basename in font_map.items():
        ttf_path = os.path.join(font_dir, f'{basename}.ttf')
        otf_path = os.path.join(font_dir, f'{basename}.otf')
        if not os.path.exists(ttf_path) and os.path.exists(otf_path):
            print(f"  Converting {basename}.otf -> .ttf ...")
            _convert_otf_to_ttf(otf_path, ttf_path)
        if os.path.exists(ttf_path):
            pdfmetrics.registerFont(TTFont(reg_name, ttf_path))
        else:
            print(f"  Warning: font {basename} not found")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Custom Flowables
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TealSectionHeader(Flowable):
    """Teal filled rounded rectangle with white section title."""

    def __init__(self, text, width=None):
        Flowable.__init__(self)
        self.text = text
        self._width = width or CONTENT_WIDTH
        self.height = 34

    def wrap(self, aW, aH):
        self._width = min(self._width, aW)
        return self._width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(TEAL)
        c.roundRect(0, 0, self._width, self.height, 4, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Pretendard-Bold', 13)
        c.drawString(14, 10, self.text)


class CheckboxSectionHeader(Flowable):
    """Bold heading with teal left-border accent bar."""

    def __init__(self, text, width=None):
        Flowable.__init__(self)
        self.text = text
        self._width = width or CONTENT_WIDTH
        self.height = 30

    def wrap(self, aW, aH):
        self._width = min(self._width, aW)
        return self._width, self.height

    def draw(self):
        c = self.canv
        # Teal left border
        c.setFillColor(TEAL)
        c.rect(0, 0, 4, self.height, fill=1, stroke=0)
        # Light background
        c.setFillColor(TEAL_LIGHT)
        c.rect(4, 0, self._width - 4, self.height, fill=1, stroke=0)
        # Text
        c.setFillColor(TEXT_COLOR)
        c.setFont('Pretendard-Bold', 12)
        c.drawString(16, 9, self.text)


class TealBulletParagraph(Flowable):
    """Teal circle-bullet with bold subsection text (wraps long text)."""

    def __init__(self, text, width=None):
        Flowable.__init__(self)
        self.raw_text = text
        self._width = width or CONTENT_WIDTH
        self._para = None
        self._ph = 0

    def wrap(self, aW, aH):
        self._width = min(self._width, aW)
        style = ParagraphStyle('_tb', fontName='Pretendard-Bold', fontSize=11,
                               leading=16, textColor=TEXT_COLOR)
        processed = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', self.raw_text)
        self._para = Paragraph(processed, style)
        _, self._ph = self._para.wrap(self._width - 24, aH)
        return self._width, self._ph + 6

    def draw(self):
        c = self.canv
        # Teal filled circle bullet
        c.setFillColor(TEAL)
        c.circle(8, self._ph - 4, 3.5, fill=1, stroke=0)
        self._para.drawOn(c, 22, 0)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Paragraph Styles
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def create_styles():
    s = {}
    s['body'] = ParagraphStyle('body',
        fontName='Pretendard', fontSize=10, leading=16,
        textColor=TEXT_COLOR, alignment=TA_LEFT,
        spaceBefore=2, spaceAfter=4, wordWrap='CJK',
        splitLongWords=True)

    s['bullet_dash'] = ParagraphStyle('bdash',
        fontName='Pretendard', fontSize=10, leading=16,
        textColor=TEXT_COLOR, alignment=TA_LEFT,
        leftIndent=24, rightIndent=8, spaceBefore=4, spaceAfter=6,
        wordWrap='CJK', splitLongWords=True)

    s['bold_left'] = ParagraphStyle('bleft',
        fontName='Pretendard-Bold', fontSize=11, leading=15,
        textColor=TEXT_COLOR, alignment=TA_LEFT, rightIndent=8,
        spaceBefore=10, spaceAfter=6)

    s['caption'] = ParagraphStyle('cap',
        fontName='Pretendard', fontSize=9, leading=12,
        textColor=CAPTION_GRAY, alignment=TA_CENTER,
        spaceBefore=4, spaceAfter=12)

    s['table_header'] = ParagraphStyle('th',
        fontName='Pretendard-Bold', fontSize=9, leading=13,
        textColor=WHITE, alignment=TA_CENTER, wordWrap='CJK')

    s['table_cell'] = ParagraphStyle('tc',
        fontName='Pretendard', fontSize=9, leading=13,
        textColor=TEXT_COLOR, alignment=TA_LEFT, wordWrap='CJK',
        splitLongWords=True, rightIndent=4)

    s['toc_title'] = ParagraphStyle('toc_title',
        fontName='Pretendard-Bold', fontSize=18, leading=24,
        textColor=TEAL, spaceBefore=20, spaceAfter=14)

    s['toc_section'] = ParagraphStyle('toc_sec',
        fontName='Pretendard-SemiBold', fontSize=11, leading=16,
        textColor=TEXT_COLOR, leftIndent=8, rightIndent=8,
        spaceBefore=8, spaceAfter=2)

    s['toc_sub'] = ParagraphStyle('toc_sub',
        fontName='Pretendard', fontSize=9, leading=13,
        textColor=GRAY_TEXT, leftIndent=24, rightIndent=8,
        spaceBefore=2, spaceAfter=6)

    return s


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Markdown Parsing Utilities
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def process_bold(text):
    """Convert **text** to <b>text</b> for Paragraph XML."""
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)


def parse_table_lines(lines):
    """Parse markdown table lines into list of rows."""
    rows = []
    for line in lines:
        s = line.strip()
        if s.startswith('|') and s.endswith('|'):
            if re.match(r'^\|[\s\-:|]+\|$', s):
                continue  # separator row
            rows.append([c.strip() for c in s.split('|')[1:-1]])
    return rows


def find_charts_for_text(text, charts_dir):
    """Find chart images relevant to given text by keyword matching.
    고정 매핑 + 파일명 기반 자동 매칭."""
    if not os.path.isdir(charts_dir):
        return []
    all_charts = glob.glob(os.path.join(charts_dir, '*.png'))
    all_charts += glob.glob(os.path.join(charts_dir, '*.jpg'))

    # 고정 매핑 (기본)
    keyword_map = {
        'market_size':    ['시장 현황', '시장 규모', 'TAM', 'SAM', 'SOM', '시장 계층'],
        'market_trend':   ['CAGR', '전망', '트렌드', '성장세', '이러닝', '성장 추이'],
        'competitor_map': ['경쟁사', '경쟁 구도', '포지셔닝', '경쟁 분석'],
        'competitor':     ['경쟁사', '경쟁 구도', '포지셔닝'],
        'price':          ['가격', '비용', '요금'],
        'segment':        ['세그먼트', '고객', '타겟', '페르소나'],
        'roadmap':        ['로드맵', '일정', '단계별'],
        'revenue':        ['수익', '매출', 'ARR', 'BM', '비즈니스 모델'],
    }

    # 파일명에서 키워드 자동 추출 (고정 매핑에 없는 차트도 매칭)
    for cp in sorted(all_charts):
        bn = os.path.splitext(os.path.basename(cp))[0].lower()
        if bn not in keyword_map:
            # 파일명의 단어를 키워드로 사용
            words = bn.replace('_', ' ').replace('-', ' ').split()
            keyword_map[bn] = words

    found = []
    for cp in sorted(all_charts):
        bn = os.path.splitext(os.path.basename(cp))[0]
        bn_lower = bn.lower()
        keywords = keyword_map.get(bn, keyword_map.get(bn_lower, []))
        for kw in keywords:
            if kw in text:
                found.append(cp)
                break
    return found


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Table Builder
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_table(rows, styles):
    """Create a professionally styled Table from parsed row data."""
    if not rows:
        return []
    ncols = len(rows[0])

    data = []
    for ri, row in enumerate(rows):
        tr = []
        for cell in row:
            st = styles['table_header'] if ri == 0 else styles['table_cell']
            tr.append(Paragraph(process_bold(cell), st))
        while len(tr) < ncols:
            tr.append(Paragraph('', styles['table_cell']))
        data.append(tr)

    # Proportional column widths based on content length
    col_len = [0] * ncols
    for row in rows:
        for ci, cell in enumerate(row):
            if ci < ncols:
                clean = re.sub(r'\*\*(.+?)\*\*', r'\1', cell)
                col_len[ci] = max(col_len[ci], len(clean))
    total = sum(col_len) or 1
    avail = CONTENT_WIDTH
    # 최소 열 너비: 첫 번째 열은 최소 80pt (한글 4글자), 나머지는 60pt
    min_first = 80
    min_rest = 60
    widths = []
    for ci, cl in enumerate(col_len):
        min_w = min_first if ci == 0 else min_rest
        widths.append(max(avail * (cl / total), min_w))
    factor = avail / sum(widths)
    widths = [w * factor for w in widths]

    tbl = Table(data, colWidths=widths, repeatRows=1)

    cmds = [
        ('BACKGROUND',    (0, 0), (-1, 0), TEAL),
        ('TEXTCOLOR',     (0, 0), (-1, 0), WHITE),
        ('FONTNAME',      (0, 0), (-1, 0), 'Pretendard-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0), 9),
        ('ALIGN',         (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME',      (0, 1), (-1, -1), 'Pretendard'),
        ('FONTSIZE',      (0, 1), (-1, -1), 9),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('GRID',          (0, 0), (-1, -1), 0.5, BORDER_GRAY),
        ('LINEBELOW',     (0, 0), (-1, 0), 1.5, TEAL_DARK),
    ]
    for ri in range(1, len(data)):
        bg = LIGHT_GRAY if ri % 2 == 0 else WHITE
        cmds.append(('BACKGROUND', (0, ri), (-1, ri), bg))
    tbl.setStyle(TableStyle(cmds))

    return [Spacer(1, 6), tbl, Spacer(1, 8)]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Chart Image Builder
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_chart(chart_path, styles):
    """Create Image + italic caption flowables for a chart."""
    if not os.path.exists(chart_path):
        return []
    try:
        from PIL import Image as PILImage
        pil_img = PILImage.open(chart_path)
        iw, ih = pil_img.size
        # Use DPI info from image to get correct physical dimensions in points
        dpi_x, dpi_y = pil_img.info.get('dpi', (150, 150))
        # Convert pixel dimensions to points (1 inch = 72 pt)
        iw_pt = iw * 72.0 / dpi_x
        ih_pt = ih * 72.0 / dpi_y
    except ImportError:
        iw_pt, ih_pt = 480, 320

    max_w = CONTENT_WIDTH
    max_h = 380  # increased from 280 to prevent excessive downscaling
    scale = min(max_w / iw_pt, max_h / ih_pt, 1.0)  # never upscale
    dw, dh = iw_pt * scale, ih_pt * scale

    bn = os.path.splitext(os.path.basename(chart_path))[0]
    cap_map = {
        'market_size':    '[그림] 목표 시장 규모 (TAM / SAM / SOM)',
        'market_trend':   '[그림] 시장 성장 추이 및 전망',
        'competitor_map': '[그림] 경쟁사 포지셔닝 맵',
        'price':          '[그림] 가격대 비교',
        'segment':        '[그림] 고객 세그먼트 분석',
        'roadmap':        '[그림] 사업 로드맵',
        'revenue':        '[그림] 수익 모델 구조',
        'feature':        '[그림] 기능 비교',
    }
    # 파일명에서 자동 캡션 생성
    cap = cap_map.get(bn, f'[그림] {bn.replace("_", " ").title()}')

    img = Image(chart_path, width=dw, height=dh)
    img.hAlign = 'CENTER'

    return [
        Spacer(1, 10),
        img,
        Paragraph(f'<i>{cap}</i>', styles['caption']),
        Spacer(1, 6),
    ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Table of Contents Builder
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_toc(styles):
    """Build table of contents page."""
    fl = []
    fl.append(Spacer(1, 4))
    fl.append(Paragraph('목 차', styles['toc_title']))

    # Decorative line
    toc_line = Table(
        [['']], colWidths=[CONTENT_WIDTH],
        style=TableStyle([
            ('LINEBELOW', (0, 0), (-1, 0), 1.2, TEAL),
            ('TOPPADDING', (0, 0), (-1, 0), 0),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 0),
        ])
    )
    fl.append(toc_line)
    fl.append(Spacer(1, 16))

    toc_items = [
        ('\u25A1 일반현황',
         '팀 구성 현황'),
        ('\u25A1 창업 아이템 개요(요약)',
         '명칭 및 범주, 아이템 개요, 문제 인식, 실현 가능성, 성장 전략, 팀 구성'),
        ('1. 문제 인식(Problem)_창업 아이템의 필요성',
         '국내외 시장 현황, 핵심 문제, 창업 아이템의 필요성'),
        ('2. 실현 가능성(Solution)_창업 아이템의 개발 계획',
         '개발 계획, 차별성 및 경쟁력 확보, 정부지원사업비 집행 방향'),
        ('3. 성장전략(Scale-up)_사업화 추진 전략',
         '경쟁사 분석, 비즈니스 모델, 투자 유치 전략, 사업 로드맵'),
        ('4. 팀 구성(Team)_대표자 및 팀원 구성 계획',
         '대표자 역량, 팀 구성(안), 협력 기관'),
    ]
    for section, sub in toc_items:
        fl.append(Paragraph(section, styles['toc_section']))
        fl.append(Paragraph(sub, styles['toc_sub']))

    fl.append(PageBreak())
    return fl


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main Markdown -> Flowables Parser
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def parse_markdown(md_text, styles, charts_dir):
    """Convert full markdown to list of ReportLab flowables."""
    lines = md_text.split('\n')
    fl = []
    i = 0
    sec_text = ''        # accumulated text for chart matching
    used_charts = set()
    doc_title = ''

    def _flush_charts():
        """Insert matching charts accumulated so far."""
        nonlocal sec_text
        if sec_text:
            for cp in find_charts_for_text(sec_text, charts_dir):
                if cp not in used_charts:
                    fl.extend(build_chart(cp, styles))
                    used_charts.add(cp)
        sec_text = ''

    while i < len(lines):
        line = lines[i]
        s = line.strip()

        # Skip empty
        if not s:
            i += 1
            continue

        # Horizontal rule -> page break
        if re.match(r'^---+$', s):
            _flush_charts()
            fl.append(PageBreak())
            i += 1
            continue

        # H1 (document title -- used on cover only)
        if s.startswith('# ') and not s.startswith('## '):
            doc_title = s[2:].strip()
            i += 1
            continue

        # H2 section headers
        if s.startswith('## '):
            ht = s[3:].strip()
            if ht.startswith('\u25A1'):  # □ checkbox header
                fl.append(Spacer(1, 10))
                fl.append(CheckboxSectionHeader(ht))
                fl.append(Spacer(1, 8))
            elif re.match(r'^\d+\.', ht):  # numbered section
                _flush_charts()
                fl.append(Spacer(1, 8))
                fl.append(TealSectionHeader(ht))
                fl.append(Spacer(1, 10))
                sec_text = ht
            else:
                fl.append(Spacer(1, 8))
                fl.append(TealSectionHeader(ht))
                fl.append(Spacer(1, 10))
                sec_text = ht
            i += 1
            continue

        # Teal bullet (◦)
        if s.startswith('\u25E6') or s.startswith('\u25CB') or (len(s) > 0 and s[0] == '◦'):
            bt = s[1:].strip()
            fl.append(Spacer(1, 10))
            fl.append(TealBulletParagraph(bt))
            fl.append(Spacer(1, 4))
            sec_text += ' ' + bt
            i += 1
            continue

        # Dash bullet (-)
        if s.startswith('- '):
            bt = process_bold(s[2:].strip())
            teal_hex = '#01696F'
            para = f'<font color="{teal_hex}">\u2013</font>&nbsp;&nbsp;{bt}'
            fl.append(Paragraph(para, styles['bullet_dash']))
            sec_text += ' ' + s[2:]
            i += 1
            continue

        # Table
        if s.startswith('|'):
            tl = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                tl.append(lines[i])
                i += 1
            rows = parse_table_lines(tl)
            if rows:
                fl.extend(build_table(rows, styles))
            continue

        # Bold standalone line  **<...>** or **...**
        if s.startswith('**') and s.endswith('**'):
            inner = s[2:-2].strip()
            fl.append(Spacer(1, 8))
            fl.append(Paragraph(inner, styles['bold_left']))
            fl.append(Spacer(1, 2))
            i += 1
            continue

        # Regular text
        fl.append(Paragraph(process_bold(s), styles['body']))
        sec_text += ' ' + s
        i += 1

    _flush_charts()
    return fl, doc_title


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Page Drawing Callbacks (header/footer/cover)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def draw_cover(canvas, doc):
    """Draw the cover page on the canvas (called by PageTemplate)."""
    c = canvas
    c.saveState()
    w, h = PAGE_W, PAGE_H

    # Top teal bar (full bleed)
    bar_h = 14
    c.setFillColor(TEAL)
    c.rect(0, h - bar_h, w, bar_h, fill=1, stroke=0)

    # Thin accent line beneath
    c.setStrokeColor(TEAL)
    c.setLineWidth(0.5)
    c.line(MARGIN, h - bar_h - 6, w - MARGIN, h - bar_h - 6)

    # Title
    y = h - 130
    c.setFillColor(TEAL)
    c.setFont('Pretendard-Bold', 34)
    c.drawString(MARGIN, y, '예비창업패키지')
    c.drawString(MARGIN, y - 50, '예비창업자 사업계획서')

    # Subtitle
    y2 = y - 120
    c.setFillColor(TEXT_COLOR)
    c.setFont('Pretendard-SemiBold', 20)
    c.drawString(MARGIN, y2, '클래스오토AI (ClassAutoAI)')

    # Description
    y3 = y2 - 32
    c.setFillColor(GRAY_TEXT)
    c.setFont('Pretendard', 12)
    c.drawString(MARGIN, y3, 'AI 기반 교육콘텐츠 자동화 SaaS 플랫폼')

    # Date
    y4 = y3 - 26
    c.setFont('Pretendard', 11)
    c.drawString(MARGIN, y4, DOC_DATE)

    # Key Highlights summary box
    box_x = MARGIN
    box_w = CONTENT_WIDTH
    box_h = 200
    box_y = 80

    # Box background
    c.setFillColor(LIGHT_GRAY)
    c.roundRect(box_x, box_y, box_w, box_h, 6, fill=1, stroke=0)

    # Box header
    hdr_h = 34
    c.setFillColor(TEAL)
    c.roundRect(box_x, box_y + box_h - hdr_h, box_w, hdr_h, 6, fill=1, stroke=0)
    c.rect(box_x, box_y + box_h - hdr_h, box_w, 8, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont('Pretendard-Bold', 11)
    c.drawString(box_x + 16, box_y + box_h - 23, '\u25B8 핵심 요약 (Key Highlights)')

    # Highlight items
    yh = box_y + box_h - 54
    for label, value in COVER_HIGHLIGHTS:
        c.setFillColor(TEAL)
        c.setFont('Pretendard-SemiBold', 10)
        c.drawString(box_x + 20, yh, f'\u25B8 {label}')
        c.setFillColor(TEXT_COLOR)
        c.setFont('Pretendard', 10)
        disp = value if len(value) <= 72 else value[:72] + '...'
        c.drawString(box_x + 22, yh - 15, disp)
        yh -= 38

    # Bottom accent line
    c.setStrokeColor(TEAL)
    c.setLineWidth(2)
    c.line(MARGIN, box_y - 12, w - MARGIN, box_y - 12)

    c.restoreState()


def draw_later_pages(canvas, doc):
    """Draw header and footer on content pages."""
    c = canvas
    c.saveState()

    page_num = doc.page - 1  # subtract cover page

    # Header
    yh = PAGE_H - 12 * mm
    c.setFont('Pretendard', 8)
    c.setFillColor(GRAY_TEXT)
    c.drawString(MARGIN, yh, DOC_TITLE)
    c.drawRightString(PAGE_W - MARGIN, yh, DOC_DATE)
    c.setStrokeColor(MID_GRAY)
    c.setLineWidth(0.5)
    c.line(MARGIN, yh - 4, PAGE_W - MARGIN, yh - 4)

    # Footer
    yf = 14 * mm
    c.setFont('Pretendard', 9)
    c.setFillColor(GRAY_TEXT)
    c.drawCentredString(PAGE_W / 2, yf, f'- {page_num} -')
    c.setStrokeColor(MID_GRAY)
    c.setLineWidth(0.5)
    c.line(MARGIN, yf + 12, PAGE_W - MARGIN, yf + 12)

    c.restoreState()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main Generation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_pdf(input_path, output_path):
    """Generate the professional PDF from a markdown file."""
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    register_fonts()

    with open(input_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    styles = create_styles()
    # 차트 디렉토리: 입력 파일 옆의 charts/ 폴더 자동 탐색
    charts_dir = CHARTS_DIR or os.path.join(os.path.dirname(os.path.abspath(input_path)), "charts")
    flowables, title = parse_markdown(md_text, styles, charts_dir)

    # Margins for content pages (extra room for header/footer)
    top_m = MARGIN + 2 * mm   # 헤더 바로 아래에서 시작
    bot_m = MARGIN + 4 * mm   # 푸터 공간

    content_frame = Frame(
        MARGIN, bot_m,
        CONTENT_WIDTH, PAGE_H - top_m - bot_m,
        id='content'
    )
    cover_frame = Frame(
        MARGIN, MARGIN,
        CONTENT_WIDTH, PAGE_H - 2 * MARGIN,
        id='cover'
    )

    cover_template = PageTemplate(id='cover', frames=[cover_frame], onPage=draw_cover)
    content_template = PageTemplate(id='content', frames=[content_frame], onPage=draw_later_pages)

    doc = BaseDocTemplate(
        output_path,
        pagesize=A4,
        title=DOC_TITLE,
        author='클래스오토AI',
        subject='예비창업패키지 사업계획서',
    )
    doc.addPageTemplates([cover_template, content_template])

    # Build: cover (empty spacer to trigger page) -> TOC -> content
    toc_flowables = build_toc(styles)

    all_flowables = [
        NextPageTemplate('content'),
        PageBreak(),
    ] + toc_flowables + flowables

    doc.build(all_flowables)

    if os.path.exists(output_path):
        size_kb = os.path.getsize(output_path) / 1024
        print(f"\nPDF generated successfully: {output_path}")
        print(f"File size: {size_kb:.1f} KB")
    else:
        print("ERROR: Output file not created!")
        sys.exit(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Entry Point
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == '__main__':
    inp = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT
    out = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT

    if not os.path.exists(inp):
        print(f"ERROR: Input not found: {inp}")
        sys.exit(1)

    generate_pdf(inp, out)
