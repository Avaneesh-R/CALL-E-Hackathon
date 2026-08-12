# Verification Report — CALL-E Vendor Discovery Pipeline
Generated: 2026-08-08

---

## ITEM 1 — CLI Environment

| Check | Result |
|-------|--------|
| `calle auth status` | AUTHENTICATED — token valid until 2029-05-04 |
| MCP tools available | `plan_call`, `run_call`, `get_call_run` — all 3 confirmed |
| `ANTHROPIC_API_KEY` | **NOT SET** — AI inference will silently fail without this |

**Action required before building:** `$env:ANTHROPIC_API_KEY = "sk-ant-..."` must be set permanently (System env, not just session).

---

## ITEM 2 — DevPost Rules (re-verified live)

Handout Section 1 is **fully accurate**. No amendments detected. Key confirmed facts:
- Deadline: September 14, 2026, 11:45am SGT
- 20 free calls on new account; up to 200 more requestable (1-5 business days, sponsor discretion)
- Judging: Real World Impact / Quality of Idea / Technical Implementation / Product Experience — equally weighted
- Submission requires: working project + GitHub PR + text description + ≤3-min video

**No changes from handout.** Safe to build against.

---

## ITEM 3 — Repo Policy (CONTRIBUTING + safety.md + SKILL.md + contract)

### What's confirmed safe
- The vendor-discovery + outreach concept is acceptable under repo rules
- Consent design (client approves vendor list before R1 starts) directly satisfies the `consent_or_outreach_basis` runtime gate requirement in the generated-skill-contract spec
- OSM as source is fine (no credential issues, no scraping ToS problems)

### Non-negotiable requirements from the repo (must implement)

**From CONTRIBUTING.md:**
1. **Dry-run path required** — every executable component must have a `--dry-run` or `plan-only` mode that doesn't place real calls. *We have `--dry-run` already; verify it works end-to-end.*
2. **Masked phone numbers in all sample output** — any README examples, logs, or docs must use masked numbers (e.g. `+44*****8560`), not real ones
3. **No secrets or tokens in repo** — CALL-E tokens, ANTHROPIC_API_KEY must be env vars only, never hardcoded or in sample files
4. **Complete setup docs** — README must include install steps, env var config, and usage examples
5. **Side effects documented** — the README must explicitly state what real-world actions the tool takes (places real phone calls to real numbers)

**From generated-skill-contract.md (mandatory candidate schema fields):**
```json
{
  "candidateId":      "source-stable-id",        // osm_id works
  "phoneNumber":      "+E164",
  "maskedPhoneNumber": "+44*****1234",
  "recipientLabel":   "business name",
  "outboundGoal":     "compiled goal string",
  "status":           "ready | skip | called | ...",
  "skipReason":       ""
}
```
Our `Lead` data model needs `maskedPhoneNumber` and `skipReason` added.

**From generated-skill-contract.md (consent_or_outreach_basis):**
The consent gate must happen before any calls. Our pre-R1 approval step already satisfies this — just needs a `consent_basis` field stored in the Campaign record. Suggested value: `"client-approved-vendor-list"`.

**From design-principles.md (Principle 7 — critical for submission):**
> "Default tests should run without live credentials or actual calls using dry-run or planning modes."

The test suite and README examples must work in dry-run. Do not require a CALL-E account just to run tests.

**From generated-skill-contract.md (source records must not provide raw goals):**
OSM business names/categories must never be concatenated directly into the CALL-E goal string. The Script Generator module must compile goals from the product description only, treating OSM data as untrusted display labels. *This is already the case in script_gen.py — confirm it stays that way.*

---

## ITEM 4 — get_call_run Output Shape (confirmed from live calls)

Already confirmed from real call data collected during this session:

```json
{
  "status": "COMPLETED",
  "result": {
    "summary": "...",
    "post_summary": "...",
    "outcome": {
      "task_completed": true,
      "completion_confidence": { "score": 0.88, "label": "high" }
    },
    "extracted": { "transcript": "[HH:MM:SS] SPEAKER: text\n..." },
    "transcript": "[HH:MM:SS] SPEAKER: text\n...",
    "call_id": "...",
    "calling": {
      "duration_seconds": 46,
      "calls": [{ "status": "finished", "hangup_type": "ByRobot", ... }]
    }
  }
}
```

