# Project Cleanup and Clean Skeleton Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clean up legacy implementation clutter and establish a minimal, unopinionated, protocol-driven skeleton scaffold for the apparel export sales automation pipeline.

**Architecture:** Python `Protocol`-driven modular architecture adhering to `docs/principle.md`. Each pipeline stage (`ingest`, `scraper`, `classifier`, `dispatcher`, `database`, `web`) exposes a clean, decoupled interface, backed by lightweight Pydantic domain models.

**Tech Stack:** Python 3.11+, Pydantic v2, pydantic-settings, HTTPX, Pytest, UV.

## Global Constraints

- Strict adherence to `docs/principle.md`: modularity over monoliths, small focused files, zero comment spam.
- Library-agnostic protocols: no hard-coding of heavy scraping frameworks (e.g. crawl4ai) or specific LLM runtime packages.
- Clean environment: reset `data/leads.db` and delete old implementation files.

---

### Task 1: Update Configuration and Build Tooling

**Files:**
- Modify: `pyproject.toml`
- Modify: `Makefile`
- Modify: `.env.example`

**Interfaces:**
- Consumes: None
- Produces: Minimal dependencies definition and developer Make targets (`install`, `test`, `clean`).

- [ ] **Step 1: Update `pyproject.toml` with lightweight dependencies**

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

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Update `Makefile` with clean standard targets**

```makefile
.PHONY: help install test clean

help:
	@echo "Available commands:"
	@echo "  make install   Install dependencies"
	@echo "  make test      Run test suite"
	@echo "  make clean     Clean temporary caches and artifacts"

install:
	uv sync --extra dev

test:
	pytest -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
```

- [ ] **Step 3: Update `.env.example`**

```env
APP_ENV=development
LOG_LEVEL=INFO
DATABASE_PATH=data/leads.db
```

- [ ] **Step 4: Run `uv sync --extra dev` to verify clean dependencies lock**

Run: `uv sync --extra dev`
Expected: Successfully synced environment.

- [ ] **Step 5: Commit build tooling changes**

```bash
git add pyproject.toml Makefile .env.example uv.lock
git commit -m "chore(config): trim dependencies to core essentials and update build tooling"
```

---

### Task 2: Remove Clutter and Legacy Files

**Files:**
- Delete: `data/leads.db`
- Delete: `src/classifier/system1_laya.py`, `src/classifier/system2_ollama.py`
- Delete: `src/scraper/crawler.py`, `src/scraper/filters.py`
- Delete: `src/dispatcher/smtp_client.py`, `src/dispatcher/scheduler.py`
- Delete: `src/database/connection.py`, `src/database/models.py`
- Delete: `src/ingest/seed.py`
- Delete: `src/web/app.py`, `src/web/static/`, `src/web/templates/`
- Delete: `tests/test_scraper.py`, `tests/test_classifier.py`, `tests/test_dispatcher.py`
- Delete: `docs/superpowers/plans/2026-10-06-timezone-enforcement-and-smtp-testing.md`
- Delete: `docs/superpowers/specs/2026-10-06-timezone-enforcement-and-smtp-testing-design.md`

**Interfaces:**
- Consumes: None
- Produces: Cleaned project tree without legacy clutter.

- [ ] **Step 1: Remove legacy code, database, tests, and obsolete specs**

```bash
rm -f data/leads.db
rm -f src/classifier/system1_laya.py src/classifier/system2_ollama.py
rm -f src/scraper/crawler.py src/scraper/filters.py
rm -f src/dispatcher/smtp_client.py src/dispatcher/scheduler.py
rm -f src/database/connection.py src/database/models.py
rm -f src/ingest/seed.py
rm -rf src/web/static src/web/templates src/web/app.py
rm -f tests/test_scraper.py tests/test_classifier.py tests/test_dispatcher.py
rm -f docs/superpowers/plans/2026-10-06-timezone-enforcement-and-smtp-testing.md
rm -f docs/superpowers/specs/2026-10-06-timezone-enforcement-and-smtp-testing-design.md
```

