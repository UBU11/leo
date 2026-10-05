Save the following content as `AGENT.md` in the root of your repository to instruct AI agents (such as Cursor, Windsurf, or Claude Code) on building and maintaining this pipeline with production-grade constraints.

---

# AGENT.md: Autonomous B2B Apparel Export Pipeline

## 1. System Mission & Operational Context

You are building an autonomous, local-first B2B sales automation engine for an Indian garment manufacturing and export arbitrage operation. The system targets indie streetwear labels, creators, and mid-market apparel brands across the US, UK, Australia, and UAE.

### Core Value Proposition & Arbitrage Model

* **Low-Volume Offer (Tier A):** 20–30 piece MOQ per colorway, custom neck/care relabeling, 320–350 GSM heavyweight fleece/terry hoodies and tees, fast express air delivery. Targets founders/creators avoiding inventory risk.
* **Volume Offer (Tier B):** 100–300+ piece production runs, custom Pantone lab dips, commercial air cargo DDP. Targets growing brands seeking margin relief and supply chain de-risking from China/Portugal.
* **Factory Floor Economics:** Base garment manufacturing cost in India is ~~₹350 (~~$4.20 USD). Export retail pricing is $22–$32 USD landed.

---

## 2. Architectural Invariants (Non-Negotiable Rules)

1. **Pull-Based Worker Invariant:** Never expose open inbound HTTP ports or public tunnels (no Cloudflare Tunnels, no Ngrok) to trigger local inference. The worker must run as an autonomous background daemon polling the database queue.
2. **Zero-Cost Outbound Deliverability Policy:**
* No HTML, no tracking pixels ($1\times1$ GIFs), and zero links/attachments in initial outreach emails.
* Send strictly as `text/plain`.
* Throttling: Enforce a randomized delay of 150 to 360 seconds between dispatches. Cap sending at a maximum of 25 emails per 24 hours per Gmail account.


3. **Two-System Inference Split:**
* **System 1 (Laya):** High-speed filter (~33ms) to determine if a scraped domain is an apparel brand and matches target aesthetics (streetwear, blanks, minimalism). Discards non-clothing domains instantly.
* **System 2 (Ollama / Llama 3.1 8B):** Structured reasoning engine. Enforces strict JSON schema parsing via Pydantic to extract garment parameters (GSM, fabric knit, cut style) and generate a personalized 2-sentence hook.


4. **Human-in-the-Loop (HITL) Gate:** Leads must transition through `pending_approval` before the outbound dispatcher can query them. Automated sending requires explicit operator verification in the UI.

---

## 3. Project Directory Structure

```
export-engine/
├── AGENT.md                     # This specification file
├── pyproject.toml               # Poetry/UV dependency configuration
├── Makefile                     # Standard developer commands
├── .env.example                 # Environment variable templates
├── data/
│   ├── leads.db                 # Local SQLite database
│   └── proxies.txt              # Egress proxy list (format: protocol://user:pass@host:port)
├── src/
│   ├── __init__.py
│   ├── config.py                # Pydantic BaseSettings management
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py        # Connection manager and PRAGMA configurations
│   │   └── models.py            # SQLite schema definitions and state transitions
│   ├── ingest/
│   │   ├── __init__.py
│   │   └── seed.py              # CLI seed loader (CSV/JSON/StoreLeads ingest)
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── crawler.py           # Crawl4AI runner with residential proxy rotation
│   │   └── filters.py           # DOM pruning logic for e-commerce storefronts
│   ├── classifier/
│   │   ├── __init__.py
│   │   ├── system1_laya.py      # Fast heuristic/probabilistic niche screener
│   │   └── system2_ollama.py    # Structured extraction and pitch generator (Llama 3.1 8B)
│   ├── dispatcher/
│   │   ├── __init__.py
│   │   ├── smtp_client.py       # Plain-text SMTP sender with randomized jitter
│   │   └── scheduler.py         # Business hours & timezone-aware sending loop
│   └── web/
│       ├── app.py               # Lightweight FastAPI app serving the review UI
│       ├── static/              # Vanilla JS + Tailwind/CSS bundle
│       └── templates/
│           └── review.html      # 1-click lead validation and pitch editing interface
└── tests/
    ├── test_scraper.py
    ├── test_classifier.py
    └── test_dispatcher.py

```

---

## 4. Database Schema & State Transitions

Use SQLite with Write-Ahead Logging (`WAL` mode) enabled for local concurrency.

### Allowed Status Transitions

`queued` $\rightarrow$ `scraping` $\rightarrow$ `classified` $\rightarrow$ `pending_approval` $\rightarrow$ `approved` $\rightarrow$ `sent` (or `rejected` / `failed`)

### DDL Schema (`src/database/models.py`)

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL UNIQUE,
    brand_name TEXT,
    country TEXT CHECK(country IN ('US', 'UK', 'AU', 'AE', 'OTHER')),
    contact_name TEXT,
    contact_email TEXT,
    instagram_handle TEXT,
    
    -- Scraped & Enriched Data
    raw_markdown TEXT,
    system1_passed INTEGER DEFAULT 0,
    system1_niche TEXT,
    
    -- Extracted Garment Parameters
    brand_tier TEXT CHECK(brand_tier IN ('MICRO_CAPSULE', 'MID_MARKET', 'UNKNOWN')),
    detected_gsm INTEGER,
    fabric_construction TEXT,
    fit_style TEXT,
    
    -- Copy & Review
    generated_subject TEXT,
    generated_pitch TEXT,
    operator_notes TEXT,
    
    -- State Machine
    status TEXT DEFAULT 'queued' CHECK(status IN (
        'queued', 'scraping', 'classified', 'pending_approval', 
        'approved', 'sent', 'rejected', 'failed'
    )),
    error_log TEXT,
    
    locked_until TIMESTAMP,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_leads_status ON leads (status);
