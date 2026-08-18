"""
Web dashboard for Vendor Discovery & Outreach.
Run: python dashboard.py
Open: http://127.0.0.1:5000
"""
import json
from flask import Flask, jsonify, render_template_string, Response, stream_with_context, request
import queue as _queue
from models import get_conn, init_db, _mask_phone
from scheduler import start_scheduler_thread

app = Flask(__name__)

_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vendor Discovery Dashboard</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
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

/* Tabs */
.tabs{display:flex;gap:4px;border-bottom:1px solid #30363d;margin-bottom:18px}
.tab-btn{background:none;border:none;border-bottom:2px solid transparent;color:#8b949e;font-size:.85rem;font-weight:600;padding:8px 16px;cursor:pointer;font-family:inherit}
.tab-btn:hover{color:#c9d1d9}
.tab-btn.active{color:#58a6ff;border-bottom-color:#58a6ff}
.view{display:none}
.view.active{display:block}

/* Analytics charts */
.chart-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:20px}
@media(max-width:900px){.chart-grid{grid-template-columns:1fr}}
.chart-card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:14px}
.chart-card h3{font-size:.8rem;color:#8b949e;text-transform:uppercase;letter-spacing:.05em;margin-bottom:10px}
.bench-card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:14px}
.bench-card h3{font-size:.85rem;color:#f0f6fc;margin-bottom:10px}
#map-view .campaign{margin-bottom:0}

/* Live console tab */
.live-console{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:12px;font-family:monospace;font-size:.78rem;min-height:120px;max-height:400px;overflow-y:auto}
.live-line{padding:2px 0;border-bottom:1px solid #1a1f26;display:flex;gap:8px}
.live-line:last-child{border-bottom:none}
.live-ts{color:#555;min-width:55px}
.live-status{color:#e3b341;font-weight:600;min-width:80px}
.live-text{color:#c9d1d9;flex:1}
.live-empty{color:#555;font-style:italic;font-size:.75rem;padding:8px 0}
.live-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#56d364;animation:pulse 1.2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}

/* Reliability badge */
.rel-badge{font-size:.62rem;padding:1px 6px;border-radius:8px;font-weight:600;margin-left:4px}
.rel-green{background:#1a3a1a;color:#56d364;border:1px solid #2a5a2a}
.rel-amber{background:#2a2a1a;color:#e3b341;border:1px solid #4a4a2a}
.rel-red{background:#3a1a1a;color:#f85149;border:1px solid #5a2a2a}
.rel-grey{background:#21262d;color:#666}

/* Template selector */
.tpl-bar{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px 14px;margin-bottom:14px;display:flex;gap:10px;align-items:center;flex-wrap:wrap;font-size:.8rem}
.tpl-bar label{color:#8b949e;font-size:.75rem}
.tpl-select{background:#0d1117;border:1px solid #30363d;color:#c9d1d9;border-radius:4px;padding:3px 8px;font-size:.78rem}
.tpl-save-btn{font-size:.72rem;background:#21262d;border:1px solid #30363d;color:#8b949e;border-radius:4px;padding:3px 10px;cursor:pointer}
.tpl-save-btn:hover{color:#58a6ff;border-color:#58a6ff}
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

<div class="tabs">
  <button class="tab-btn active" id="tab-leads" onclick="switchTab('leads')">Leads</button>
  <button class="tab-btn" id="tab-analytics" onclick="switchTab('analytics')">Analytics</button>
  <button class="tab-btn" id="tab-map" onclick="switchTab('map')">Map</button>
  <button class="tab-btn" id="tab-live" onclick="switchTab('live')">&#9654; Live</button>
</div>

<div id="stats" class="stats"></div>

<div id="leads-view" class="view active">
  <div class="tpl-bar" id="tpl-bar">
    <label>Templates:</label>
    <select class="tpl-select" id="tpl-select" onchange="applyTemplate()">
      <option value="">-- select a template --</option>
    </select>
    <span id="tpl-info" style="color:#8b949e;font-size:.72rem;flex:1"></span>
    <button class="tpl-save-btn" onclick="promptSaveTemplate()">&#128190; Save current as template</button>
  </div>
  <div id="sched" style="display:none" class="sched-banner">
    <h3>&#128197; Scheduled Follow-up Calls</h3>
    <div id="sched-list"></div>
  </div>
  <div id="campaigns"></div>
</div>

<div id="analytics-view" class="view">
  <div class="chart-grid">
    <div class="chart-card"><h3>Outcomes</h3><div style="position:relative;height:280px"><canvas id="chart-outcomes"></canvas></div></div>
    <div class="chart-card"><h3>Interest Level</h3><div style="position:relative;height:280px"><canvas id="chart-interest"></canvas></div></div>
    <div class="chart-card"><h3>Sentiment Trend</h3><div style="position:relative;height:280px"><canvas id="chart-sentiment"></canvas></div></div>
  </div>
  <div class="bench-card">
    <h3>Price Intelligence</h3>
    <div id="bench-body"></div>
  </div>
</div>

<div id="map-view" class="view" style="height:500px"></div>

<div id="live-view" class="view">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
    <span id="live-indicator" style="display:none"><span class="live-dot"></span></span>
    <span style="color:#8b949e;font-size:.8rem">Real-time call console &mdash; updates as calls happen</span>
  </div>
  <div id="live-console" class="live-console">
    <div class="live-empty">No active calls. Start a campaign to see live updates here.</div>
  </div>
</div>

<script>
const SC = {
  positive:'s-positive', negative:'s-negative', no_answer:'s-no_answer',
  completed:'s-completed', not_called:'s-not_called', failed:'s-failed',
  skipped:'s-skipped', positive_r2:'s-positive_r2'
};

let _lastData = [];
let _activeTab = 'leads';
const _charts = {};
let _map = null;
let _mapMarkers = [];

function switchTab(name){
  _activeTab = name;
  ['leads','analytics','map','live'].forEach(t=>{
    document.getElementById('tab-'+t).classList.toggle('active', t===name);
    document.getElementById(t+'-view').classList.toggle('active', t===name);
  });
  if(name==='analytics') renderAnalytics(_lastData);
  if(name==='map') renderMap(_lastData);
}

const CHART_TXT = '#c9d1d9', CHART_GRID = '#30363d';

function renderAnalytics(data){
  // Outcomes donut
  const outColors = {positive:'#56d364',negative:'#f85149',no_answer:'#e3b341',completed:'#58a6ff',failed:'#f85149',skipped:'#666'};
  const outKeys = ['positive','negative','no_answer','completed','failed','skipped'];
  const outCounts = Object.fromEntries(outKeys.map(k=>[k,0]));
  data.forEach(c=>c.leads.forEach(l=>{ if(l.status in outCounts) outCounts[l.status]++; }));

  // Interest bar
  const intKeys = ['high','medium','low','none','unknown'];
  const intColors = {high:'#56d364',medium:'#e3b341',low:'#f85149',none:'#666',unknown:'#8b949e'};
  const intCounts = Object.fromEntries(intKeys.map(k=>[k,0]));
  data.forEach(c=>c.leads.forEach(l=>{
    const v = (l.r1_inference && l.r1_inference.interest_level) ? String(l.r1_inference.interest_level).toLowerCase() : 'unknown';
    intCounts[v in intCounts ? v : 'unknown']++;
  }));

  // Sentiment trend: one point per campaign
  const labels = [], pos = [], neu = [], neg = [];
  data.forEach(c=>{
    let p=0,n=0,g=0;
    c.leads.forEach(l=>{
      const s = (l.r1_inference && l.r1_inference.sentiment) ? String(l.r1_inference.sentiment).toLowerCase() : '';
      if(s==='positive') p++; else if(s==='neutral') n++; else if(s==='negative') g++;
    });
    labels.push(trunc(c.product_description||('#'+c.id), 12));
    pos.push(p); neu.push(n); neg.push(g);
  });

  const noGrid = {grid:{color:CHART_GRID,display:false},ticks:{color:CHART_TXT}};
  const legendTop = {position:'top',labels:{color:CHART_TXT}};

  _charts['outcomes']?.destroy();
  _charts['outcomes'] = new Chart(document.getElementById('chart-outcomes'),{
    type:'doughnut',
    data:{labels:outKeys,datasets:[{data:outKeys.map(k=>outCounts[k]),backgroundColor:outKeys.map(k=>outColors[k]),borderColor:'#161b22'}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:legendTop}}
  });

  _charts['interest']?.destroy();
  _charts['interest'] = new Chart(document.getElementById('chart-interest'),{
    type:'bar',
    data:{labels:intKeys,datasets:[{data:intKeys.map(k=>intCounts[k]),backgroundColor:intKeys.map(k=>intColors[k])}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:noGrid,y:{...noGrid,beginAtZero:true}}}
  });

  _charts['sentiment']?.destroy();
  _charts['sentiment'] = new Chart(document.getElementById('chart-sentiment'),{
    type:'line',
    data:{labels:labels,datasets:[
      {label:'positive',data:pos,borderColor:'#56d364',backgroundColor:'#56d364',tension:.2},
      {label:'neutral',data:neu,borderColor:'#e3b341',backgroundColor:'#e3b341',tension:.2},
      {label:'negative',data:neg,borderColor:'#f85149',backgroundColor:'#f85149',tension:.2},
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:legendTop},scales:{x:noGrid,y:{...noGrid,beginAtZero:true}}}
  });

  renderBenchmark(data);
}

function renderBenchmark(data){
  const order = {high:0,medium:1,low:2,none:3,unknown:4};
  const rows = [];
  data.forEach(c=>c.leads.forEach(l=>{
    const pr = l.r2_inference && l.r2_inference.price_range;
    if(pr!==null && pr!==undefined && String(pr).trim()!==''){
      rows.push({
        name: l.masked_phone || l.name || '?',
        price: String(pr),
        interest: (l.r1_inference && l.r1_inference.interest_level) ? String(l.r1_inference.interest_level).toLowerCase() : 'unknown',
      });
    }
  }));
  const box = document.getElementById('bench-body');
  if(!rows.length){ box.innerHTML = '<span style="color:#555;font-size:.8rem">No R2 price data yet</span>'; return; }
  rows.sort((a,b)=>(order[a.interest]??9)-(order[b.interest]??9));
  box.innerHTML = `<table><thead><tr><th>Name</th><th>Price Range</th><th>Interest Level</th></tr></thead>
    <tbody>${rows.map(r=>`<tr class="lead-row">
      <td style="font-family:monospace;color:#79c0ff">${escHtml(r.name)}</td>
      <td style="color:#c9d1d9">${escHtml(r.price)}</td>
      <td>${escHtml(r.interest)}</td></tr>`).join('')}</tbody></table>`;
}

function renderMap(data){
  const pts = [];
  data.forEach(c=>c.leads.forEach(l=>{
    if(l.lat!==null && l.lat!==undefined && l.lon!==null && l.lon!==undefined) pts.push(l);
  }));
  if(!_map){
    const clat = pts.length ? pts.reduce((s,l)=>s+l.lat,0)/pts.length : 20.5937;
    const clon = pts.length ? pts.reduce((s,l)=>s+l.lon,0)/pts.length : 78.9629;
    _map = L.map('map-view', {zoomControl:true}).setView([clat,clon], pts.length?6:5);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution:'&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>'
    }).addTo(_map);
  }
  _mapMarkers.forEach(m=>_map.removeLayer(m));
  _mapMarkers = [];
  const mc = {positive:'#56d364',completed:'#58a6ff',negative:'#f85149',no_answer:'#e3b341',not_called:'#8b949e',failed:'#f85149'};
  pts.forEach(l=>{
    const col = mc[l.r1_status] || '#8b949e';
    const m = L.circleMarker([l.lat,l.lon], {radius:7,color:col,fillColor:col,fillOpacity:.8,weight:1});
    m.bindPopup(`<b>${escHtml(l.name)}</b><br>${escHtml(l.category)}<br>${escHtml(l.r1_status)}`);
    m.addTo(_map);
    _mapMarkers.push(m);
  });
  setTimeout(()=>_map.invalidateSize(), 50);
}
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

// ── Live console ──────────────────────────────────────────────
let _liveSource = null;
let _liveRunId  = null;

function appendLiveLine(ts, statusText, text){
  const c = document.getElementById('live-console');
  if(c.querySelector('.live-empty')) c.innerHTML='';
  const d = document.createElement('div');
  d.className='live-line';
  d.innerHTML=`<span class="live-ts">${escHtml(ts||'')}</span><span class="live-status">${escHtml(statusText)}</span><span class="live-text">${escHtml(text||'')}</span>`;
  c.appendChild(d);
  c.scrollTop=c.scrollHeight;
}

function openLiveStream(runId){
  if(_liveSource){ _liveSource.close(); }
  _liveRunId = runId;
  _liveSource = new EventSource('/api/live/'+runId);
  document.getElementById('live-indicator').style.display='inline';
  _liveSource.onmessage = function(e){
    const ev = JSON.parse(e.data);
    if(ev.type==='status'){
      appendLiveLine(new Date().toLocaleTimeString(), ev.status, ev.summary||'');
      if(ev.transcript&&ev.transcript.length){
        ev.transcript.forEach(l=>appendLiveLine(l.time, l.speaker, l.text));
      }
    } else if(ev.type==='done'){
      appendLiveLine('', 'DONE', ev.status||'');
      document.getElementById('live-indicator').style.display='none';
      _liveSource.close(); _liveSource=null;
    }
  };
}

async function pollLiveRuns(){
  try {
    const runs = await fetch('/api/live-runs').then(r=>r.json());
    if(runs.length>0 && runs[0]!==_liveRunId){
      openLiveStream(runs[0]);
      // Auto-switch to Live tab if not already there
      if(document.getElementById('live-view') && !document.getElementById('live-view').classList.contains('active')){
        switchTab('live');
      }
    }
  } catch(e){}
}

// ── Templates ─────────────────────────────────────────────────
async function loadTemplates(){
  try {
    const tpls = await fetch('/api/templates').then(r=>r.json());
    const sel = document.getElementById('tpl-select');
    if(!sel) return;
    // Keep the blank first option
    while(sel.options.length>1) sel.remove(1);
    tpls.forEach(t=>{
      const o = document.createElement('option');
      o.value = t.name;
      o.textContent = t.name;
      o.dataset.tpl = JSON.stringify(t);
      sel.appendChild(o);
    });
  } catch(e){}
}

function applyTemplate(){
  const sel = document.getElementById('tpl-select');
  const opt = sel.options[sel.selectedIndex];
  if(!opt||!opt.dataset.tpl) { document.getElementById('tpl-info').textContent=''; return; }
  const t = JSON.parse(opt.dataset.tpl);
  const info = [t.region&&'Region: '+t.region, t.language&&'Lang: '+t.language, t.persona_name&&'Persona: '+t.persona_name].filter(Boolean).join(' · ');
  document.getElementById('tpl-info').textContent = info;
}

async function promptSaveTemplate(){
  const name = prompt('Template name (used with --template NAME flag):');
  if(!name||!name.trim()) return;
  // Save the first campaign's goal_script as a template
  if(!_lastData||!_lastData.length){ alert('No campaign data loaded yet.'); return; }
  const c = _lastData[0];
  try {
    const r = await fetch('/api/templates', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({name: name.trim(), goal_script: c.goal_script||'', region:'', language:''})
    });
    const res = await r.json();
    if(res.ok){ alert('Template "'+name+'" saved!'); loadTemplates(); }
    else { alert('Save failed: '+(res.error||'unknown')); }
  } catch(e){ alert('Error: '+e); }
}

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
              <button class="raw-btn" onclick="event.stopPropagation();this.closest('.inf-val').querySelector('.val-full').style.display='inline';this.parentNode.style.display='none'">more</button>
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
  _lastData = data;

  loadTemplates();
  pollLiveRuns();

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
                  ${l.reliability&&l.reliability.score?`<span class="rel-badge rel-${escHtml(l.reliability.score)}">${l.reliability.score==='green'?'✓ reliable':l.reliability.score==='red'?'✗ low':'~ ok'}</span>`:''}
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

  if(_activeTab==='analytics') renderAnalytics(data);
  if(_activeTab==='map') renderMap(data);
}

// Countdown + auto-refresh
let t=8;
setInterval(()=>{ t--; document.getElementById('cd').textContent=t; if(t<=0){t=8;load();pollLiveRuns();} },1000);
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
    from reliability import compute_all_reliability
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
                   LEFT JOIN (
                       SELECT lead_id, extracted_fields FROM call_logs
                       WHERE id IN (SELECT MAX(id) FROM call_logs WHERE round=1 GROUP BY lead_id)
                   ) r1log ON r1log.lead_id=l.id
                   LEFT JOIN (
                       SELECT lead_id, extracted_fields FROM call_logs
                       WHERE id IN (SELECT MAX(id) FROM call_logs WHERE round=2 GROUP BY lead_id)
                   ) r2log ON r2log.lead_id=l.id
                   WHERE l.campaign_id=? ORDER BY l.id""",
                (c["id"],)
            ).fetchall()

            try:
                rel_map = compute_all_reliability(conn, c["id"])
            except Exception:
                rel_map = {}

            leads = []
            for l in leads_raw:
                r1_ef = json.loads(l["r1_fields"]) if l["r1_fields"] else {}
                r2_ef = json.loads(l["r2_fields"]) if l["r2_fields"] else {}

                # Separate transcript from inference; handle string vs list format
                raw_tr = r1_ef.pop("transcript", [])
                if isinstance(raw_tr, str):
                    from caller import parse_transcript_to_json
                    transcript = parse_transcript_to_json({"result": {"transcript": raw_tr}})
                else:
                    transcript = raw_tr or []
                # Also check r2 for transcript if r1 has none
                if not transcript:
                    raw_tr2 = r2_ef.pop("transcript", [])
                    if isinstance(raw_tr2, str):
                        from caller import parse_transcript_to_json
                        transcript = parse_transcript_to_json({"result": {"transcript": raw_tr2}})
                    else:
                        transcript = raw_tr2 or []
                else:
                    r2_ef.pop("transcript", None)
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
                    "reliability":    rel_map.get(l["id"], {"score": "grey", "answer_rate": 0, "attempts": 0}),
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


@app.route("/api/live-runs")
def api_live_runs():
    """Returns list of run_ids currently being polled."""
    try:
        from caller import active_live_runs
        return jsonify(active_live_runs())
    except Exception:
        return jsonify([])


@app.route("/api/live/<run_id>")
def api_live_stream(run_id):
    """SSE stream for a live call run."""
    from caller import register_live_queue, unregister_live_queue
    q = register_live_queue(run_id)

    def _generate():
        try:
            while True:
                try:
                    event = q.get(timeout=20)
                    yield f"data: {json.dumps(event)}\n\n"
                    if event.get("type") == "done":
                        break
                except _queue.Empty:
                    yield ": ping\n\n"  # keep-alive
        finally:
            unregister_live_queue(run_id)

    return Response(stream_with_context(_generate()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/templates", methods=["GET"])
def api_templates_get():
    from models import list_templates
    return jsonify(list_templates())


@app.route("/api/templates", methods=["POST"])
def api_templates_post():
    from models import save_template, init_db
    init_db()
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"ok": False, "error": "name required"}), 400
    try:
        save_template(
            name=name,
            goal_script=data.get("goal_script"),
            persona_name=data.get("persona_name"),
            persona_tone=data.get("persona_tone", "professional"),
            region=data.get("region"),
            language=data.get("language"),
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    init_db()
    start_scheduler_thread()
    print("Dashboard: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", debug=False, port=5000)
