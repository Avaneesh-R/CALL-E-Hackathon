# Vendor Discovery & Outreach Agent — Design Handout

Before building the full production pipeline I need your answers to the questions below.
Each section is independent — answer what you know, skip what you don't.

---

## 1. Product Vision

**Q1.1 — Who uses this?**
Who is the end user running campaigns?
- [ ] Me personally (single user, CLI is fine)
- [ ] A small team (need multi-user support)
- [ ] Clients / customers (need a proper UI / web app)

**Q1.2 — Core use case?**
What is the #1 thing this tool does?
- [ ] Source new suppliers for a product (B2B procurement)
- [ ] Appreciation / relationship calls to existing vendors
- [ ] Lead generation / cold outreach for a service
- [ ] All of the above (configurable per campaign)

**Q1.3 — Campaign scope**
How many vendors per campaign, typically?
- [ ] 5–20 (demo / small batch)
- [ ] 20–100 (medium campaign)
- [ ] 100+ (need bulk/async processing)

---

## 2. Pipeline Flow

**Q2.1 — Round structure**
Keep the current 2-round structure (R1 = qualify, R2 = collect details)?
- [ ] Yes, 2 rounds is correct
- [ ] Only Round 1 needed (qualify and stop)
- [ ] 3+ rounds (e.g. R3 = schedule a meeting)

**Q2.2 — Human gate between rounds**
After R1, before R2 calls go out:
- [ ] Fully automatic — if R1 = positive, auto-proceed to R2
- [ ] Human approval required — show me the R1 results first, I confirm R2
- [ ] AI decides — if AI confidence is high enough, auto-proceed

**Q2.3 — Failed / no-answer handling**
If a vendor doesn't answer:
- [ ] Skip permanently
- [ ] Retry once after 45 min (CALL-E's suggestion)
- [ ] Retry at next business-hours window
- [ ] Flag for manual callback

**Q2.4 — After R2, what next?**
- [ ] Just a report / transcript is enough
- [ ] Auto-send a follow-up email to interested vendors
- [ ] Push to a CRM (which one?)
- [ ] Export to CSV / Google Sheets
- [ ] All of the above

---

## 3. Interface

**Q3.1 — How do you want to run campaigns?**
- [ ] CLI (`python main.py --product ... --location ...`) — current approach
- [ ] Simple web UI (browser, runs locally)
- [ ] Hosted web app (deploy to cloud)
- [ ] All three (CLI + web)

**Q3.2 — Real-time monitoring**
While calls are in progress, do you want to:
- [ ] See a live feed of call status in terminal
- [ ] See a live dashboard in browser
- [ ] Just get a summary at the end

**Q3.3 — Results output format**
- [ ] Terminal table (current)
- [ ] JSON file
- [ ] CSV export
- [ ] PDF report
- [ ] All of the above

---

## 4. AI Inference

**Q4.1 — Do you have an Anthropic API key?**
The AI inference step needs `ANTHROPIC_API_KEY` set in your environment.
- [ ] Yes, I'll set it now: `$env:ANTHROPIC_API_KEY = "sk-ant-..."`
- [ ] No, use rule-based classification only (keyword matching)
- [ ] No, skip inference entirely for now

**Q4.2 — What should AI extract from R1 transcripts?**
- [ ] Interest level (high / medium / low / none)
- [ ] Sentiment (positive / neutral / negative)
- [ ] Key objections or concerns raised
- [ ] Whether to recommend proceeding to R2
- [ ] All of the above

**Q4.3 — What should AI extract from R2 transcripts?**
- [ ] Contact name
- [ ] Can supply / quantity
- [ ] Price range
- [ ] Timeline / availability
- [ ] Next steps agreed
- [ ] All of the above

---

## 5. Discovery

**Q5.1 — Data source**
OpenStreetMap works for Western cities. For India (Hauz Khas, etc.) OSM phone coverage is poor.
- [ ] OSM only — I'll use Western cities for demos
- [ ] Add a manual CSV upload option (paste in vendor list)
- [ ] Add JustDial / India-specific scraping
- [ ] I'll provide my own vendor lists

**Q5.2 — Which regions will you demo?**
- [ ] UK / London
- [ ] US (SF, NYC, LA)
- [ ] India (Delhi, Mumbai)
- [ ] Other: ___________

**Q5.3 — How many vendors per campaign max?**
Number: _____

---

## 6. CALL-E Specifics

**Q6.1 — Call quota / budget**
How many calls can you make per day on your CALL-E account?
Number: _____

**Q6.2 — Business hours enforcement**
Should the system automatically refuse to call outside business hours (9am–6pm local time)?
- [ ] Yes — detect timezone from vendor location and gate calls
- [ ] No — let me handle timing manually

**Q6.3 — Caller introduction**
The current goal script introduces the bot as "a sourcing agent." Should it:
- [ ] Keep as-is
- [ ] Use a specific company/product name: ___________
- [ ] Be customisable per campaign

---

## 7. Hackathon Submission

**Q7.1 — What does the submission need?**
- [ ] Working demo (live CLI / web app)
- [ ] Demo video
- [ ] GitHub repo with README
- [ ] Slide deck / pitch
- [ ] All of the above

**Q7.2 — Deadline**
Date / time: ___________

**Q7.3 — Judging criteria**
What are judges scoring on?
(e.g. technical innovation, real-world usefulness, UX, AI integration, originality)
Answer: ___________

**Q7.4 — Team size**
- [ ] Solo
- [ ] 2–3 people
- [ ] 4+ people

---

## 8. Nice-to-Haves (rank if you want)

- [ ] Scheduled campaigns (call at a specific time)
- [ ] Multi-product / multi-location in one run
- [ ] Vendor deduplication across campaigns
- [ ] Call recording playback
- [ ] Confidence scores on AI inference
- [ ] WhatsApp / SMS follow-up after call
- [ ] Auto-generated email draft for interested vendors

---

## Quick Decisions I Can Make Now (no answer needed)

These I'll implement by default unless you say otherwise:

- SQLite for local storage (easy to inspect, no setup)
- OSM for discovery (free, no ToS issues)
- `claude-haiku-4-5` for AI inference (fast, cheap, per-call)
- Max 40 polls × 15s = 10 min timeout per call
- Calls run sequentially per campaign (no parallel, avoids rate limits)
- `--yes` flag to skip all confirmation prompts in demo mode

---

*Answer inline or tell me verbally — I'll build from whatever you give me.*