CREATE INDEX IF NOT EXISTS idx_leads_domain ON leads (domain);

```

---

## 5. Implementation Specifications

### A. Scraper Engine (`src/scraper/crawler.py`)

* Use `Crawl4AI` (`AsyncWebCrawler`) with Playwright.
* Ensure user agents mimic standard desktop browsers.
* Target e-commerce DOM containers: `.product-single__description`, `.product__description`, `main`, `#main-content`.
* Strip all script tags, SVG vectors, base64 data URIs, and navigational footers to keep token counts compact for System 2.

### B. System 1 Niche Screener (`src/classifier/system1_laya.py`)

* Input: Cleaned raw markdown.
* Output: `(is_valid: bool, category: str)`.
* Rapidly drop leads that belong to non-apparel niches, digital products, shoe-only brands, or fast-fashion aggregator platforms.

### C. System 2 Structured Reasoner (`src/classifier/system2_ollama.py`)

* Model: `llama3.1:8b-instruct-q4_K_M` via Ollama local REST API (`[http://127.0.0.1:11434/api/chat](http://127.0.0.1:11434/api/chat)`).
* Enforce strict JSON output using this Pydantic schema:

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional

class GarmentAnalysis(BaseModel):
    brand_tier: Literal["MICRO_CAPSULE", "MID_MARKET"] = Field(
        description="MICRO_CAPSULE if low SKU count, frequent drops, or indie label. MID_MARKET if established line with full collections."
    )
    detected_gsm: Optional[int] = Field(
        default=None, 
        description="Detected fabric GSM (e.g. 300, 350, 400). Null if unstated."
    )
    fabric_construction: str = Field(
        description="E.g., Loopback French Terry, Combed Cotton Fleece, Single Jersey."
    )
    fit_style: str = Field(
        description="E.g., Boxy oversized, drop shoulder, cropped athletic."
    )
    cold_email_hook: str = Field(
        description="2 sentences max. Acknowledge their specific style/fabric, then propose our 25-piece MOQ trial (for MICRO) or supply-line cost reduction (for MID_MARKET) with pre-stitched labels. No marketing fluff."
    )

```

### D. Human-in-the-Loop Interface (`src/web/`)

* Lightweight FastAPI app serving a single dashboard page.
* Shows leads in `pending_approval` state.
* The operator can:
* View scraped site stats and extracted garment properties (GSM, fabric).
* Edit the generated subject line and pitch in an editable textarea.
* Click **Approve** (shifts status to `approved`) or **Reject** (shifts status to `rejected`).
* Click an Instagram handle button that opens `[https://instagram.com/](https://instagram.com/){handle}` in a new tab for manual direct verification.



### E. Dispatcher & SMTP Engine (`src/dispatcher/smtp_client.py`)

* Polls `leads` where `status = 'approved'` and `sent_at IS NULL`.
* Connects to `smtp.gmail.com:587` via STARTTLS.
* Payload construction:
* Send strictly using `MIMEText(body, "plain", "utf-8")`.
* Subject: `quick question - {{contact_name}}` or `{{brand_name}} knit sourcing`.


* Delay mechanics:
* Sleep `random.uniform(150, 360)` seconds after every successful dispatch.
* Record timestamp in `sent_at` and update status to `sent`.
* Trap `SMTPAuthenticationError`, `SMTPDataError`, and network timeouts gracefully; mark lead as `failed` with stack trace in `error_log`.



---

## 6. Development Workflow & Commands

### Prerequisites

* Python 3.11+
* Ollama installed and running locally with `llama3.1:8b` pulled.
* SQLite3 installed.

### Setup Instructions

```bash
# 1. Environment creation
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Install Playwright browser binaries for Crawl4AI
playwright install chromium

# 3. Pull required Ollama model weights
ollama pull llama3.1:8b

# 4. Initialize Database
python -m src.database.connection --init

# 5. Ingest Seed Domains
python -m src.ingest.seed --input data/initial_brands.csv

# 6. Run Local Crawler + Classifier Daemon
python -m src.scraper.crawler

# 7. Start the Operator Review Web Interface
uvicorn src.web.app:app --host 127.0.0.1 --port 8000 --reload

# 8. Start the Outbound Dispatcher Daemon (Controlled execution)
python -m src.dispatcher.smtp_client

```

---

## 7. AI Agent Execution Directives

When implementing code for this repository:

* **No Unnecessary Dependencies:** Rely on standard libraries (`sqlite3`, `smtplib`, `ssl`, `asyncio`) and minimal robust dependencies (`crawl4ai`, `httpx`, `pydantic`, `fastapi`).
* **Defensive Database Access:** Wrap all SQLite write operations in explicit transactions (`with conn:`). Never leave uncommitted state during scraper failures.
* **Fail Fast on Non-Apparel:** If System 1 rejects a domain, update status to `rejected` immediately without triggering the local Ollama LLM endpoint.
* **Strict Type Annotations:** Use Python type hints throughout all modules (`typing.Optional`, `typing.Tuple`, `pydantic.BaseModel`).