- [ ] **Step 2: Clean `__pycache__` artifacts**

```bash
make clean
```

- [ ] **Step 3: Commit removal of cluttered legacy files**

```bash
git add -u
git commit -m "chore(cleanup): remove cluttered legacy implementation files and obsolete specs"
```

---

### Task 3: Implement Domain Models and Core Configuration

**Files:**
- Create: `src/models.py`
- Modify: `src/config.py`

**Interfaces:**
- Consumes: Pydantic v2
- Produces: `LeadStatus`, `Lead`, `GarmentAnalysis`, `OutreachMessage`, `Settings`

- [ ] **Step 1: Write failing test for domain models and config**

In `tests/test_scaffold.py`:
```python
from datetime import datetime
from src.models import Lead, LeadStatus, GarmentAnalysis, OutreachMessage
from src.config import Settings

def test_domain_models():
    lead = Lead(domain="examplebrand.com", status=LeadStatus.queued)
    assert lead.domain == "examplebrand.com"
    assert lead.status == LeadStatus.queued
    assert isinstance(lead.created_at, datetime)

    analysis = GarmentAnalysis(is_apparel_brand=True, detected_categories=["hoodies"])
    assert analysis.is_apparel_brand is True

    msg = OutreachMessage(
        recipient_email="hello@examplebrand.com",
        subject="Direct Garment Export",
        body_text="Hi there",
    )
    assert msg.recipient_email == "hello@examplebrand.com"

def test_settings_load():
    settings = Settings()
    assert settings.app_env in ["development", "production", "test"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scaffold.py -v`
Expected: FAIL (ModuleNotFoundError or AttributeError)

- [ ] **Step 3: Implement `src/models.py`**

```python
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field


class LeadStatus(str, Enum):
    queued = "queued"
    scraping = "scraping"
    classified = "classified"
    pending_approval = "pending_approval"
    approved = "approved"
    sent = "sent"
    rejected = "rejected"
    failed = "failed"


class Lead(BaseModel):
    domain: str
    status: LeadStatus = LeadStatus.queued
    brand_name: str | None = None
    contact_email: str | None = None
    hook: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GarmentAnalysis(BaseModel):
    is_apparel_brand: bool
    detected_categories: list[str] = Field(default_factory=list)
    aesthetic_notes: str | None = None


class OutreachMessage(BaseModel):
    recipient_email: str
    subject: str
    body_text: str
```

- [ ] **Step 4: Implement `src/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"
    database_path: str = "data/leads.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_scaffold.py -v`
Expected: PASS

- [ ] **Step 6: Commit models and configuration**

```bash
git add src/models.py src/config.py tests/test_scaffold.py
git commit -m "feat(core): implement core domain models and lightweight configuration"
```

---

### Task 4: Implement Pipeline Protocol Interfaces

**Files:**
- Create: `src/database/repository.py`
- Create: `src/ingest/loader.py`
- Create: `src/scraper/crawler.py`
- Create: `src/classifier/analyzer.py`
- Create: `src/dispatcher/sender.py`
- Create: `src/web/server.py`
- Update: `src/__init__.py`, `src/database/__init__.py`, `src/ingest/__init__.py`, `src/scraper/__init__.py`, `src/classifier/__init__.py`, `src/dispatcher/__init__.py`, `src/web/__init__.py`

**Interfaces:**
- Consumes: `src.models.Lead`, `src.models.LeadStatus`, `src.models.GarmentAnalysis`, `src.models.OutreachMessage`
- Produces: `LeadRepository`, `SeedLoader`, `StoreCrawler`, `BrandAnalyzer`, `OutboundSender`, `ReviewServer`

- [ ] **Step 1: Add protocol tests to `tests/test_scaffold.py`**

