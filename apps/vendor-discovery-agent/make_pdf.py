"""Generates a layman-friendly but detailed PDF description of the Vendor Discovery pipeline."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable, KeepTogether)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

OUT = r"C:\Users\rj02a\OneDrive\Desktop\calle\VendorAgent_Description.pdf"

# ── Colours ──────────────────────────────────────────────────────────────────
C_DARK_BLUE  = HexColor("#1a3a6b")
C_BLUE       = HexColor("#1a73e8")
C_LIGHT_BLUE = HexColor("#d0e8ff")
C_GREEN      = HexColor("#1a6b3c")
C_LIGHT_GRN  = HexColor("#d4edda")
C_ORANGE     = HexColor("#b85c00")
C_LIGHT_ORG  = HexColor("#ffecd0")
C_PURPLE     = HexColor("#5b2fa0")
C_LIGHT_PUR  = HexColor("#ede0ff")
C_GREY       = HexColor("#f5f7fa")
C_MID_GREY   = HexColor("#6c757d")
C_DARK       = HexColor("#1a1a2e")
C_RULE       = HexColor("#dee2e6")

W = 155 * mm  # usable width

# ── Styles (use unique names to avoid collisions) ────────────────────────────
_BASE = getSampleStyleSheet()["Normal"]

def ps(name, **kw):
    return ParagraphStyle(name, parent=_BASE, **kw)

S_TITLE    = ps("s_title",  fontSize=24, fontName="Helvetica-Bold",
                textColor=white, leading=30)
S_SUBTITLE = ps("s_sub",    fontSize=12, fontName="Helvetica-Oblique",
                textColor=HexColor("#b0c8ff"), leading=17)
S_FOOTLINE = ps("s_foot",   fontSize=9,  textColor=HexColor("#8ab0ff"), leading=13)
S_H1       = ps("s_h1",     fontSize=18, fontName="Helvetica-Bold",
                textColor=C_DARK, leading=24, spaceBefore=10, spaceAfter=4)
S_H2       = ps("s_h2",     fontSize=14, fontName="Helvetica-Bold",
                textColor=C_BLUE, leading=19, spaceBefore=10, spaceAfter=3)
S_H3       = ps("s_h3",     fontSize=11, fontName="Helvetica-Bold",
                textColor=C_DARK, leading=15, spaceBefore=6, spaceAfter=2)
S_BODY     = ps("s_body",   fontSize=10, leading=15, textColor=C_DARK,
                spaceAfter=5, alignment=TA_JUSTIFY)
S_SMALL    = ps("s_small",  fontSize=9,  leading=13, textColor=C_MID_GREY,
                spaceAfter=4, alignment=TA_JUSTIFY)
S_BULLET   = ps("s_bullet", fontSize=10, leading=15, textColor=C_DARK,
                leftIndent=14, spaceAfter=2)
S_CELL     = ps("s_cell",   fontSize=9,  leading=13, textColor=C_DARK)
S_CELL_HD  = ps("s_cellhd", fontSize=9,  leading=13, fontName="Helvetica-Bold",
                textColor=white)
S_CELL_B   = ps("s_cellb",  fontSize=9,  leading=13, fontName="Helvetica-Bold",
                textColor=C_DARK)
S_CENTER   = ps("s_ctr",    fontSize=9,  leading=13, textColor=C_DARK,
                alignment=TA_CENTER)
S_FTR      = ps("s_ftr",    fontSize=8,  textColor=C_MID_GREY,
                alignment=TA_CENTER)

def hr():
    return HRFlowable(width="100%", thickness=0.5,
                      color=C_RULE, spaceAfter=6, spaceBefore=6)

def pad(top=6, bot=6, left=8, right=8):
    return [
        ("TOPPADDING",    (0,0), (-1,-1), top),
        ("BOTTOMPADDING", (0,0), (-1,-1), bot),
        ("LEFTPADDING",   (0,0), (-1,-1), left),
        ("RIGHTPADDING",  (0,0), (-1,-1), right),
    ]

# ── Helper: coloured banner box ───────────────────────────────────────────────
def banner(rows_content, bg, pad_top=10, pad_bot=10, pad_lr=14):
    """rows_content = list of Paragraph objects; one per row, same bg colour."""
    data = [[p] for p in rows_content]
    t = Table(data, colWidths=[W])
    cmds = [
        ("BACKGROUND",    (0,0), (-1,-1), bg),
        ("TOPPADDING",    (0,0), (-1,0),  pad_top),
        ("BOTTOMPADDING", (0,-1),(-1,-1), pad_bot),
        ("TOPPADDING",    (0,1), (-1,-2), 2),
        ("BOTTOMPADDING", (0,0), (-1,-2), 2),
        ("LEFTPADDING",   (0,0), (-1,-1), pad_lr),
        ("RIGHTPADDING",  (0,0), (-1,-1), pad_lr),
    ]
    t.setStyle(TableStyle(cmds))
    return t

# ── Helper: section box (title row + body rows, bordered) ────────────────────
def section_box(title, body_paras, bg=C_GREY, title_color=C_DARK):
    title_style = ps(f"sb_t_{title[:8].replace(' ','_')}",
                     fontSize=11, fontName="Helvetica-Bold",
                     textColor=title_color, leading=15)
    data = [[Paragraph(title, title_style)]]
    for p in body_paras:
        data.append([p])
    t = Table(data, colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  bg),
        ("BACKGROUND",    (0,1), (-1,-1), white),
        ("BOX",           (0,0), (-1,-1), 0.7, C_RULE),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING",   (0,0), (-1,-1), 12),
        ("RIGHTPADDING",  (0,0), (-1,-1), 12),
    ]))
    return KeepTogether([t, Spacer(1, 8)])

# ── Helper: numbered flow steps ───────────────────────────────────────────────
def flow_table(steps):
    """steps = [(number, title, description, color)]
    Each step = 2 rows: [num | title] then ['' | desc]
    """
    data = []
    for num, title, desc, col in steps:
        n_style = ps(f"fn{num}", fontSize=13, fontName="Helvetica-Bold",
                     textColor=white, alignment=TA_CENTER, leading=16)
        t_style = ps(f"ft{num}", fontSize=10, fontName="Helvetica-Bold",
                     textColor=C_DARK, leading=14)
        d_style = ps(f"fd{num}", fontSize=9, textColor=HexColor("#444444"), leading=13)
        data.append([Paragraph(str(num), n_style), Paragraph(title, t_style)])
        data.append([Paragraph("", S_SMALL),        Paragraph(desc, d_style)])

    col_w = [14*mm, W - 14*mm]
    t = Table(data, colWidths=col_w)
    cmds = [
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (0,-1), 3),
        ("LEFTPADDING",   (1,0), (1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
    ]
    # colour the number cells (every even row = title row)
    for i, (_, _, _, col) in enumerate(steps):
        r = i * 2
        cmds.append(("BACKGROUND", (0,r), (0,r+1), col))
        cmds.append(("BACKGROUND", (1,r), (1,r),   C_GREY))
        if i < len(steps) - 1:
            cmds.append(("LINEBELOW", (0, r+1), (-1, r+1), 0.4, C_RULE))
    t.setStyle(TableStyle(cmds))
    return KeepTogether([t, Spacer(1, 8)])

# ── Helper: two-column comparison table ───────────────────────────────────────
def two_col(left_items, right_items, left_title, right_title, l_bg, r_bg):
    col_w = (W - 4*mm) / 2
    # Build header row + item rows for left and right combined
    rows = [[
        Paragraph(left_title,  ps("lh", fontSize=9, fontName="Helvetica-Bold", textColor=white, leading=13)),
        Paragraph(right_title, ps("rh", fontSize=9, fontName="Helvetica-Bold", textColor=white, leading=13)),
    ]]
    max_rows = max(len(left_items), len(right_items))
    for i in range(max_rows):
        l = left_items[i]  if i < len(left_items)  else ""
        r = right_items[i] if i < len(right_items) else ""
        rows.append([Paragraph(l, S_CELL), Paragraph(r, S_CELL)])

    t = Table(rows, colWidths=[col_w, col_w])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (0,0),   l_bg),
        ("BACKGROUND",    (1,0), (1,0),   r_bg),
        ("BOX",           (0,0), (-1,-1), 0.5, C_RULE),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, C_RULE),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_GREY, white]),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    return KeepTogether([t, Spacer(1, 10)])

# ── Helper: simple data table ─────────────────────────────────────────────────
def data_table(rows_raw, col_widths, header_bg):
    data = []
    for ri, row in enumerate(rows_raw):
        style_ = S_CELL_HD if ri == 0 else S_CELL
        data.append([Paragraph(str(c), style_) for c in row])
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  header_bg),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_GREY, white]),
        ("BOX",           (0,0), (-1,-1), 0.5, C_RULE),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, C_RULE),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 7),
        ("RIGHTPADDING",  (0,0), (-1,-1), 7),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    return KeepTogether([t, Spacer(1, 10)])

# ============================================================
#  BUILD STORY
# ============================================================
doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=25*mm, rightMargin=25*mm,
    topMargin=20*mm, bottomMargin=20*mm,
)
story = []

# ── Title banner ─────────────────────────────────────────────────────────────
story.append(banner([
    Paragraph("Vendor Discovery &amp; Outreach Agent", S_TITLE),
    Paragraph("A plain-English guide to how the system finds vendors,<br/>"
              "writes call scripts, and runs AI-powered phone outreach", S_SUBTITLE),
    Spacer(1, 4),
    Paragraph("Built for the CALL-E Hackathon &nbsp;|&nbsp; "
              "Powered by CALL-E + OpenStreetMap + Groq AI", S_FOOTLINE),
], bg=C_DARK_BLUE, pad_top=18, pad_bot=18))
story.append(Spacer(1, 14))

# ── What is this ─────────────────────────────────────────────────────────────
story.append(Paragraph("What Is This?", S_H2))
story.append(Paragraph(
    "The Vendor Discovery &amp; Outreach Agent is a software pipeline that does in minutes "
    "what normally takes a sourcing team days: it <b>finds local businesses</b> that could "
    "supply a product, <b>calls them automatically</b> to qualify their interest, and "
    "<b>collects pricing and availability details</b> in a second round — all without a "
    "human picking up the phone. Every vendor, every call, and every extracted data point "
    "is saved in a database and shown on a live web dashboard.", S_BODY))

story.append(section_box(
    "The One-Sentence Summary",
    [Paragraph(
        "You type a product name and a city. The system finds up to 20 vendors on "
        "OpenStreetMap, calls each one using an AI voice agent, and returns a structured "
        "table of who is interested, what they can supply, and at what price.",
        ps("oss", fontSize=11, fontName="Helvetica-Bold", leading=16,
           textColor=C_DARK_BLUE))],
    bg=C_LIGHT_BLUE))

# ── Problem it solves ─────────────────────────────────────────────────────────
story.append(Paragraph("The Problem It Solves", S_H2))
story.append(two_col(
    left_items=[
        "Manually searching maps and directories for every vendor",
        "Copy-pasting phone numbers one by one",
        "Calling 20 shops yourself to find 2 that are interested",
        "Typing up call notes after every conversation",
        "Losing track of who said what across 10 browser tabs",
    ],
    right_items=[
        "OSM query returns a ranked list with phones in seconds",
        "Phones validated and formatted to E.164 automatically",
        "CALL-E AI agent calls all vendors and records outcomes",
        "Groq AI reads the transcript and extracts structured data",
        "Everything in one database, visible on a live dashboard",
    ],
    left_title="Without this system",
    right_title="With this system",
    l_bg=HexColor("#c0392b"),
    r_bg=HexColor("#1a6b3c"),
))

# ── Three core modules ────────────────────────────────────────────────────────
story.append(hr())
story.append(Paragraph("The Three Core Modules", S_H1))
story.append(Paragraph(
    "The system is split into three clearly separated modules. Each does one job, "
    "and they connect in a straight pipeline: discover -> script -> call.", S_BODY))
story.append(Spacer(1, 6))

story.append(flow_table([
    (1, "Module 1 — Vendor Discovery  (discovery.py)",
     "Queries OpenStreetMap's global open database to find businesses matching your "
     "product keyword in any city. Filters to only those with verified phone numbers. "
     "Returns name, phone (E.164 format), category, GPS coordinates, and stable OSM ID.",
     C_BLUE),
    (2, "Module 2 — Script Generation  (script_gen.py)",
     "Takes the product description and generates a natural-language goal script for "
     "the CALL-E AI agent. Round 1 qualifies interest; Round 2 collects pricing, "
     "quantities, timelines, and contact names. The client must approve before any call.",
     C_ORANGE),
    (3, "Module 3 — Call Pipeline  (caller.py)",
     "Sends each vendor's phone and the approved script to CALL-E, which plans the "
     "call, dials, and returns a full transcript. The pipeline polls for completion, "
     "then runs Groq AI on the transcript to extract structured intelligence.",
     C_GREEN),
]))

# ── Module 1 detail ───────────────────────────────────────────────────────────
story.append(hr())
story.append(Paragraph("Module 1 — Vendor Discovery in Detail", S_H2))
story.append(Paragraph(
    "<b>Source:</b> OpenStreetMap (OSM) — the world's largest free geographic database, "
    "maintained by millions of contributors and licensed under ODbL.", S_BODY))
story.append(Paragraph(
    "<b>How it works:</b> The system sends a structured query to the Overpass API asking: "
    "<i>'Give me all businesses tagged as a shoe shop / hardware store / etc. that also "
    "have a phone number, within a bounding box around this city.'</i> The bounding box "
    "is automatically calculated from the city name using the Nominatim geocoder.", S_BODY))

story.append(Paragraph("What the query returns per vendor:", S_H3))
for item in [
    "<b>name</b> — Business name as listed in OSM",
    "<b>phone</b> — Reformatted to E.164 international format (+441234567890)",
    "<b>masked_phone</b> — Masked version for safe display (+44****890)",
    "<b>category</b> — OSM tag matched (e.g. shop=shoes, shop=hardware)",
    "<b>lat / lon</b> — GPS coordinates, used for timezone-aware business hours check",
    "<b>candidate_id</b> — Stable URI in the form osm:&lt;id&gt; for audit trails",
]:
    story.append(Paragraph(f"&#8226;  {item}", S_BULLET))
story.append(Spacer(1, 6))

story.append(section_box(
    "Business Hours Gate",
    [Paragraph(
        "Before placing any call, the system resolves the vendor's local timezone using "
        "GPS coordinates. Calls outside Monday-Friday 09:00-18:00 local time are skipped "
        "automatically and logged as 'outside_business_hours'. This prevents calling a "
        "London shop at 3am or a Delhi vendor on a Sunday.", S_BODY)],
    bg=C_LIGHT_ORG, title_color=C_ORANGE))

# ── Module 2 detail ───────────────────────────────────────────────────────────
story.append(Paragraph("Module 2 — Script Generation in Detail", S_H2))
story.append(Paragraph(
    "The AI phone agent needs clear instructions for what to say. These are called a "
    "<b>goal script</b>. Module 2 generates two scripts from a single product description:", S_BODY))

story.append(Paragraph("Round 1 — Qualification Script", S_H3))
story.append(Paragraph(
    "Introduces the caller as a sourcing agent. Asks: does the business sell this product? "
    "Would they be open to a follow-up about quantities and pricing? Keeps the call under "
    "2 minutes. Ends politely regardless of the answer.", S_BODY))

story.append(Paragraph("Round 2 — Data Capture Script", S_H3))
story.append(Paragraph(
    "Used only with vendors who said yes in Round 1. Collects: contact name, supply "
    "capacity and quantities, rough price per unit, and earliest available timeline. "
    "Keeps the call under 5 minutes.", S_BODY))

story.append(section_box(
    "Client Approval Gate (Mandatory)",
    [Paragraph(
        "No call is ever placed without the client first seeing and approving the script. "
        "Interactively, the system shows the script and asks: Use as-is, Edit, or Quit. "
        "In automated mode (--yes), the approval timestamp is recorded in the database. "
        "The timestamp and consent basis are stored in every campaign record as a "
        "compliance audit trail.", S_BODY)],
    bg=C_LIGHT_GRN, title_color=C_GREEN))

# ── Module 3 detail ───────────────────────────────────────────────────────────
story.append(Paragraph("Module 3 — The Call Pipeline in Detail", S_H2))
story.append(Paragraph(
    "This module connects to CALL-E's API and manages the full lifecycle of each "
    "phone call — from planning through transcript extraction.", S_BODY))

story.append(flow_table([
    (1, "plan_call — Prepare the call",
     "Sends the phone number and goal script to CALL-E. The AI reads the script and "
     "prepares the voice agent. Returns a plan_id and confirm_token. No phone has rung yet.",
     HexColor("#2196F3")),
    (2, "run_call — Execute the call",
     "Sends the plan_id and confirm_token to actually dial. CALL-E's agent speaks "
     "naturally with whoever answers. Returns a run_id immediately (call is async).",
     HexColor("#4CAF50")),
    (3, "poll_until_done — Wait for completion",
     "Every 15 seconds, checks CALL-E for current status. Terminal statuses: COMPLETED, "
     "FAILED, NO ANSWER, BUSY, DECLINED, CANCELLED. Space vs underscore variants are "
     "both handled. Times out after 10 minutes maximum.",
     HexColor("#FF9800")),
    (4, "Groq AI inference — Extract intelligence",
     "Reads the call transcript. Parses it into timestamped speaker lines. Sends to "
     "Groq Llama 3.3-70B to extract: interest level, sentiment, key signals, Round 2 "
     "recommendation, and a one-sentence summary. All stored in SQLite.",
     HexColor("#9C27B0")),
    (5, "classify_round1 — Make the call/no-call decision",
     "Checks CALL-E's outcome.task_completed boolean. Falls back to transcript keyword "
     "scan if unavailable. Returns: positive | negative | no_answer | failed. "
     "Only 'positive' leads proceed to Round 2.",
     HexColor("#607D8B")),
]))

# ── Data outputs ──────────────────────────────────────────────────────────────
story.append(hr())
story.append(Paragraph("What You Get Back", S_H1))

story.append(data_table([
    ["Output",           "Where",                    "Contents"],
    ["Terminal table",   "Console",                  "Name, masked phone, category, status, AI summary per vendor"],
    ["SQLite database",  "vendor_discovery.db",      "Full raw call data, transcripts, extracted fields, consent timestamps"],
    ["Web dashboard",    "http://localhost:5000",     "Live view, auto-refreshes every 8s, colour-coded statuses"],
    ["Excel export",     "file.xlsx (optional)",     "One row per vendor: all R1+R2 fields, AI extractions, candidate IDs"],
], col_widths=[35*mm, 45*mm, 75*mm], header_bg=C_BLUE))

# ── Groq inference fields ─────────────────────────────────────────────────────
story.append(Paragraph("AI Inference — What Groq Extracts", S_H2))
story.append(Paragraph(
    "After every completed call, the transcript is sent to Groq's free API "
    "(Llama 3.3-70B, 14,400 requests/day free tier) for structured extraction.", S_BODY))

story.append(data_table([
    ["Round", "Field",              "What it means"],
    ["R1",    "interest_level",     "high / medium / low / none / unknown"],
    ["R1",    "sentiment",          "positive / neutral / negative overall tone"],
    ["R1",    "key_signals",        "Exact phrases from the vendor indicating interest or refusal"],
    ["R1",    "recommend_round2",   "true / false — whether to proceed to a follow-up call"],
    ["R1",    "summary",            "One sentence describing the call outcome"],
    ["R2",    "contact_name",       "Name of the right person to speak with"],
    ["R2",    "can_supply",         "true / false / null — whether they can provide the product"],
    ["R2",    "quantity_mentioned", "Any quantity figure the vendor mentioned"],
    ["R2",    "price_range",        "Price per unit or batch as stated by the vendor"],
    ["R2",    "timeline",           "Earliest date or lead time they quoted"],
    ["R2",    "next_steps",         "What the vendor suggested as next action"],
], col_widths=[12*mm, 42*mm, 101*mm], header_bg=C_BLUE))

# ── Safety features ───────────────────────────────────────────────────────────
story.append(hr())
story.append(Paragraph("Safety, Privacy &amp; Compliance", S_H1))

story.append(data_table([
    ["Feature",              "What it does",                                          "Why it matters"],
    ["Phone masking",        "Phones shown as +44****890 everywhere except the DB",   "Prevents accidental number exposure in logs or screenshots"],
    ["Consent gate",         "Client must approve vendor list; timestamp recorded",   "Provides audit trail proving outreach was authorised"],
    ["Business hours gate",  "GPS+timezone check blocks calls outside 09:00-18:00",   "Prevents nuisance calls; respects vendor working hours"],
    ["Dry-run mode",         "--dry-run plans calls but never dials any number",      "Safe for demos and testing without spending call credits"],
    ["Bounded retries",      "No-answer leads retried at most once; no loops",        "Controls call spend; avoids harassing uninterested vendors"],
    ["No secrets in files",  "API keys via environment variables only; never hardcoded","Prevents credentials leaking through version control"],
    ["OSM attribution",      "ODbL credit shown in all outputs and the dashboard",    "Legally required by the ODbL licence"],
], col_widths=[36*mm, 62*mm, 57*mm], header_bg=C_GREEN))

# ── How to run ────────────────────────────────────────────────────────────────
story.append(hr())
story.append(Paragraph("How to Run It", S_H2))

story.append(data_table([
    ["Command",                                                                         "What it does"],
    ["python main.py --product \"shoes\" --location \"London\" --dry-run",              "Discover vendors + generate script. NO real calls placed. Safe for testing."],
    ["python main.py --product \"hardware\" --location \"Mumbai\" --limit 5 --yes",     "Full campaign: discover 5 vendors, auto-approve, call all, run AI inference."],
    ["python main.py ... --export-excel results.xlsx",                                   "Same as above, plus export a formatted Excel file when done."],
    ["python main.py ... --skip-hours-gate",                                             "Bypass the business-hours check (for testing at weekends or off-hours)."],
    ["python dashboard.py",                                                              "Start the web dashboard at http://127.0.0.1:5000 (auto-refreshes every 8s)."],
], col_widths=[88*mm, 67*mm], header_bg=HexColor("#2d3748")))

# ── Tech stack ────────────────────────────────────────────────────────────────
story.append(Paragraph("Technology Stack", S_H2))

story.append(data_table([
    ["Component",          "Technology",                      "Role"],
    ["Vendor discovery",   "OpenStreetMap / Overpass API",    "Free global business directory with GPS data"],
    ["AI phone agent",     "CALL-E (calle.ai)",               "Plans, executes, and transcribes phone calls"],
    ["Transcript AI",      "Groq API — Llama 3.3-70B",        "Free tier: 14,400 req/day, structured extraction"],
    ["Data storage",       "SQLite",                          "Zero-config local database, no server needed"],
    ["Web dashboard",      "Flask + vanilla JavaScript",       "Lightweight, no build step, auto-refreshing UI"],
    ["Business hours",     "timezonefinder + zoneinfo",        "GPS-to-timezone lookup, Python standard library"],
    ["Excel export",       "openpyxl",                        "Formatted .xlsx with colour-coded headers"],
    ["Compliance agents",  "Claude Opus 4.8 subagents",       "5 specialised reviewers for consent, schema, security"],
], col_widths=[36*mm, 50*mm, 69*mm], header_bg=C_PURPLE))

# ── Footer ────────────────────────────────────────────────────────────────────
story.append(hr())
story.append(Paragraph(
    "Data (c) OpenStreetMap contributors, ODbL licence — openstreetmap.org/copyright  |  "
    "Built for CALL-E Hackathon, AIRUDDER Pte Ltd  |  Deadline: September 14 2026",
    S_FTR))

doc.build(story)
print(f"PDF written: {OUT}")
