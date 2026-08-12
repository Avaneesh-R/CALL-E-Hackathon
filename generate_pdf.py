# -*- coding: utf-8 -*-
"""
Generate the CALL-E Vendor Discovery & Outreach Agent system reference PDF.
Output: D:\\figures\\calle_system_full.pdf
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
NAVY      = HexColor('#1B2A4A')
GOLD      = HexColor('#C9A84C')
LIGHTBG   = HexColor('#F7F8FC')
WHITE     = HexColor('#FFFFFF')
DARKTEXT  = HexColor('#1A1A2E')
GRAY      = HexColor('#6C757D')
BOXBG     = HexColor('#EEF2FF')
GREEN     = HexColor('#2D6A4F')
CODEBG    = HexColor('#1E1E2E')
CODETEXT  = HexColor('#CDD6F4')

PAGE_W, PAGE_H = A4
MARGIN = 50
USABLE = PAGE_W - 2 * MARGIN   # 495

OUT_PATH = r'D:\figures\calle_system_full.pdf'

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
styles = getSampleStyleSheet()

def _mk(name, **kw):
    if name in styles:
        s = styles[name]
        for k, v in kw.items():
            setattr(s, k, v)
        return s
    return styles.add(ParagraphStyle(name=name, **kw)) or styles[name]

ChapterTitle = ParagraphStyle('ChapterTitle', fontName='Helvetica-Bold',
    fontSize=22, textColor=NAVY, leading=26, spaceAfter=4)
ChapterNum = ParagraphStyle('ChapterNum', fontName='Helvetica-Bold',
    fontSize=10, textColor=GOLD, leading=12, spaceAfter=2)
SectionHeader = ParagraphStyle('SectionHeader', fontName='Helvetica-Bold',
    fontSize=14, textColor=white, leading=16)
SubHeader = ParagraphStyle('SubHeader', fontName='Helvetica-Bold',
    fontSize=11, textColor=NAVY, leading=14, spaceBefore=8, spaceAfter=3)
Body = ParagraphStyle('Body', fontName='Helvetica', fontSize=10,
    textColor=DARKTEXT, leading=16, spaceAfter=6, alignment=TA_JUSTIFY)
Caption = ParagraphStyle('Caption', fontName='Helvetica-Oblique', fontSize=9,
    textColor=GRAY, leading=12, spaceAfter=4)
DiagramText = ParagraphStyle('DiagramText', fontName='Courier', fontSize=8,
    textColor=CODETEXT, leading=11)
QuoteText = ParagraphStyle('QuoteText', fontName='Helvetica-Oblique', fontSize=11,
    textColor=NAVY, leading=17, leftIndent=14, rightIndent=14, spaceAfter=6)
TOCEntry = ParagraphStyle('TOCEntry', fontName='Helvetica', fontSize=11,
    textColor=DARKTEXT, leading=22)
CellBody = ParagraphStyle('CellBody', fontName='Helvetica', fontSize=9,
    textColor=DARKTEXT, leading=12)
CellHead = ParagraphStyle('CellHead', fontName='Helvetica-Bold', fontSize=9,
    textColor=white, leading=12)
KeyFact = ParagraphStyle('KeyFact', fontName='Helvetica', fontSize=9.5,
    textColor=DARKTEXT, leading=15)

def esc(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

# ---------------------------------------------------------------------------
# Reusable flowable builders
# ---------------------------------------------------------------------------
def section_header(title):
    t = Table([[Paragraph(esc(title), SectionHeader)]], colWidths=[USABLE])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
    ]))
    return t

def diagram_box(lines):
    """lines: list of raw text lines (already ASCII). Escaped + joined with <br/>."""
    body = '<br/>'.join(esc(ln) for ln in lines)
    p = Paragraph(body, DiagramText)
    t = Table([[p]], colWidths=[USABLE])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CODEBG),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
    ]))
    return t

def quote_box(text):
    p = Paragraph(esc(text), QuoteText)
    t = Table([[p]], colWidths=[USABLE])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BOXBG),
        ('LINEBEFORE', (0, 0), (0, -1), 3, GOLD),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 16),
        ('RIGHTPADDING', (0, 0), (-1, -1), 16),
    ]))
    return t

def keyfacts_box(title, facts):
    rows = [[Paragraph('<b>%s</b>' % esc(title), ParagraphStyle(
        'kf', fontName='Helvetica-Bold', fontSize=10, textColor=NAVY, leading=14))]]
    for f in facts:
        rows.append([Paragraph('&bull; ' + esc(f), KeyFact)])
    t = Table(rows, colWidths=[USABLE])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BOXBG),
        ('LINEBELOW', (0, 0), (0, 0), 0.5, GOLD),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (0, 0), 10),
        ('BOTTOMPADDING', (0, -1), (0, -1), 10),
    ]))
    return t

def feature_table(header, rows, col_widths):
    data = [[Paragraph(esc(h), CellHead) for h in header]]
    for r in rows:
        data.append([Paragraph(esc(str(c)), CellBody) for c in r])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, 0), 1, GOLD),
        ('GRID', (0, 0), (-1, -1), 0.25, HexColor('#D5DAE8')),
    ]
    for i in range(1, len(data)):
        bg = WHITE if i % 2 == 1 else BOXBG
        style.append(('BACKGROUND', (0, i), (-1, i), bg))
    t.setStyle(TableStyle(style))
    return t

def chapter_head(num, title):
    return [
        Paragraph('CHAPTER %s' % num, ChapterNum),
        Paragraph(esc(title), ChapterTitle),
        HRFlowable(width=USABLE, thickness=2, color=GOLD, spaceBefore=4, spaceAfter=12),
    ]

def layman(text):
    return Paragraph('<i><font color="#C9A84C">In plain terms:</font> %s</i>' % esc(text),
        ParagraphStyle('layman', fontName='Helvetica-Oblique', fontSize=10,
            textColor=GRAY, leading=15, spaceAfter=8))

def body(text):
    return Paragraph(text, Body)

def spacer(h=8):
    return Spacer(1, h)

# ---------------------------------------------------------------------------
# Cover page (drawn directly on canvas of page 1) + footer on all pages
# ---------------------------------------------------------------------------
class DocCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._saved_page_states)
        for i, state in enumerate(self._saved_page_states):
            self.__dict__.update(state)
            self._pageNumber = i + 1
            if i == 0:
                self.draw_cover()
            else:
                self.draw_footer()
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_footer(self):
        self.saveState()
        self.setStrokeColor(GOLD)
        self.setLineWidth(0.5)
        self.line(50, 35, 545, 35)
        self.setFont('Helvetica', 8)
        self.setFillColor(GRAY)
        self.drawCentredString(
            297.5, 22,
            'CALL-E Vendor Discovery Agent — Page %d' % self._pageNumber)
        self.restoreState()

    def draw_cover(self):
        self.saveState()
        cx = PAGE_W / 2
        # full page navy background
        self.setFillColor(NAVY)
        self.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
        # thin gold frame
        self.setStrokeColor(GOLD)
        self.setLineWidth(1.2)
        self.rect(28, 28, PAGE_W - 56, PAGE_H - 56, stroke=1, fill=0)
        # logo
        self.setFillColor(GOLD)
        self.setFont('Helvetica-Bold', 48)
        self.drawCentredString(cx, 560, 'CALL-E')
        # subtitle
        self.setFillColor(white)
        self.setFont('Helvetica', 20)
        self.drawCentredString(cx, 522, 'Vendor Discovery & Outreach Agent')
        # tagline
        self.setFillColor(HexColor('#B8C0D8'))
        self.setFont('Helvetica-Oblique', 13)
        self.drawCentredString(cx, 490, 'Find vendors. Call them. Close deals. Automatically.')
        # gold divider
        self.setStrokeColor(GOLD)
        self.setLineWidth(1.5)
        self.line(cx - 120, 465, cx + 120, 465)
        # reference label
        self.setFillColor(white)
        self.setFont('Helvetica-Bold', 12)
        self.drawCentredString(cx, 300, 'Complete System Reference')
        # hackathon
        self.setFillColor(HexColor('#B8C0D8'))
        self.setFont('Helvetica', 10)
        self.drawCentredString(cx, 270, 'CALL-E Hackathon 2026  ·  AIRUDDER Pte Ltd')
        self.drawCentredString(cx, 254, 'August 10, 2026')
        # bottom gold line
        self.setStrokeColor(GOLD)
        self.setLineWidth(0.5)
        self.line(80, 90, PAGE_W - 80, 90)
        self.setFillColor(GRAY)
        self.setFont('Helvetica-Oblique', 8)
        self.drawCentredString(cx, 74,
            'Free-tier only · Groq · CALL-E CLI · OpenStreetMap · SQLite')
        self.restoreState()

# ---------------------------------------------------------------------------
# Build story
# ---------------------------------------------------------------------------
story = []

# Page 1 cover placeholder (canvas draws it) -> break to real content
story.append(Spacer(1, 1))
story.append(PageBreak())

# ---- Page 2: Table of Contents ----
story.append(section_header('Table of Contents'))
story.append(spacer(12))
toc = [
    (1, 'What Is This?'),
    (2, 'System Architecture'),
    (3, 'Vendor Discovery Engine'),
    (4, 'AI Scoring'),
    (5, 'Automated Calling Pipeline'),
    (6, 'Smart Retry & Scheduling'),
    (7, 'WhatsApp & SMS Messaging'),
    (8, 'Dashboard & Analytics'),
    (9, 'Database Schema'),
    (10, 'End-to-End Campaign Lifecycle'),
    (11, 'Features — Wave 1 & Wave 2'),
    (12, 'Quick Reference'),
]
for n, title in toc:
    story.append(Paragraph(
        '<font color="#C9A84C"><b>Chapter %d</b></font>&nbsp;&nbsp;&mdash;&nbsp;&nbsp;%s' % (n, esc(title)),
        TOCEntry))
story.append(PageBreak())

# ---- Chapter 1 ----
story += chapter_head(1, 'What Is This?')
story.append(quote_box(
    'Imagine having an AI sales assistant that automatically finds local suppliers, '
    'calls them, negotiates terms, and follows up by WhatsApp — all without you '
    'doing anything.'))
story.append(spacer(6))
story.append(Paragraph('The Problem', SubHeader))
story.append(body(
    'B2B vendor discovery is <b>manual, slow and expensive</b>. A procurement team '
    'searches directories by hand, copies phone numbers, dials one supplier at a time, '
    'repeats itself on every call, and loses track of who to follow up with. Most leads '
    'never even get a second attempt.'))
story.append(Paragraph('The Solution', SubHeader))
story.append(body(
    'CALL-E is an <b>end-to-end automated pipeline</b>. You describe a product and a '
    'location; the system discovers matching vendors from OpenStreetMap, scores them with '
    'AI, phones each one with a real voice agent, classifies the outcome, retries the '
    'no-answers at smart intervals, falls back to WhatsApp/SMS when calls fail, and shows '
    'everything live on a web dashboard. You only step in at the very end to close deals '
    'with vendors already marked <i>positive</i>.'))
story.append(spacer(4))
story.append(keyfacts_box('Key Facts', [
    'Free tier only — Groq (llama-3.3-70b), CALL-E CLI, OpenStreetMap / Overpass / Nominatim.',
    'Storage is a single SQLite file (vendor_discovery.db) — no server database required.',
    'Built with Python (pipeline + Flask) and Node.js (CALL-E CLI + Baileys WhatsApp).',
    'Runs on any laptop — no cloud infrastructure, no paid API keys needed to start.',
]))
story.append(PageBreak())

# ---- Chapter 2 ----
story += chapter_head(2, 'System Architecture')
story.append(layman('Six departments, one factory. Each stage hands its work to the next.'))
story.append(diagram_box([
    "+---------------------------------------------------------+",
    "|              CALL-E SYSTEM ARCHITECTURE                 |",
    "+--------------+--------------+--------------+------------+",
    "| DISCOVERY    | SCORING      | CALLER       | SCHEDULER  |",
    "| OSM/Overpass | Groq AI      | CALL-E CLI   | Retry      |",
    "| Nominatim    | llama-3.3    | plan->run    | Ladder     |",
    "| Phone norm   | 70b-versatile| ->status     | Biz hours  |",
    "+------+-------+------+-------+------+-------+-----+------+",
    "       |              |             |             |",
    "       +--------------+------+------+-------------+",
    "                             v",
    "              +--------------------------+",
    "              |    FLASK DASHBOARD       |",
    "              |  Leads  .  Analytics     |",
    "              |  Map (Leaflet) . Live SSE|",
    "              +--------------------------+",
    "                             v",
    "              +--------------------------+",
    "              |    MESSAGING FALLBACK    |",
    "              |  WhatsApp (Baileys)      |",
    "              |  Fast2SMS . Twilio . Mock|",
    "              +--------------------------+",
]))
story.append(spacer(10))
story.append(Paragraph('Technology Stack', SubHeader))
story.append(feature_table(
    ['Component', 'Technology'],
    [
        ['Vendor discovery', 'OpenStreetMap Overpass API + Nominatim geocoding'],
        ['AI scoring & inference', 'Groq API · llama-3.3-70b-versatile (free tier)'],
        ['Voice calling', 'CALL-E CLI (@calle-ai/cli) plan → run → status'],
        ['Scheduling & retries', 'Python threading background poller + SQLite'],
        ['Web dashboard', 'Flask + Chart.js + Leaflet.js + Server-Sent Events'],
        ['Messaging fallback', 'Baileys (WhatsApp) · Fast2SMS · Twilio · Mock'],
        ['Persistence', 'SQLite (vendor_discovery.db)'],
        ['Exports', 'openpyxl (Excel) · CSV · JSON'],
    ],
    [140, 355]))
story.append(PageBreak())

# ---- Chapter 3 ----
story += chapter_head(3, 'Vendor Discovery Engine')
story.append(layman(
    'Like Google Maps, but it finds suppliers and extracts their phone numbers.'))
story.append(Paragraph('How Overpass Works', SubHeader))
story.append(body(
    'A product keyword is mapped to OpenStreetMap tags (for example "grocery" → '
    '<font face="Courier">shop=supermarket</font>). The engine then queries the Overpass '
    'API for nodes and ways carrying those tags <b>and</b> a phone tag, within either a '
    'bounding box (from Nominatim) or an <font face="Courier">around:</font> radius centred '
    'on the location. Unknown keywords are mapped to tags by Groq before falling back to a '
    'free-text name search. Three Overpass mirrors are tried in turn for resilience.'))
story.append(diagram_box([
    "[out:json][timeout:60];",
    "(",
    '  node[\"shop\"=\"supermarket\"][\"phone\"](s,w,n,e);',
    '  node[\"shop\"=\"supermarket\"][\"contact:phone\"](s,w,n,e);',
    '  way[\"shop\"=\"supermarket\"][\"phone\"](s,w,n,e);',
    ");",
    "out body center qt 60;",
]))
story.append(spacer(8))
story.append(Paragraph('Phone Normalization', SubHeader))
story.append(body(
    'Raw OSM numbers are messy. The normalizer strips every non-digit (keeping a leading '
    '<font face="Courier">+</font>), then handles the common case where OSM concatenates '
    'two numbers like <font face="Courier">+91XXXXXXXXXX+91YYYYYYYYYY</font> by splitting on '
    'the second <font face="Courier">+</font> boundary and keeping the first segment. A '
    'spam filter rejects numbers under 8 digits or with two or fewer distinct digits.'))
story.append(Paragraph('Geocoding & Deduplication', SubHeader))
story.append(body(
    'Nominatim resolves the location string to a bounding box or centre point; tiny '
    'point-boxes are expanded to ~2&nbsp;km. Each vendor carries an <font face="Courier">'
    'osm_id</font> (e.g. <font face="Courier">node/12345</font>); duplicate phone numbers '
    'are dropped during discovery, and on save the pipeline skips any phone already present '
    'in the database so the same vendor is never added twice.'))
story.append(PageBreak())

# ---- Chapter 4 ----
story += chapter_head(4, 'AI Scoring')
story.append(layman(
    'Before calling anyone, the AI reads the vendor profile and ranks who is worth '
    'calling first.'))
story.append(Paragraph('Model & Signals', SubHeader))
story.append(body(
    'Lead quality is scored from the richness of the OpenStreetMap record, then AI '
    'inference (Groq <font face="Courier">llama-3.3-70b-versatile</font>, free tier ~14,400 '
    'requests/day) refines priorities after the first call. The base score rewards data '
    'completeness so well-documented vendors are dialled first.'))
story.append(feature_table(
    ['Signal', 'Points', 'Why It Matters'],
    [
        ['Exact category match', '+20', 'Vendor genuinely sells the product'],
        ['Has website', '+15', 'Established, contactable business'],
        ['Has name', '+10', 'Identifiable on the call'],
        ['Complete address (3+/4)', '+10', 'Real physical location'],
        ['Has opening hours', '+10', 'Active, staffed premises'],
        ['Has email', '+5', 'Extra fallback channel'],
        ['(capped at)', '100', 'Maximum lead score'],
    ],
    [175, 60, 260]))
story.append(spacer(8))
story.append(Paragraph('Output & Usage', SubHeader))
story.append(body(
    'Scoring returns a numeric score plus a list of human-readable reasons (e.g. '
    '"has website", "exact category match"), both stored on the lead. Leads are then '
    '<b>sorted by score descending</b> before any calls are placed. After round&nbsp;1, '
    '<font face="Courier">score_from_r1_inference</font> nudges the score up or down using '
    'the AI-detected interest level and sentiment, re-prioritising round&nbsp;2.'))
story.append(PageBreak())

# ---- Chapter 5 ----
story += chapter_head(5, 'Automated Calling Pipeline')
story.append(layman(
    'The system dials the vendor, has a real conversation, and records everything.'))
story.append(diagram_box([
    "call plan  (goal + phone)   -> plan_id + confirm_token",
    "         |",
    "         v",
    "call run   (plan_id + token)-> run_id",
    "         |",
    "         v",
    "call status(run_id) --[poll every 15s, max 40 polls]--> done",
    "         |",
    "         v",
    "classify:  positive / negative / unknown / no_answer",
]))
story.append(spacer(10))
story.append(Paragraph('Pipeline Flow', SubHeader))
story.append(body(
    'The CALL-E CLI is wrapped as a subprocess. <font face="Courier">plan</font> produces a '
    '<font face="Courier">plan_id</font> and a <font face="Courier">confirm_token</font> '
    '(a deliberate human/consent gate); <font face="Courier">run</font> starts the call and '
    'returns a <font face="Courier">run_id</font>; <font face="Courier">status</font> is '
    'polled every 15&nbsp;seconds up to 40 times (a 10-minute ceiling) until a terminal '
    'status. A business-hours gate can skip the call entirely before planning.'))
story.append(Paragraph('Resilience: Fetch Retry Budget', SubHeader))
story.append(body(
    'Transient <font face="Courier">"fetch failed"</font> errors during polling are '
    'retried up to <b>3 times</b> per cycle before the error is raised; a successful poll '
    'resets the counter. Each poll also publishes a live event (status + parsed transcript '
    '+ summary) onto the SSE queue for the dashboard.'))
story.append(Paragraph('classify_round1 Logic', SubHeader))
story.append(body(
    'Outcome classification uses CALL-E’s own status first (NO_ANSWER/BUSY/DECLINED '
    '→ <font face="Courier">no_answer</font>; FAILED → '
    '<font face="Courier">failed</font>). A <font face="Courier">callback_requested</font> '
    'flag or a <font face="Courier">report_blocked</font> next-step is treated as '
    '<b>positive</b> (the vendor wants a call back). Otherwise '
    '<font face="Courier">outcome.task_completed</font> decides positive/negative, and a '
    'transcript keyword scan is the final fallback — inconclusive calls return '
    '<font face="Courier">unknown</font>.'))
story.append(PageBreak())

# ---- Chapter 6 ----
story += chapter_head(6, 'Smart Retry & Scheduling')
story.append(layman(
    'If no one picks up, the system tries again later at the right time.'))
story.append(diagram_box([
    "Call attempt 1 (immediate)",
    "    +- no answer / unknown -> +30 min",
    "         +- no answer / unknown -> +2 hours",
    "              +- no answer / unknown -> +24 hours",
    "                   +- exhausted -> send WhatsApp / SMS fallback",
]))
story.append(spacer(10))
story.append(Paragraph('Retry Ladder', SubHeader))
story.append(body(
    'A no-answer, busy, failed or <b>unknown</b> outcome schedules the next round-1 attempt '
    'using an escalating delay ladder (<font face="Courier">+30&nbsp;min → +2&nbsp;h '
    '→ +24&nbsp;h</font>). The lead’s '
    '<font face="Courier">retry_count</font> advances each time; once the ladder is '
    'exhausted the lead is marked <font face="Courier">exhausted</font> and an SMS/WhatsApp '
    'fallback is sent. A background thread polls every 10&nbsp;seconds and claims each due '
    'row atomically (<font face="Courier">pending → in_progress</font>) to prevent '
    'double-firing.'))
story.append(Paragraph('Business-Hours Gate', SubHeader))
story.append(body(
    'Calls are gated to local business hours (Mon–Fri, 09:00–18:00) using the '
    'timezone resolved from the vendor’s lat/lon. Outside those hours the pipeline '
    'returns <font face="Courier">SKIPPED</font>. Vendor-requested callbacks are honoured '
    'regardless of the gate, since the vendor themselves named the time.'))
story.append(Paragraph('Outcome Routing', SubHeader))
story.append(feature_table(
    ['Outcome', 'Action'],
    [
        ['positive', 'Mark positive; schedule round-2 data-capture call'],
        ['negative', 'Mark negative; close the lead'],
        ['unknown', 'Retry like no-answer (inconclusive call)'],
        ['no_answer / busy / failed', 'Retry via ladder; SMS fallback when exhausted'],
    ],
    [180, 315]))
story.append(spacer(6))
story.append(Paragraph(
    'The <font face="Courier">scheduled_calls</font> table stores '
    '<font face="Courier">lead_id</font>, <font face="Courier">scheduled_at</font>, '
    '<font face="Courier">round</font> and status for every queued attempt.', Caption))
story.append(PageBreak())

# ---- Chapter 7 ----
story += chapter_head(7, 'WhatsApp & SMS Messaging')
story.append(layman(
    'When all calls fail, a polite WhatsApp message goes out automatically.'))
story.append(diagram_box([
    "SMS_PROVIDER env var",
    "    |-- whatsapp -> Baileys (Node.js, localhost:3001, free after QR)",
    "    |-- fast2sms -> Fast2SMS API (Indian numbers, needs recharge)",
    "    |-- twilio   -> Twilio API (global, paid)",
    "    +-- mock     -> logs only, no real send",
]))
story.append(spacer(10))
story.append(Paragraph('Provider Selection', SubHeader))
story.append(body(
    'The <font face="Courier">SMS_PROVIDER</font> environment variable chooses the channel '
    '(default <font face="Courier">fast2sms</font>). Missing credentials degrade gracefully '
    'to the mock provider so the pipeline never crashes on a failed send. Every send — '
    'real or mock — is written to the <font face="Courier">messages</font> table with '
    'its phone, body, provider and status.'))
story.append(Paragraph('Baileys WhatsApp Server', SubHeader))
story.append(body(
    'A companion Node.js REST server (<font face="Courier">whatsapp_server.js</font>) runs '
    'on <font face="Courier">localhost:3001</font> and is authenticated once by scanning a '
    'QR code — free forever afterwards. It exposes '
    '<font face="Courier">/status</font>, <font face="Courier">/send</font>, '
    '<font face="Courier">/send-sticker</font> and <font face="Courier">/inbox</font> '
    'endpoints; the Python side POSTs JSON to <font face="Courier">/send</font>.'))
story.append(Paragraph('send_sms vs send_sms_text', SubHeader))
story.append(body(
    '<font face="Courier">send_sms()</font> composes a polite vendor-fallback message from '
    'the product name and is used automatically when retries are exhausted. '
    '<font face="Courier">send_sms_text()</font> sends an arbitrary body through the same '
    'provider layer, for ad-hoc or dashboard-triggered messages. Fast2SMS strips the country '
    'code and only sends to 10-digit Indian numbers, skipping others cleanly.'))
story.append(PageBreak())

# ---- Chapter 8 ----
story += chapter_head(8, 'Dashboard & Analytics')
story.append(layman(
    'A live web app that shows everything — like mission control for your sales team.'))
story.append(feature_table(
    ['Tab', 'What It Shows', 'Key Features'],
    [
        ['Leads', 'All vendors found, their status and call history',
         'Search, filter, expand-row transcript, status badges, reliability score'],
        ['Analytics', 'Charts of outcomes and call volume',
         'Chart.js donut + bars, interest & sentiment, price intelligence'],
        ['Map', 'Geographic view of vendors',
         'Leaflet.js; answered calls = larger pulse markers; transcript popup; legend'],
        ['Live Console', 'Real-time call events as they happen',
         'SSE stream, run_id tracking, live status line'],
    ],
    [90, 175, 230]))
story.append(spacer(10))
story.append(Paragraph('Live Console (SSE) Architecture', SubHeader))
story.append(body(
    'Each active call registers a <font face="Courier">queue.Queue</font> keyed by its '
    '<font face="Courier">run_id</font>. The poller publishes status/transcript/summary '
    'events onto that queue, and Flask streams them to the browser with '
    '<font face="Courier">stream_with_context</font> over '
    '<font face="Courier">/live-stream/&lt;run_id&gt;</font> using Server-Sent Events — '
    'no polling, no websockets.'))
story.append(Paragraph('Auto-Refresh & State', SubHeader))
story.append(body(
    'The dashboard refreshes on an 8-second interval. Expanded transcript rows keep their '
    'open/closed state across refreshes, so a panel you opened stays open while data '
    'updates underneath it. Status and reliability badges are colour-coded per lead.'))
story.append(PageBreak())

# ---- Chapter 9 ----
story += chapter_head(9, 'Database Schema')
story.append(layman(
    'Everything is stored in one small file — like a spreadsheet that never forgets.'))
story.append(diagram_box([
    "campaigns ------------------------------+",
    "  id, product_description, location,    |",
    "  goal_script, consent_basis, created_at|",
    "         | 1                            |",
    "         | oo                           |",
    "       leads --------------------------+|",
    "  id, campaign_id, osm_id, name,       ||",
    "  phone, masked_phone, address,        ||",
    "  lat, lon, lead_score, status,        ||",
    "  retry_count                          ||",
    "         | 1          | 1              ||",
    "         | oo         | oo             ||",
    "    call_logs    scheduled_calls       ||",
    "    call_id      scheduled_at          ||",
    "    round        round, timezone       ||",
    "    raw_status   status, goal_script   ||",
    "                                messages||",
    "                     lead_id, body,    ||",
    "                     provider, status  ||",
    "templates (id, name, goal_script, ...) ||",
    "---------------------------------------++",
]))
story.append(spacer(10))
story.append(Paragraph('Core Tables', SubHeader))
story.append(feature_table(
    ['Column', 'Type', 'Purpose'],
    [
        ['campaigns.product_description', 'TEXT', 'What is being sourced'],
        ['campaigns.location', 'TEXT', 'Search area string'],
        ['campaigns.consent_basis', 'TEXT', 'Client-approved calling basis'],
        ['leads.phone / masked_phone', 'TEXT', 'E.164 number + masked display'],
        ['leads.osm_id', 'TEXT', 'OpenStreetMap identity (dedup)'],
        ['leads.lead_score', 'REAL', 'Quality score for call ordering'],
        ['leads.status', 'TEXT', 'not_called / positive / completed / ...'],
        ['leads.retry_count', 'INTEGER', 'Retry-ladder position'],
        ['call_logs.round', 'INTEGER', '1 = qualify, 2 = data capture'],
        ['call_logs.raw_status_output', 'TEXT', 'Full CALL-E status JSON'],
        ['scheduled_calls.scheduled_at', 'TEXT', 'UTC time the call is due'],
        ['scheduled_calls.round', 'INTEGER', 'Which round this retry is for'],
        ['messages.provider', 'TEXT', 'whatsapp / fast2sms / twilio / mock'],
        ['templates.goal_script', 'TEXT', 'Reusable call script'],
    ],
    [200, 65, 230]))
story.append(PageBreak())

# ---- Chapter 10 ----
story += chapter_head(10, 'End-to-End Campaign Lifecycle')
story.append(layman(
    'Here is the full journey from "find me vendors" to "deal closed".'))
story.append(diagram_box([
    " 1. User creates campaign: product + location + radius",
    " 2. Discovery: OSM Overpass pulls vendors -> normalize phones -> geocode",
    " 3. Scoring: Groq AI + OSM richness scores each vendor",
    " 4. Queue: leads sorted by score, added to scheduled_calls",
    " 5. Caller: CALL-E dials vendor -> conversation -> transcript",
    " 6. Classify: positive / negative / unknown / no_answer",
    " 7. Retry: unknown / no_answer -> scheduled retry (+30m/+2h/+24h)",
    " 8. Fallback: exhausted -> WhatsApp / SMS message sent",
    " 9. Dashboard: live map + table updated in real time",
    "10. User: contacts the 'positive' leads and closes the deal",
]))
story.append(spacer(10))
story.append(body(
    'Positive round-1 leads flow into a round-2 data-capture call that extracts structured '
    'fields (can-supply, quantity, price range, currency, timeline, next steps) via AI '
    'inference over the transcript. Results are shown on the dashboard and can be exported '
    'to Excel, CSV or JSON, with an optional email report at the end of the campaign.'))
story.append(PageBreak())

# ---- Chapter 11 ----
story += chapter_head(11, 'Features — Wave 1 & Wave 2')
story.append(body(
    'The system was built in two phases. <b>Wave&nbsp;1</b> delivered the core '
    'discover→score→call→retry pipeline; <b>Wave&nbsp;2</b> added real-time '
    'visibility, messaging, and a series of correctness fixes hardened against real OSM '
    'and CALL-E data.'))
story.append(Paragraph('Wave 1 — Core Pipeline', SubHeader))
story.append(feature_table(
    ['Feature', 'Description'],
    [
        ['Discovery Engine', 'OSM Overpass + Nominatim vendor search with phone extraction'],
        ['AI Scoring', 'OSM-richness lead score, sorted before calling'],
        ['Automated Calling', 'CALL-E plan → run → status pipeline with polling'],
        ['Retry Scheduling', 'Escalating retry ladder with business-hours gate'],
        ['Basic Dashboard', 'Flask leads table with status and results'],
    ],
    [150, 345]))
story.append(spacer(8))
story.append(Paragraph('Wave 2 — Enhancements & Fixes', SubHeader))
story.append(feature_table(
    ['Feature', 'Description'],
    [
        ['SSE Live Console', 'Real-time call events streamed to the browser'],
        ['Map Markers', 'Answered calls shown as pulsing Leaflet markers'],
        ['Expand-Row Persistence', 'Transcript panel stays open across refreshes'],
        ['WhatsApp Integration', 'Baileys server; sticker sending; inbox reading'],
        ['Fast2SMS', 'Indian SMS fallback via API'],
        ['Reliability Badges', 'Retry count + last attempt shown per lead'],
        ['Template UI', 'Manage call script templates from the dashboard'],
        ['Geocoding Fix', 'Nominatim batch geocode for leads missing lat/lon'],
        ['Fetch Retry Budget', 'Transient CALL-E errors retried 3x before failing'],
        ['report_blocked Fix', 'Correctly classified as a positive outcome'],
        ['Unknown → Retry', 'Inconclusive calls now retry instead of closing'],
        ['Concat Phone Fix', 'OSM numbers like +91X+91Y now split correctly'],
    ],
    [150, 345]))
story.append(PageBreak())

# ---- Chapter 12 ----
story += chapter_head(12, 'Quick Reference')
story.append(Paragraph('Required Environment Variables', SubHeader))
story.append(feature_table(
    ['Variable', 'Purpose', 'How to Set'],
    [
        ['GROQ_API_KEY', 'AI scoring, inference, time parsing', 'console.groq.com (free tier)'],
        ['SMS_PROVIDER', 'Choose messaging channel', 'whatsapp | fast2sms | twilio | mock'],
        ['FAST2SMS_API_KEY', 'Indian SMS fallback', 'fast2sms.com dashboard'],
        ['TWILIO_ACCOUNT_SID', 'Twilio auth (optional)', 'twilio.com console'],
        ['TWILIO_AUTH_TOKEN', 'Twilio auth (optional)', 'twilio.com console'],
        ['TWILIO_FROM_NUMBER', 'Twilio sender number', 'twilio.com console'],
    ],
    [150, 175, 170]))
story.append(spacer(10))
story.append(Paragraph('Start Commands', SubHeader))
story.append(diagram_box([
    "# Start Flask dashboard",
    "python main.py            -> http://127.0.0.1:5000",
    "",
    "# Start WhatsApp server (scan QR on first run)",
    "node whatsapp_server.js   -> http://localhost:3001",
    "",
    "# Re-authenticate CALL-E",
    "calle auth login",
]))
story.append(spacer(10))
story.append(Paragraph('CALL-E CLI Reference', SubHeader))
story.append(feature_table(
    ['Command', 'Purpose'],
    [
        ['call plan', 'Generate a call script/plan from a goal + phone'],
        ['call run', 'Execute the planned call (needs plan_id + confirm_token)'],
        ['call status', 'Poll for the call result by run_id'],
        ['calle auth login', 'Re-authenticate the CALL-E CLI'],
    ],
    [150, 345]))
story.append(spacer(14))
story.append(HRFlowable(width=USABLE, thickness=1, color=GOLD))
story.append(spacer(6))
story.append(Paragraph(
    'CALL-E Vendor Discovery &amp; Outreach Agent · Complete System Reference · '
    'CALL-E Hackathon 2026 · AIRUDDER Pte Ltd. Data © OpenStreetMap contributors (ODbL).',
    Caption))

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
doc = SimpleDocTemplate(
    OUT_PATH, pagesize=A4,
    leftMargin=MARGIN, rightMargin=MARGIN,
    topMargin=MARGIN, bottomMargin=MARGIN + 8,
    title='CALL-E Vendor Discovery & Outreach Agent',
    author='CALL-E Hackathon 2026')
doc.build(story, canvasmaker=DocCanvas)
print('PDF written to', OUT_PATH)
