# Vendor Discovery & Outreach Agent

Automatically discover local vendors via OpenStreetMap and conduct two-round AI phone outreach using CALL-E — without any manual research.

Built for the CALL-E Hackathon (AIRUDDER Pte Ltd, deadline Sep 14 2026).

---

## What it does

1. **Discover** — queries OpenStreetMap/Overpass for businesses matching your product keyword in any city, filters to those with phone numbers
2. **Qualify (Round 1)** — CALL-E agent calls each vendor to check interest
3. **Capture (Round 2)** — follows up with positive vendors to collect pricing, quantities, timeline, and contact name
4. **Infer** — Groq (Llama 3.3-70B) extracts structured intelligence from every transcript
5. **Store** — SQLite database with full audit trail; Excel export available
6. **Dashboard** — live web UI auto-refreshing every 8 seconds

---

## Requirements

- Python 3.9+
- Node.js (for `calle` CLI)
- `calle` npm package: `npm install -g @calle-ai/cli`
- CALL-E account at [calle.ai](https://calle.ai)

Install Python dependencies:
```
pip install flask timezonefinder openpyxl tzdata groq requests
```

Set environment variables (never hardcode):
```
set GROQ_API_KEY=<your-groq-key>
```

---

## Usage

### Dry run (no real calls placed)
```
python main.py --product "office chairs" --location "London, UK" --dry-run
```

### Real campaign
```
python main.py --product "leather shoes" --location "London, UK" --limit 5 --yes
```

### With Excel export
```
python main.py --product "hardware tools" --location "Berlin, Germany" --limit 10 --export-excel results.xlsx
```

### All flags
```
  --product      Product or service to source (required)
  --location     City or region to search (required)
  --limit        Max vendors to discover (default 10)
  --region       Region hint for CALL-E, e.g. GB, US, IN
  --language     Language hint for CALL-E, e.g. English
  --dry-run      Plan calls but do NOT execute — safe for testing
  --yes / -y     Skip all interactive confirmation prompts
  --export-excel Export results to .xlsx after campaign
```

### Web dashboard
```
python dashboard.py
# Open http://127.0.0.1:5000
```
Auto-refreshes every 8s. Shows all campaigns, masked phone numbers, R1/R2 status, AI summaries, and consent timestamps.

---

## Architecture

```
main.py              Orchestrator: discovery -> consent gate -> R1 calls -> R2 calls
discovery.py         OpenStreetMap/Overpass API vendor search
script_gen.py        Goal script generator + client approval prompt
caller.py            CALL-E plan/run/poll pipeline + Groq transcript inference
business_hours.py    Timezone-aware business hours gate (blocks calls outside 09:00-18:00 local)
models.py            SQLite schema: campaigns, leads, call_logs
dashboard.py         Flask web UI
```

### Consent gate

Every campaign records `consent_approved_at` (UTC ISO timestamp) and `consent_basis` in the database at the moment the client confirms the vendor list. No call is dispatched before this checkpoint. The `--yes` flag auto-confirms but still records the timestamp — it does not bypass the gate.

### Business hours

Before each call, `business_hours.py` resolves the vendor's timezone from lat/lon (via `timezonefinder`) and checks Mon-Fri 09:00-18:00 local. Calls outside this window are logged as `skipped / outside_business_hours` — not failed.

### Phone masking

All phone numbers are masked (`+44****123`) in logs, the dashboard, Excel output, and any file that could appear in version control. Raw phones are stored only in the SQLite database (not committed to git).

---

## Database

SQLite at `vendor_discovery.db` (auto-created on first run, not committed to git).

Tables: `campaigns`, `leads`, `call_logs`.

Key lead fields: `masked_phone`, `candidate_id` (stable OSM URI), `skip_reason`, `consent_basis`.

---

## Side effects

Running without `--dry-run` places **real phone calls** via CALL-E to the discovered vendors. Each call consumes CALL-E credits. Estimated: 1-2 calls per vendor per round.

Cancellation: there is no mid-campaign cancel. To stop, kill the process (Ctrl+C). Already-placed calls will complete; no further calls will be dispatched.

---

## OSM Attribution

Data (c) OpenStreetMap contributors (ODbL) — https://openstreetmap.org/copyright

---

## License

MIT
