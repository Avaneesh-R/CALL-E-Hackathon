"""
Web dashboard for Vendor Discovery & Outreach.
Run: python dashboard.py
Open: http://127.0.0.1:5000
Auto-refreshes every 8 seconds.
"""
import json
from flask import Flask, jsonify, render_template_string
from models import get_conn, init_db

app = Flask(__name__)

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vendor Discovery Dashboard</title>
<style>
  body { font-family: 'Segoe UI', sans-serif; background: #0f1117; color: #e0e0e0; margin: 0; padding: 20px; }
  h1 { color: #58a6ff; margin-bottom: 4px; font-size: 1.4rem; }
  .subtitle { color: #888; font-size: 0.8rem; margin-bottom: 24px; }
  .campaign { background: #161b22; border: 1px solid #30363d; border-radius: 8px; margin-bottom: 24px; padding: 16px; }
  .campaign-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .campaign-title { font-size: 1rem; font-weight: 600; color: #f0f6fc; }
  .campaign-meta { font-size: 0.75rem; color: #888; }
  .consent-badge { font-size: 0.7rem; padding: 2px 8px; border-radius: 10px; background: #1a3a1a; color: #56d364; border: 1px solid #2a5a2a; }
  table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
  th { background: #21262d; color: #8b949e; text-align: left; padding: 8px 10px; border-bottom: 1px solid #30363d; font-weight: 500; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.05em; }
  td { padding: 8px 10px; border-bottom: 1px solid #21262d; vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  .status { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 600; }
  .s-positive    { background: #1a3a1a; color: #56d364; }
  .s-negative    { background: #3a1a1a; color: #f85149; }
  .s-no_answer   { background: #2a2a1a; color: #e3b341; }
  .s-completed   { background: #1a2a3a; color: #58a6ff; }
  .s-not_called  { background: #21262d; color: #8b949e; }
  .s-failed      { background: #3a1a1a; color: #f85149; }
  .s-skipped     { background: #21262d; color: #888; }
  .s-dry_run     { background: #21262d; color: #888; }
  .notes { color: #c9d1d9; max-width: 280px; }
  .phone { font-family: monospace; color: #79c0ff; }
  .cat { color: #d2a8ff; }
  .refreshing { position: fixed; top: 12px; right: 16px; font-size: 0.72rem; color: #444; }
  .stat-bar { display: flex; gap: 16px; margin-bottom: 20px; }
  .stat { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 10px 16px; text-align: center; min-width: 80px; }
  .stat-num { font-size: 1.4rem; font-weight: 700; color: #58a6ff; }
  .stat-label { font-size: 0.68rem; color: #888; text-transform: uppercase; letter-spacing: 0.05em; }
  a { color: #58a6ff; text-decoration: none; }
</style>
</head>
<body>
<h1>Vendor Discovery &amp; Outreach</h1>
<div class="subtitle">Data (c) OpenStreetMap contributors (ODbL) &mdash; <a href="https://openstreetmap.org/copyright" target="_blank">openstreetmap.org/copyright</a></div>
<div class="refreshing" id="refresh-label">auto-refresh in <span id="countdown">8</span>s</div>

<div id="stats" class="stat-bar"></div>
<div id="campaigns"></div>

<script>
const STATUS_CLASS = {
  positive: 's-positive', negative: 's-negative', no_answer: 's-no_answer',
  completed: 's-completed', not_called: 's-not_called', failed: 's-failed',
  skipped: 's-skipped', dry_run: 's-dry_run'
};
function statusBadge(s) {
  const cls = STATUS_CLASS[s] || 's-not_called';
  return `<span class="status ${cls}">${s || 'unknown'}</span>`;
}
function truncate(s, n) { return s && s.length > n ? s.slice(0, n) + '...' : (s || ''); }

async function load() {
  const data = await fetch('/api/campaigns').then(r => r.json());

  // Stats
  let totalLeads = 0, totalPositive = 0, totalCompleted = 0;
  data.forEach(c => { c.leads.forEach(l => {
    totalLeads++;
    if (l.status === 'positive') totalPositive++;
    if (l.status === 'completed') totalCompleted++;
  }); });
  document.getElementById('stats').innerHTML = `
    <div class="stat"><div class="stat-num">${data.length}</div><div class="stat-label">Campaigns</div></div>
    <div class="stat"><div class="stat-num">${totalLeads}</div><div class="stat-label">Leads</div></div>
    <div class="stat"><div class="stat-num">${totalPositive}</div><div class="stat-label">R1 Positive</div></div>
    <div class="stat"><div class="stat-num">${totalCompleted}</div><div class="stat-label">R2 Done</div></div>
  `;

  // Campaigns
  document.getElementById('campaigns').innerHTML = data.map(c => `
    <div class="campaign">
      <div class="campaign-header">
        <div>
          <span class="campaign-title">#${c.id} &mdash; ${c.product_description}</span>
          &nbsp;<span class="campaign-meta">@ ${c.location}</span>
        </div>
        <div style="display:flex;gap:8px;align-items:center;">
          ${c.consent_approved_at ? `<span class="consent-badge">Consent approved ${c.consent_approved_at.slice(0,16)}</span>` : '<span class="consent-badge" style="background:#3a1a1a;color:#f85149;border-color:#5a2a2a;">No consent gate</span>'}
          <span class="campaign-meta">${c.created_at ? c.created_at.slice(0,16) : ''}</span>
        </div>
      </div>
      <table>
        <thead><tr>
          <th>Name</th><th>Phone</th><th>Category</th>
          <th>R1 Status</th><th>R2 Status</th><th>AI Summary</th>
        </tr></thead>
        <tbody>
          ${c.leads.map(l => `<tr>
            <td>${truncate(l.name, 30)}</td>
            <td class="phone">${l.masked_phone || ''}</td>
            <td class="cat">${truncate(l.category, 20)}</td>
            <td>${statusBadge(l.r1_status)}</td>
            <td>${statusBadge(l.r2_status)}</td>
            <td class="notes">${truncate(l.summary, 80)}</td>
          </tr>`).join('')}
        </tbody>
      </table>
    </div>
  `).join('');
}

// Countdown + auto-refresh
let t = 8;
setInterval(() => {
  t--;
  document.getElementById('countdown').textContent = t;
  if (t <= 0) { t = 8; load(); }
}, 1000);

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
            "SELECT id, product_description, location, consent_basis, consent_approved_at, created_at FROM campaigns ORDER BY id DESC"
        ).fetchall()

        result = []
        for c in campaigns:
            leads_raw = conn.execute(
                """SELECT l.id, l.name, l.masked_phone, l.phone, l.category, l.status,
                          l.round1_call_id, l.round2_call_id, l.skip_reason,
                          r1log.extracted_fields AS r1_fields,
                          r2log.extracted_fields AS r2_fields
                   FROM leads l
                   LEFT JOIN call_logs r1log ON r1log.lead_id = l.id AND r1log.round = 1
                   LEFT JOIN call_logs r2log ON r2log.lead_id = l.id AND r2log.round = 2
                   WHERE l.campaign_id = ?
                   ORDER BY l.id""",
                (c["id"],)
            ).fetchall()

            leads = []
            for l in leads_raw:
                r1_ef = json.loads(l["r1_fields"]) if l["r1_fields"] else {}
                r2_ef = json.loads(l["r2_fields"]) if l["r2_fields"] else {}
                summary = (r2_ef.get("summary") or r1_ef.get("summary")
                           or r2_ef.get("transcript_summary", "")[:80]
                           or r1_ef.get("transcript_summary", "")[:80])
                from models import _mask_phone
                leads.append({
                    "id": l["id"],
                    "name": l["name"],
                    "masked_phone": l["masked_phone"] or _mask_phone(l["phone"]),
                    "category": l["category"],
                    "status": l["status"],
                    "r1_status": l["status"] if not l["round2_call_id"] else (
                        "positive" if l["status"] in ("completed", "positive") else l["status"]
                    ),
                    "r2_status": l["status"] if l["round2_call_id"] else None,
                    "summary": summary,
                    "skip_reason": l["skip_reason"],
                })

            result.append({
                "id": c["id"],
                "product_description": c["product_description"],
                "location": c["location"],
                "consent_basis": c["consent_basis"],
                "consent_approved_at": c["consent_approved_at"],
                "created_at": c["created_at"],
                "leads": leads,
            })

    return jsonify(result)


if __name__ == "__main__":
    init_db()
    print("Dashboard running at http://127.0.0.1:5000")
    app.run(debug=False, port=5000)