**Status field caveat:** API returns `"NO ANSWER"` (space), not `"NO_ANSWER"` (underscore). Already fixed in `caller.py` with `.upper().replace(" ", "_")`. Verify classify_round1 and poll_until_done both use this normalization — they do.

**R1 classification is viable:** `outcome.task_completed` (bool) + `completion_confidence.score` + transcript text → sufficient for LLM-based interest/sentiment classification.

**R2 field capture:** `result.extracted` contains whatever CALL-E's agent captured. The goal script must explicitly ask for each field and repeat it back for confirmation (not rely on post-hoc extraction). This is the right design — stick to it.

---

## ITEM 5 — Reference Implementations

### batch-runner (`apps/python/batch-runner`)
- Does: plan → run → poll loop on JSONL input files; writes `call_e_results.jsonl` and `call_e_status_events.jsonl`
- Has: dry-run mode, configurable poll intervals, transcript extraction, Rich terminal output
- **Does NOT have:** vendor discovery, OSM integration, round-1/round-2 logic, consent gate, web dashboard, Excel export
- **Verdict:** Do not reuse — our pipeline is more complex. But adopt its JSONL result format for the GitHub PR submission (it's the established pattern in the repo).

### n8n-calle-api (`plugins/n8n-calle-api`)
- IVR quality testing plugin, not outreach
- Useful pattern: `callItemId` for idempotency, masked phone in every result record
- **Verdict:** Borrow the result schema shape; nothing to reuse directly.

---

## ITEM 6 — OSM Coverage (confirmed)

| Region | Category | Vendors found | With phone |
|--------|----------|---------------|------------|
| London, UK | shoes | 5+ | 5 (100%) |
| San Francisco, US | shoes | 8 | 8 (100%) |
| South Delhi, India | shoes | ~50 | ~2 (4%) |

**London and SF are solid for live demos.** India is too sparse for a reliable demo — use CSV-upload fallback or a Western city. This is already in the handout; confirmed.

---

## ITEM 7 — Consolidated Findings

### Confirmed safe to build on
- CALL-E pipeline (plan → run → poll) works end-to-end, status/transcript shape confirmed
- OSM discovery works reliably for UK/US
- 2-round structure with auto R1→R2 progression is valid
- Pre-R1 consent gate design satisfies repo policy
- classify_round1 bug (`"NO ANSWER"` space) already fixed

### Changes from handout assumptions
- `--timeout-seconds` = 15s is the **CLI HTTP request timeout**, not per-call. `--poll-timeout-seconds` = 300s is the polling timeout. Our custom poll loop (40×15s = 600s) is fine and deliberately longer.
- No specific `consent_basis` enum is mandated — `"client-approved-vendor-list"` is a valid value we can define.

### Blockers before any production code ships

| Blocker | Fix |
|---------|-----|
| `ANTHROPIC_API_KEY` not set | Set as system env var permanently |
| `Lead` model missing `maskedPhoneNumber` + `skipReason` + `consent_basis` on Campaign | Add to `models.py` |
| No README with setup/usage/side-effect docs | Write before GitHub PR |
| No formal dry-run test that works without CALL-E account | Add dry-run integration test |

### Does not force a redesign
Everything in the handout's design (Sections 3–11) is implementable as specified. No technical blockers found.

---

## Next: Implementation Order

1. Set `ANTHROPIC_API_KEY` (you do this — I can't)
2. Update `models.py` — add missing fields
3. Build web dashboard (Flask/FastAPI + live polling table)
4. Add business-hours timezone gate to `caller.py`
5. Add Excel export to `main.py`
6. Write README with dry-run instructions
7. Test full pipeline end-to-end on London shoes (2-3 real calls)
8. Prep GitHub PR for `apps/python/vendor-discovery-agent`