```python
from typing import runtime_checkable, Protocol
from src.database.repository import LeadRepository
from src.ingest.loader import SeedLoader
from src.scraper.crawler import StoreCrawler
from src.classifier.analyzer import BrandAnalyzer
from src.dispatcher.sender import OutboundSender
from src.web.server import ReviewServer

def test_protocol_interfaces_exist():
    assert issubclass(LeadRepository, Protocol)
    assert issubclass(SeedLoader, Protocol)
    assert issubclass(StoreCrawler, Protocol)
    assert issubclass(BrandAnalyzer, Protocol)
    assert issubclass(OutboundSender, Protocol)
    assert issubclass(ReviewServer, Protocol)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scaffold.py -k test_protocol_interfaces_exist -v`
Expected: FAIL

- [ ] **Step 3: Implement protocol files and package `__init__.py` files**

Create `src/database/repository.py`:
```python
from typing import Protocol, runtime_checkable
from src.models import Lead, LeadStatus


@runtime_checkable
class LeadRepository(Protocol):
    def save_lead(self, lead: Lead) -> None: ...
    def get_lead(self, domain: str) -> Lead | None: ...
    def list_by_status(self, status: LeadStatus, limit: int = 50) -> list[Lead]: ...
    def update_status(self, domain: str, status: LeadStatus) -> None: ...
```

Create `src/ingest/loader.py`:
```python
from pathlib import Path
from typing import Protocol, runtime_checkable
from src.models import Lead


@runtime_checkable
class SeedLoader(Protocol):
    def load_seeds(self, source_path: Path | str) -> list[Lead]: ...
```

Create `src/scraper/crawler.py`:
```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class StoreCrawler(Protocol):
    def crawl(self, domain: str) -> dict[str, str]: ...
```

Create `src/classifier/analyzer.py`:
```python
from typing import Protocol, runtime_checkable
from src.models import GarmentAnalysis


@runtime_checkable
class BrandAnalyzer(Protocol):
    def analyze(self, domain: str, storefront_data: dict[str, str]) -> GarmentAnalysis: ...
```

Create `src/dispatcher/sender.py`:
```python
from typing import Protocol, runtime_checkable
from src.models import OutreachMessage


@runtime_checkable
class OutboundSender(Protocol):
    def send(self, message: OutreachMessage) -> bool: ...
```

Create `src/web/server.py`:
```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class ReviewServer(Protocol):
    def run(self, host: str = "127.0.0.1", port: int = 8000) -> None: ...
```

Ensure all package `__init__.py` files cleanly expose their interface:
- `src/__init__.py`
- `src/database/__init__.py`: `from .repository import LeadRepository; __all__ = ["LeadRepository"]`
- `src/ingest/__init__.py`: `from .loader import SeedLoader; __all__ = ["SeedLoader"]`
- `src/scraper/__init__.py`: `from .crawler import StoreCrawler; __all__ = ["StoreCrawler"]`
- `src/classifier/__init__.py`: `from .analyzer import BrandAnalyzer; __all__ = ["BrandAnalyzer"]`
- `src/dispatcher/__init__.py`: `from .sender import OutboundSender; __all__ = ["OutboundSender"]`
- `src/web/__init__.py`: `from .server import ReviewServer; __all__ = ["ReviewServer"]`

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scaffold.py -v`
Expected: PASS

- [ ] **Step 5: Commit protocol interfaces**

```bash
git add src/ tests/test_scaffold.py
git commit -m "feat(scaffold): add clean protocol interfaces for all pipeline modules"
```

---

### Task 5: End-to-End Verification and Push to Remote

**Files:**
- Entire repository

- [ ] **Step 1: Run full test suite**

Run: `make test`
Expected: All tests pass cleanly.

- [ ] **Step 2: Run `make clean` and verify directory tree**

Run: `make clean && git status`
Expected: Working tree clean, no untracked clutter.

- [ ] **Step 3: Push commits to GitHub**

Run: `git push -u origin feat/dispatcher-timezone-and-smtp-testing`
Expected: Successfully pushed to remote repository.
