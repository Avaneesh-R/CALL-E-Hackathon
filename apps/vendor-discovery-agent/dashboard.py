"""
Web dashboard for Vendor Discovery & Outreach.
Run: python dashboard.py
Open: http://127.0.0.1:5000
"""
import json
from flask import Flask, jsonify, render_template_string
from models import get_conn, init_db, _mask_phone
from scheduler import start_scheduler_thread

app = Flask(__name__)

_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vendor Discovery Dashboard</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',sans-serif;background:#0f1117;color:#e0e0e0;padding:20px}
h1{color:#58a6ff;font-size:1.35rem;margin-bottom:2px}
.sub{color:#666;font-size:.75rem;margin-bottom:20px}
.sub a{color:#58a6ff;text-decoration:none}
.refresh-tag{position:fixed;top:12px;right:16px;font-size:.7rem;color:#444}

/* Stats bar */
.stats{display:flex;gap:12px;margin-bottom:18px;flex-wrap:wrap}
.stat{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px 18px;text-align:center;min-width:80px}
.stat-n{font-size:1.5rem;font-weight:700;color:#58a6ff}
.stat-l{font-size:.65rem;color:#666;text-transform:uppercase;letter-spacing:.05em}

/* Scheduled calls banner */
.sched-banner{background:#162016;border:1px solid #2a5a2a;border-radius:6px;padding:10px 14px;margin-bottom:16px;font-size:.82rem}
.sched-banner h3{color:#56d364;font-size:.85rem;margin-bottom:6px}
.sched-item{display:flex;gap:10px;padding:4px 0;border-bottom:1px solid #1e3a1e;align-items:center}
.sched-item:last-child{border-bottom:none}
.sched-time{color:#e3b341;min-width:160px;font-size:.78rem}
.sched-status{font-size:.7rem;padding:1px 7px;border-radius:8px}
.ss-pending{background:#1a3a1a;color:#56d364}
.ss-fired{background:#1a2a3a;color:#58a6ff}
.ss-failed{background:#3a1a1a;color:#f85149}
.ss-skipped{background:#21262d;color:#888}

/* Campaign card */
.campaign{background:#161b22;border:1px solid #30363d;border-radius:8px;margin-bottom:20px}
.camp-hdr{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;border-bottom:1px solid #21262d;flex-wrap:wrap;gap:6px}
.camp-title{font-size:.95rem;font-weight:600;color:#f0f6fc}
.camp-meta{font-size:.72rem;color:#666}
.consent-ok{font-size:.68rem;padding:2px 8px;border-radius:10px;background:#1a3a1a;color:#56d364;border:1px solid #2a5a2a}
.consent-no{font-size:.68rem;padding:2px 8px;border-radius:10px;background:#3a1a1a;color:#f85149;border:1px solid #5a2a2a}

/* Table */
table{width:100%;border-collapse:collapse;font-size:.8rem}
thead th{background:#21262d;color:#8b949e;text-align:left;padding:7px 10px;font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;border-bottom:1px solid #30363d}
tbody tr.lead-row{cursor:pointer;transition:background .15s}
tbody tr.lead-row:hover{background:#1c2128}
tbody tr.lead-row td{padding:8px 10px;border-bottom:1px solid #21262d;vertical-align:middle}
tbody tr.lead-row:last-of-type td{border-bottom:none}

/* Expand panel */
tr.expand-row{display:none}
tr.expand-row.open{display:table-row}
tr.expand-row td{padding:0}
.expand-inner{background:#0d1117;border-top:1px solid #30363d;padding:14px 16px;display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:700px){.expand-inner{grid-template-columns:1fr}}
.exp-section{background:#161b22;border:1px solid #21262d;border-radius:6px;padding:12px}
.exp-section h4{font-size:.75rem;text-transform:uppercase;letter-spacing:.07em;color:#8b949e;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #21262d}
.exp-section.full{grid-column:1/-1}

/* Transcript */
.transcript-line{display:flex;gap:8px;padding:3px 0;font-size:.78rem;border-bottom:1px solid #1a1f26}
.transcript-line:last-child{border-bottom:none}
.t-time{color:#555;min-width:55px;font-family:monospace}
.t-bot{color:#58a6ff;min-width:45px;font-weight:600}
.t-user{color:#56d364;min-width:45px;font-weight:600}
.t-text{color:#c9d1d9;flex:1}

/* Inference grid */
.inf-row{display:flex;padding:3px 0;border-bottom:1px solid #1a1f26;font-size:.78rem}
.inf-row:last-child{border-bottom:none}
.inf-key{color:#8b949e;min-width:130px;flex-shrink:0}
.inf-val{color:#c9d1d9;flex:1;word-break:break-word}

/* Raw JSON modal */
.modal-backdrop{display:none;position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:1000;align-items:center;justify-content:center}
.modal-backdrop.open{display:flex}
.modal-box{background:#161b22;border:1px solid #30363d;border-radius:10px;width:min(90vw,780px);max-height:80vh;display:flex;flex-direction:column;overflow:hidden}
.modal-head{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;border-bottom:1px solid #30363d}
.modal-head h3{font-size:.85rem;color:#f0f6fc}
.modal-close{background:none;border:none;color:#666;font-size:1.2rem;cursor:pointer;padding:0 4px;line-height:1}
.modal-close:hover{color:#f85149}
.modal-body{overflow:auto;padding:14px 16px;flex:1}
pre.json-view{font-family:monospace;font-size:.76rem;color:#c9d1d9;white-space:pre-wrap;word-break:break-all;margin:0}
.raw-btn{font-size:.62rem;background:#21262d;border:1px solid #30363d;color:#8b949e;border-radius:4px;padding:1px 7px;cursor:pointer;margin-left:6px;vertical-align:middle}
.raw-btn:hover{color:#58a6ff;border-color:#58a6ff}

/* Address */
.address-tag{font-size:.72rem;color:#8b949e;font-style:italic;padding:2px 0}

/* Scheduled tag on lead row */
.sched-tag{font-size:.68rem;background:#162016;color:#56d364;border:1px solid #2a4a2a;border-radius:8px;padding:1px 7px;white-space:nowrap}

/* Status badges */
.status{display:inline-block;padding:2px 8px;border-radius:10px;font-size:.68rem;font-weight:600}
.s-positive{background:#1a3a1a;color:#56d364}
.s-negative{background:#3a1a1a;color:#f85149}
.s-no_answer{background:#2a2a1a;color:#e3b341}
.s-completed{background:#1a2a3a;color:#58a6ff}
.s-not_called{background:#21262d;color:#8b949e}
.s-failed{background:#3a1a1a;color:#f85149}
.s-skipped{background:#21262d;color:#666}
.s-positive_r2{background:#1a2a3a;color:#58a6ff}

/* Chevron */
.chev{color:#444;font-size:.9rem;transition:transform .2s;display:inline-block;margin-right:4px}
.chev.open{transform:rotate(90deg)}

/* Copy button */
.copy-btn{font-size:.65rem;background:#21262d;border:1px solid #30363d;color:#8b949e;border-radius:4px;padding:1px 5px;cursor:pointer}
.copy-btn:hover{color:#58a6ff}
</style>
</head>
<body>
<h1>Vendor Discovery &amp; Outreach</h1>
<div class="sub">Data &copy; <a href="https://openstreetmap.org/copyright" target="_blank">OpenStreetMap contributors (ODbL)</a></div>
<div class="refresh-tag">Refresh in <span id="cd">8</span>s</div>

<!-- Raw JSON modal -->
<div class="modal-backdrop" id="raw-modal" onclick="if(event.target===this)closeModal()">
  <div class="modal-box">
    <div class="modal-head">
      <h3 id="raw-modal-title">Full Inference JSON</h3>
      <button class="modal-close" onclick="closeModal()">&#x2715;</button>
    </div>
    <div class="modal-body"><pre class="json-view" id="raw-modal-body"></pre></div>
  </div>
</div>

<div id="stats" class="stats"></div>
<div id="sched" style="display:none" class="sched-banner">
  <h3>&#128197; Scheduled Follow-up Calls</h3>
  <div id="sched-list"></div>
</div>
<div id="campaigns"></div>

<script>
const SC = {
  positive:'s-positive', negative:'s-negative', no_answer:'s-no_answer',
  completed:'s-completed', not_called:'s-not_called', failed:'s-failed',
  skipped:'s-skipped', positive_r2:'s-positive_r2'
};
function badge(s){ return `<span class="status ${SC[s]||'s-not_called'}">${s||'?'}</span>`; }
function trunc(s,n){ return s&&s.length>n?s.slice(0,n)+'...':s||''; }
function escHtml(s){ return s?String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'):''; }

function renderTranscript(lines){
  if(!lines||!lines.length) return '<span style="color:#555;font-size:.75rem">No transcript available</span>';
  return lines.map(l=>{
    const isBOT = l.speaker&&l.speaker.toUpperCase()==='BOT';
    return `<div class="transcript-line">
      <span class="t-time">${escHtml(l.time)}</span>
      <span class="${isBOT?'t-bot':'t-user'}">${escHtml(l.speaker)}</span>
      <span class="t-text">${escHtml(l.text)}</span>
    </div>`;
  }).join('');
}

// Store raw inference objects for modal display (avoids inline JSON injection)
const _rawStore = {};
let _storeIdx = 0;

function openModalByKey(key){
  const entry = _rawStore[key];
  if(!entry) return;
  document.getElementById('raw-modal-title').textContent = entry.title;
  document.getElementById('raw-modal-body').textContent = JSON.stringify(entry.data, null, 2);
  document.getElementById('raw-modal').classList.add('open');
}
function closeModal(){
  document.getElementById('raw-modal').classList.remove('open');
}
document.addEventListener('keydown', e=>{ if(e.key==='Escape') closeModal(); });

function renderInference(inf, label){
  if(!inf||Object.keys(inf).length===0)
    return `<span style="color:#555;font-size:.75rem">No ${label} inference</span>`;

  // Register in store so the View Raw button can access full data safely
  const key = 'inf_' + (_storeIdx++);
  _rawStore[key] = {title: label + ' — Full JSON', data: inf};

  // Show all fields except transcript blob (rendered separately); show raw_inference & error
  const SKIP = new Set(['transcript']);
  const rows = Object.entries(inf)
    .filter(([k])=>!SKIP.has(k))
    .map(([k,v])=>{
      const val = Array.isArray(v)?v.join(', '):String(v??'—');
      // Long values: show first 120 chars + "more" inline expand
      if(val.length > 120){
        return `<div class="inf-row">
          <span class="inf-key">${escHtml(k.replace(/_/g,' '))}</span>
          <span class="inf-val">
            <span class="val-short">${escHtml(val.slice(0,120))}&hellip;
              <button class="raw-btn" onclick="event.stopPropagation();this.parentNode.querySelector('.val-full').style.display='inline';this.style.display='none'">more</button>
            </span>
            <span class="val-full" style="display:none">${escHtml(val)}</span>
          </span>
        </div>`;
      }
      return `<div class="inf-row">
        <span class="inf-key">${escHtml(k.replace(/_/g,' '))}</span>
        <span class="inf-val">${escHtml(val)}</span>
      </div>`;
    }).join('');

  const rawBtn = `<button class="raw-btn" onclick="event.stopPropagation();openModalByKey('${key}')">&#123;&#125; View Raw</button>`;
  return `<div style="display:flex;justify-content:flex-end;margin-bottom:6px">${rawBtn}</div>${rows}`;
}

function toggleExpand(leadId){
  const row = document.getElementById('exp-'+leadId);
  const chev = document.getElementById('chev-'+leadId);
  if(!row) return;
  const isOpen = row.classList.contains('open');
  row.classList.toggle('open', !isOpen);
  chev.classList.toggle('open', !isOpen);
}

async function load(){
  const [data, sched] = await Promise.all([
    fetch('/api/campaigns').then(r=>r.json()),
    fetch('/api/scheduled').then(r=>r.json()),
  ]);

  // Stats
  let totLeads=0, totPos=0, totDone=0, totSched=0;
  data.forEach(c=>c.leads.forEach(l=>{
    totLeads++;
    if(l.status==='positive') totPos++;
    if(l.status==='completed') totDone++;
  }));
  totSched = sched.filter(s=>s.status==='pending').length;
  document.getElementById('stats').innerHTML = `
    <div class="stat"><div class="stat-n">${data.length}</div><div class="stat-l">Campaigns</div></div>
    <div class="stat"><div class="stat-n">${totLeads}</div><div class="stat-l">Leads</div></div>
    <div class="stat"><div class="stat-n">${totPos}</div><div class="stat-l">R1 Positive</div></div>
    <div class="stat"><div class="stat-n">${totDone}</div><div class="stat-l">R2 Done</div></div>
    <div class="stat"><div class="stat-n">${totSched}</div><div class="stat-l">Scheduled</div></div>
  `;

  // Scheduled banner
  const schedBox = document.getElementById('sched');
  const schedList = document.getElementById('sched-list');
  if(sched.length>0){
    schedBox.style.display='block';
    schedList.innerHTML = sched.map(s=>`
      <div class="sched-item">
        <span class="sched-time">&#128337; ${escHtml(s.local_time)}</span>
        <span style="color:#c9d1d9;flex:1;font-size:.78rem">${escHtml(s.lead_name||s.masked_phone)} &mdash; ${escHtml(s.product)}</span>
        <span class="sched-status ss-${escHtml(s.status)}">${escHtml(s.status)}</span>
      </div>`).join('');
  } else {
    schedBox.style.display='none';
  }

  // Campaigns
  document.getElementById('campaigns').innerHTML = data.map(c=>`
    <div class="campaign">
      <div class="camp-hdr">
        <div>
          <span class="camp-title">#${c.id} &mdash; ${escHtml(c.product_description)}</span>
          &nbsp;<span class="camp-meta">@ ${escHtml(c.location)}</span>
        </div>
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
          ${c.consent_approved_at
            ? `<span class="consent-ok">&#10003; Consent ${escHtml(c.consent_approved_at.slice(0,16))} UTC</span>`
            : '<span class="consent-no">&#10007; No consent gate</span>'}
          <span class="camp-meta">${escHtml(c.created_at||'')}</span>
        </div>
      </div>
      <table>
        <thead><tr>
          <th style="width:28px"></th>
          <th>Name</th><th>Phone</th><th>Category</th>
          <th>R1</th><th>R2</th><th>Quick Summary</th>
        </tr></thead>
        <tbody>
          ${c.leads.map(l=>`
            <tr class="lead-row" onclick="toggleExpand(${l.id})">
              <td><span class="chev" id="chev-${l.id}">&#9658;</span></td>
              <td>
                <div>${escHtml(trunc(l.name,28))}</div>
                ${l.address?`<div class="address-tag">&#128205; ${escHtml(trunc(l.address,40))}</div>`:''}
              </td>
              <td style="font-family:monospace;color:#79c0ff">${escHtml(l.masked_phone)}</td>
              <td style="color:#d2a8ff">${escHtml(trunc(l.category,18))}</td>
              <td>${badge(l.r1_status)}</td>
              <td>${l.r2_status?badge(l.r2_status):'<span style="color:#444">—</span>'}
                  ${l.scheduled_at?`<br><span class="sched-tag">&#128197; ${escHtml(l.scheduled_local)}</span>`:''}
              </td>
              <td style="color:#8b949e;font-size:.75rem">${escHtml(trunc(l.summary,60))}</td>
            </tr>
            <tr class="expand-row" id="exp-${l.id}">
              <td colspan="7">
                <div class="expand-inner">

                  <div class="exp-section">
                    <h4>&#128222; Lead Details</h4>
                    ${renderInference({
                      'Name': l.name,
                      'Phone (masked)': l.masked_phone,
                      'Category': l.category,
                      'Address': l.address||'Not available in OSM',
                      'Candidate ID': l.candidate_id||'—',
                      'Status': l.status,
                      'Skip reason': l.skip_reason||'—',
                    }, 'lead')}
                    ${l.scheduled_at?`
                    <div style="margin-top:8px;padding:6px;background:#162016;border-radius:4px;font-size:.75rem">
                      <span style="color:#56d364">&#128197; Scheduled R2 call:</span>
                      <span style="color:#e3b341"> ${escHtml(l.scheduled_local)}</span>
                      <span style="color:#56d364"> (${escHtml(l.scheduled_tz)})</span>
                    </div>`:''}
                  </div>

                  <div class="exp-section">
                    <h4>&#129302; R1 Inference (Qualification)</h4>
                    ${renderInference(l.r1_inference,'R1')}
                  </div>

                  <div class="exp-section">
                    <h4>&#128203; R2 Inference (Data Capture)</h4>
                    ${renderInference(l.r2_inference,'R2')}
                  </div>

                  <div class="exp-section">
                    <h4>&#128172; Full Transcript</h4>
                    ${renderTranscript(l.transcript)}
                  </div>

                </div>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `).join('');
}

// Countdown + auto-refresh
let t=8;
setInterval(()=>{ t--; document.getElementById('cd').textContent=t; if(t<=0){t=8;load();} },1000);
load();
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(_HTML)


@app.route("/api/campaigns")
def api_campaigns():
    init_db()
    with get_conn() as conn:
        campaigns = conn.execute(
            "SELECT id,product_description,location,consent_basis,consent_approved_at,created_at "
            "FROM campaigns ORDER BY id DESC"
        ).fetchall()

        # Scheduled calls lookup: lead_id -> row
        sched_rows = conn.execute(
            "SELECT * FROM scheduled_calls WHERE status IN ('pending','in_progress') ORDER BY lead_id, scheduled_at"
        ).fetchall()
        sched_by_lead = {}
        for s in sched_rows:
            # Keep earliest pending call per lead (query ordered by lead_id, scheduled_at)
            if s["lead_id"] not in sched_by_lead:
                sched_by_lead[s["lead_id"]] = s

        result = []
        for c in campaigns:
            leads_raw = conn.execute(
                """SELECT l.id, l.name, l.masked_phone, l.phone, l.category, l.status,
                          l.address, l.candidate_id, l.skip_reason,
                          l.round1_call_id, l.round2_call_id, l.lat, l.lon,
                          r1log.extracted_fields AS r1_fields,
                          r2log.extracted_fields AS r2_fields
                   FROM leads l
                   LEFT JOIN call_logs r1log ON r1log.lead_id=l.id AND r1log.round=1
                   LEFT JOIN call_logs r2log ON r2log.lead_id=l.id AND r2log.round=2
                   WHERE l.campaign_id=? ORDER BY l.id""",
                (c["id"],)
            ).fetchall()

            leads = []
            for l in leads_raw:
                r1_ef = json.loads(l["r1_fields"]) if l["r1_fields"] else {}
                r2_ef = json.loads(l["r2_fields"]) if l["r2_fields"] else {}

                # Separate transcript from inference
                transcript = r1_ef.pop("transcript", [])
                summary = (r2_ef.get("summary") or r1_ef.get("summary")
                           or r2_ef.get("transcript_summary","")
                           or r1_ef.get("transcript_summary",""))

                # Determine R1 / R2 display status
                has_r2 = bool(l["round2_call_id"])
                r1_status = l["status"]
                r2_status = l["status"] if has_r2 else None

                # Scheduled call info
                sc = sched_by_lead.get(l["id"])
                sched_local = None
                sched_tz    = None
                if sc:
                    try:
                        from datetime import datetime, timezone
                        from zoneinfo import ZoneInfo
                        tz = ZoneInfo(sc["timezone"] or "UTC")
                        dt = datetime.fromisoformat(sc["scheduled_at"])
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        sched_local = dt.astimezone(tz).strftime("%b %d %H:%M")
                        sched_tz    = sc["timezone"]
                    except Exception:
                        sched_local = sc["scheduled_at"][:16]

                leads.append({
                    "id":             l["id"],
                    "name":           l["name"],
                    "masked_phone":   l["masked_phone"] or _mask_phone(l["phone"]),
                    "category":       l["category"],
                    "address":        l["address"],
                    "candidate_id":   l["candidate_id"],
                    "skip_reason":    l["skip_reason"],
                    "status":         l["status"],
                    "r1_status":      r1_status,
                    "r2_status":      r2_status,
                    "summary":        summary,
                    "transcript":     transcript,
                    "r1_inference":   r1_ef,
                    "r2_inference":   r2_ef,
                    "scheduled_at":   sc["scheduled_at"] if sc else None,
                    "scheduled_local":sched_local,
                    "scheduled_tz":   sched_tz,
                })

            result.append({
                "id":                  c["id"],
                "product_description": c["product_description"],
                "location":            c["location"],
                "consent_basis":       c["consent_basis"],
                "consent_approved_at": c["consent_approved_at"],
                "created_at":          c["created_at"],
                "leads":               leads,
            })

    return jsonify(result)


@app.route("/api/scheduled")
def api_scheduled():
    init_db()
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT sc.*, l.name AS lead_name, l.masked_phone, l.phone,
                      c.product_description AS product
               FROM scheduled_calls sc
               JOIN leads l ON l.id=sc.lead_id
               JOIN campaigns c ON c.id=sc.campaign_id
               ORDER BY sc.scheduled_at"""
        ).fetchall()
        result = []
        for r in rows:
            local_time = r["scheduled_at"]
            try:
                from datetime import datetime, timezone
                from zoneinfo import ZoneInfo
                tz = ZoneInfo(r["timezone"] or "UTC")
                dt = datetime.fromisoformat(r["scheduled_at"])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                local_time = dt.astimezone(tz).strftime("%Y-%m-%d %H:%M %Z")
            except Exception:
                pass
            result.append({
                "id":         r["id"],
                "lead_name":  r["lead_name"],
                "masked_phone": r["masked_phone"] or _mask_phone(r["phone"]),
                "product":    r["product"],
                "status":     r["status"],
                "local_time": local_time,
                "timezone":   r["timezone"],
            })
    return jsonify(result)


if __name__ == "__main__":
    init_db()
    start_scheduler_thread()
    print("Dashboard: http://127.0.0.1:5000")
    app.run(debug=False, port=5000)
