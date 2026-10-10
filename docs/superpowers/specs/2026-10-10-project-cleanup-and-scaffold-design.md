# Design Spec: Clean Project Scaffold & Clutter Removal

## 1. Context & Motivation

The repository previously accumulated specific implementations (Crawl4AI browser scrapers, Ollama/Laya dual-system classifiers, SMTP daemons, and database migrations) that cluttered the workspace. The goal is to clear legacy implementation clutter while preserving the core vision defined in [AGENT.md](file:///home/ubu/Documents/dev/ai/leo/AGENT.md) and adhering to the clean code principles in [docs/principle.md](file:///home/ubu/Documents/dev/ai/leo/docs/principle.md).

This specification outlines the complete reset to a modular, unopinionated skeleton scaffold with clear Python `Protocol` interfaces, lightweight dependencies, and clean testing infrastructure.

---

## 2. Directory Layout & Changes

### 2.1 Files to Remove
* Legacy implementations:
  * `src/classifier/system1_laya.py`, `src/classifier/system2_ollama.py`
  * `src/scraper/crawler.py`, `src/scraper/filters.py`
  * `src/dispatcher/smtp_client.py`, `src/dispatcher/scheduler.py`
  * `src/database/connection.py`, `src/database/models.py`
  * `src/ingest/seed.py`
  * `src/web/app.py`, `src/web/static/`, `src/web/templates/`
  * `src/config.py` (legacy implementation)
  * `tests/test_scraper.py`, `tests/test_classifier.py`, `tests/test_dispatcher.py`
  * `data/leads.db` (reset legacy SQLite database)
  * Obsolete docs in `docs/superpowers/plans/` and `docs/superpowers/specs/` (excluding this new spec)
  * Cached artifacts: `.pytest_cache`, `__pycache__`

### 2.2 Files to Retain
* `AGENT.md`: Core system mission, arbitrage model, and pipeline state machine definition.
* `docs/principle.md`: Strict modularity, clean code, and zero-clutter commenting standards.
* `data/initial_brands.csv`, `data/proxies.txt`: Template seed files for brand discovery.
* `README.md`: High-level project summary.

### 2.3 New Scaffold Structure
```
leo/
├── AGENT.md
├── README.md
├── Makefile
├── pyproject.toml
├── .env.example
├── data/
│   ├── initial_brands.csv
│   └── proxies.txt
├── docs/
│   ├── principle.md
│   └── superpowers/
├── src/
│   ├── __init__.py
│   ├── config.py              # Lightweight settings class
│   ├── models.py              # Domain entities (Lead, GarmentAnalysis, OutreachMessage, LeadStatus)
│   ├── database/
│   │   ├── __init__.py
│   │   └── repository.py      # LeadRepository protocol
│   ├── ingest/
│   │   ├── __init__.py
│   │   └── loader.py          # SeedLoader protocol
│   ├── scraper/
│   │   ├── __init__.py
│   │   └── crawler.py         # StoreCrawler protocol
│   ├── classifier/
│   │   ├── __init__.py
│   │   └── analyzer.py        # BrandAnalyzer protocol
│   ├── dispatcher/
│   │   ├── __init__.py
│   │   └── sender.py          # OutboundSender protocol
│   └── web/
│       ├── __init__.py
│       └── server.py          # Minimal review interface stub
└── tests/
    ├── __init__.py
    └── test_scaffold.py       # Import and protocol conformance tests
```

---

## 3. Core Domain Models & Protocols

### 3.1 Domain Models (`src/models.py`)
* `LeadStatus`: String Enum representing the lifecycle states:
  * `queued`, `scraping`, `classified`, `pending_approval`, `approved`, `sent`, `rejected`, `failed`
* `Lead`: Dataclass or Pydantic model with:
  * `domain: str`
  * `status: LeadStatus = LeadStatus.queued`
  * `brand_name: str | None = None`
  * `contact_email: str | None = None`
  * `hook: str | None = None`
  * `created_at: datetime`
* `GarmentAnalysis`: Result of brand evaluation:
  * `is_apparel_brand: bool`
  * `detected_categories: list[str]`
  * `aesthetic_notes: str | None = None`
* `OutreachMessage`: Outbound message structure:
  * `recipient_email: str`
  * `subject: str`
  * `body_text: str`

### 3.2 Protocol Interfaces
* **`LeadRepository` (`src/database/repository.py`):**
  * `save_lead(lead: Lead) -> None`
  * `get_lead(domain: str) -> Lead | None`
  * `list_by_status(status: LeadStatus, limit: int = 50) -> list[Lead]`
  * `update_status(domain: str, status: LeadStatus) -> None`
* **`SeedLoader` (`src/ingest/loader.py`):**
  * `load_seeds(source_path: str) -> list[Lead]`
* **`StoreCrawler` (`src/scraper/crawler.py`):**
  * `crawl(domain: str) -> dict[str, str]` (raw scraped storefront data)
* **`BrandAnalyzer` (`src/classifier/analyzer.py`):**
  * `analyze(domain: str, storefront_data: dict[str, str]) -> GarmentAnalysis`
* **`OutboundSender` (`src/dispatcher/sender.py`):**
  * `send(message: OutreachMessage) -> bool`
* **`ReviewServer` (`src/web/server.py`):**
  * Minimal factory/runner function stub for human-in-the-loop review.

---

## 4. Dependencies & Tooling

### 4.1 `pyproject.toml`
Trimmed to remove heavy scrapers and model runtimes:
```toml
[project]
name = "export-engine"
version = "0.1.0"
description = "Autonomous B2B sales automation engine for garment export"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.7.0",
    "pydantic-settings>=2.2.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.0",
]
```

### 4.2 `Makefile`
Clean developer targets:
* `make install`: Syncs dependencies using uv.
* `make test`: Runs pytest suite.
* `make clean`: Removes `__pycache__`, `.pytest_cache`, and temporary files.

---

## 5. Verification Plan

1. Verify legacy cluttered files are safely removed.
2. Verify all new modules import cleanly without errors.
3. Verify test suite passes via `pytest -v`.
4. Ensure `git status` reflects an organized, atomic commit.
