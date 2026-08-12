"""Convert D:\figures\pipeline_features.md to PDF using markdown + reportlab."""
import re, markdown
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable, ListFlowable, ListItem)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

SRC  = Path(r"D:\figures\pipeline_features.md")
DEST = Path(r"D:\figures\pipeline_features.pdf")

md_text = SRC.read_text(encoding="utf-8")

doc = SimpleDocTemplate(
    str(DEST),
    pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm,
    topMargin=2*cm,  bottomMargin=2*cm,
)

BASE   = colors.HexColor("#e0e0e0")
ACCENT = colors.HexColor("#58a6ff")
DIM    = colors.HexColor("#8b949e")
BG     = colors.HexColor("#0d1117")
PANEL  = colors.HexColor("#161b22")
BORDER = colors.HexColor("#30363d")
GREEN  = colors.HexColor("#56d364")
YELLOW = colors.HexColor("#e3b341")
RED    = colors.HexColor("#f85149")

styles = getSampleStyleSheet()

def S(name, **kw):
    return ParagraphStyle(name, **kw)

st_h1 = S("H1", fontName="Helvetica-Bold", fontSize=20, textColor=ACCENT,
           spaceAfter=6, spaceBefore=16, backColor=BG, borderPad=4)
st_h2 = S("H2", fontName="Helvetica-Bold", fontSize=14, textColor=ACCENT,
           spaceAfter=4, spaceBefore=14, borderPad=2,
           borderWidth=0, borderColor=BORDER)
st_h3 = S("H3", fontName="Helvetica-Bold", fontSize=11, textColor=GREEN,
           spaceAfter=3, spaceBefore=10)
st_h4 = S("H4", fontName="Helvetica-Bold", fontSize=10, textColor=YELLOW,
           spaceAfter=2, spaceBefore=8)
st_body = S("Body", fontName="Helvetica", fontSize=9, textColor=BASE,
            leading=14, spaceAfter=4)
st_code = S("Code", fontName="Courier", fontSize=8, textColor=GREEN,
            backColor=PANEL, leading=12, leftIndent=10, spaceAfter=4, spaceBefore=4)
st_bullet = S("Bullet", fontName="Helvetica", fontSize=9, textColor=BASE,
              leading=13, leftIndent=14, spaceAfter=2, bulletIndent=4)
st_dim = S("Dim", fontName="Helvetica-Oblique", fontSize=8.5, textColor=DIM,
           spaceAfter=2)

def esc(t):
    return (t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))

def parse_inline(text):
    """Handle **bold**, `code`, *italic* inline."""
    text = esc(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`([^`]+)`', r'<font face="Courier" color="#56d364">\1</font>', text)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    return text

story = []

lines = md_text.splitlines()
i = 0
in_table = False
table_rows = []

def flush_table():
    global table_rows, in_table
    if not table_rows:
        in_table = False
        return
    # First row = header, second = separator, rest = data
    data_rows = [r for r in table_rows if not re.match(r'^\|[-| :]+\|$', r)]
    cells = []
    for row in data_rows:
        parts = [c.strip() for c in row.strip().strip('|').split('|')]
        cells.append(parts)
    if not cells:
        table_rows = []
        in_table = False
        return
    # Render
    col_count = max(len(r) for r in cells)
    # Pad rows
    padded = [r + ['']*(col_count-len(r)) for r in cells]
    p_cells = []
    for ri, row in enumerate(padded):
        p_row = []
        for ci, cell in enumerate(row):
            sty = st_dim if ri == 0 else st_body
            p_row.append(Paragraph(parse_inline(cell), sty))
        p_cells.append(p_row)
    col_w = (17*cm) / col_count
    tbl = Table(p_cells, colWidths=[col_w]*col_count)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PANEL),
        ('TEXTCOLOR',  (0,0), (-1,0), DIM),
        ('BACKGROUND', (0,1), (-1,-1), BG),
        ('GRID',       (0,0), (-1,-1), 0.4, BORDER),
        ('VALIGN',     (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [BG, colors.HexColor("#111419")]),
        ('TOPPADDING',  (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING',(0,0), (-1,-1), 6),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 6))
    table_rows = []
    in_table = False

while i < len(lines):
    line = lines[i]

    # Table detection
    if line.startswith('|'):
        in_table = True
        table_rows.append(line)
        i += 1
        continue
    elif in_table:
        flush_table()

    # Headings
    if line.startswith('#### '):
        story.append(Paragraph(parse_inline(line[5:]), st_h4))
    elif line.startswith('### '):
        story.append(Paragraph(parse_inline(line[4:]), st_h3))
    elif line.startswith('## '):
        story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=4))
        story.append(Paragraph(parse_inline(line[3:]), st_h2))
    elif line.startswith('# '):
        story.append(Paragraph(parse_inline(line[2:]), st_h1))
        story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=6))
    # Bullets
    elif line.startswith('- ') or line.startswith('* '):
        story.append(Paragraph(u"• " + parse_inline(line[2:]), st_bullet))
    elif re.match(r'^\d+\. ', line):
        num, rest = line.split('. ', 1)
        story.append(Paragraph(f"<b>{num}.</b> {parse_inline(rest)}", st_bullet))
    # Code blocks
    elif line.startswith('```'):
        i += 1
        code_lines = []
        while i < len(lines) and not lines[i].startswith('```'):
            code_lines.append(esc(lines[i]))
            i += 1
        story.append(Paragraph('<br/>'.join(code_lines) or ' ', st_code))
    # HR
    elif line.strip() in ('---', '***', '___'):
        story.append(HRFlowable(width="100%", thickness=0.4, color=BORDER, spaceAfter=4))
    # Blank line
    elif line.strip() == '':
        story.append(Spacer(1, 4))
    # Normal paragraph
    else:
        story.append(Paragraph(parse_inline(line), st_body))

    i += 1

if in_table:
    flush_table()

# Dark background via canvas
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.pdfgen import canvas as _canvas_mod

def dark_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BG)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    # Page number
    canvas.setFillColor(DIM)
    canvas.setFont("Helvetica", 7)
    canvas.drawRightString(A4[0]-2*cm, 1.2*cm, f"Page {doc.page}")
    canvas.restoreState()

doc.build(story, onFirstPage=dark_bg, onLaterPages=dark_bg)
print(f"PDF saved: {DEST}")
