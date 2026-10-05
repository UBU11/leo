# AGENT.md: Autonomous B2B Apparel Export Pipeline

## 1. System Mission & Operational Context

Autonomous, local-first B2B sales automation engine for an Indian garment manufacturing and export arbitrage operation targeting indie streetwear labels, creators, and mid-market apparel brands across US, UK, Australia, and UAE.

### Value Proposition & Arbitrage Model
- **Low-Volume Offer (Tier A):** 20–30 piece MOQ per colorway, custom neck/care relabeling, 320–350 GSM heavyweight fleece/terry hoodies and tees, fast express air delivery.
- **Volume Offer (Tier B):** 100–300+ piece production runs, custom Pantone lab dips, commercial air cargo DDP.
- **Economics:** Base garment manufacturing cost in India is ~₹350 (~$4.20 USD). Export retail pricing is $22–$32 USD landed.

---

## 2. Architectural Invariants

1. **Pull-Based Worker Invariant:** Never expose open inbound HTTP ports or public tunnels. Background daemons poll SQLite.
2. **Zero-Cost Outbound Deliverability Policy:**
   - Strict `text/plain` only: no HTML, no tracking pixels, zero links/attachments in initial outreach.
   - Throttling: Randomized delay of 150-360 seconds between dispatches. Max 25 emails / 24h per Gmail account.
3. **Two-System Inference Split:**
   - **System 1 (Laya):** High-speed heuristic filter (~33ms) screening for apparel relevance.
   - **System 2 (Ollama / Llama 3.1 8B):** Structured reasoning engine generating JSON garment analysis and 2-sentence hook.
4. **Human-in-the-Loop (HITL) Gate:** Operator verification in UI transitions `pending_approval` -> `approved`.

---

## 3. Project Directory Structure

```
├── AGENT.md
├── pyproject.toml
├── Makefile
├── .env.example
├── data/
│   ├── leads.db
│   ├── proxies.txt
│   └── initial_brands.csv
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   └── models.py
│   ├── ingest/
│   │   ├── __init__.py
│   │   └── seed.py
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── crawler.py
│   │   └── filters.py
│   ├── classifier/
│   │   ├── __init__.py
│   │   ├── system1_laya.py
│   │   └── system2_ollama.py
│   ├── dispatcher/
│   │   ├── __init__.py
│   │   ├── smtp_client.py
│   │   └── scheduler.py
│   └── web/
│       ├── __init__.py
│       ├── app.py
│       ├── static/
│       │   └── app.js
│       └── templates/
│           └── review.html
└── tests/
    ├── __init__.py
    ├── test_scraper.py
    ├── test_classifier.py
    └── test_dispatcher.py
```

---

## 4. State Machine Transitions

`queued` -> `scraping` -> `classified` -> `pending_approval` -> `approved` -> `sent` (or `rejected` / `failed`)
