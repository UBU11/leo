# Timezone Business Hours Enforcement and Robust SMTP Testing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate timezone business hours filtering into the lead dispatching queue and establish a robust, reliable test suite covering plain-text SMTP transport, error states, and daily rate limits.

**Architecture:** Split responsibilities cleanly between `src/dispatcher/scheduler.py` (which determines active business hour windows and evaluates lead timezone eligibility from the database) and `src/dispatcher/smtp_client.py` (which executes rate-limiting, plain-text MIME creation, TLS transport, and state transitions). Tests in `tests/test_dispatcher.py` thoroughly mock network calls to verify all success and failure branches.

**Tech Stack:** Python 3.11+, standard library `smtplib`, `ssl`, `email.mime.text`, `sqlite3`, `datetime`, and `pytest`.

## Global Constraints
- Strictly adhere to `docs/principle.md`: modularity over monoliths, no clutter comments, meaningful naming, early returns, atomic git commits (`feat(scope): ...` or `test(scope): ...`).
- Adhere to `docs/agent.md`: plain text outreach (`text/plain`, UTF-8), zero HTML/trackers, randomized delay 150-360s, max 25 emails/24h.
- All database write operations must use explicit transactions (`with conn:`).

---

### Task 1: Timezone Business Hours Filtering in Scheduler

**Files:**
- Modify: `src/dispatcher/scheduler.py`
- Test: `tests/test_dispatcher.py`

**Interfaces:**
- Produces:
  - `is_within_business_hours(country: Optional[str], dt: Optional[datetime] = None) -> bool`
  - `get_next_eligible_lead(conn: sqlite3.Connection, current_dt: Optional[datetime] = None) -> Optional[sqlite3.Row]`

- [ ] **Step 1: Write failing tests for scheduler in `tests/test_dispatcher.py`**

```python
from datetime import datetime, timezone
import sqlite3
import pytest
from src.database.models import SCHEMA_SQL
from src.dispatcher.scheduler import is_within_business_hours, get_next_eligible_lead

def test_is_within_business_hours_boundaries():
    # US active (13-22 UTC)
    assert is_within_business_hours("US", datetime(2026, 10, 5, 14, 0, tzinfo=timezone.utc)) is True
    assert is_within_business_hours("US", datetime(2026, 10, 5, 4, 0, tzinfo=timezone.utc)) is False

    # UK active (9-17 UTC)
    assert is_within_business_hours("UK", datetime(2026, 10, 5, 10, 0, tzinfo=timezone.utc)) is True
    assert is_within_business_hours("UK", datetime(2026, 10, 5, 20, 0, tzinfo=timezone.utc)) is False

    # AU active (0-8 UTC)
    assert is_within_business_hours("AU", datetime(2026, 10, 5, 2, 0, tzinfo=timezone.utc)) is True
    assert is_within_business_hours("AU", datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)) is False

    # AE active (5-13 UTC)
    assert is_within_business_hours("AE", datetime(2026, 10, 5, 7, 0, tzinfo=timezone.utc)) is True
    assert is_within_business_hours("AE", datetime(2026, 10, 5, 18, 0, tzinfo=timezone.utc)) is False

    # Unknown or None country defaults to True
    assert is_within_business_hours("OTHER", datetime(2026, 10, 5, 4, 0, tzinfo=timezone.utc)) is True
    assert is_within_business_hours(None, datetime(2026, 10, 5, 4, 0, tzinfo=timezone.utc)) is True

def test_get_next_eligible_lead_timezone_skipping():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)

    # Insert two approved leads: id=1 is AU (inactive at 15:00 UTC), id=2 is US (active at 15:00 UTC)
    with conn:
        conn.execute(
            """
            INSERT INTO leads (domain, country, contact_name, contact_email, status)
            VALUES ('au-brand.com', 'AU', 'Mate', 'mate@au-brand.com', 'approved'),
                   ('us-brand.com', 'US', 'John', 'john@us-brand.com', 'approved')
            """
        )

    eval_dt = datetime(2026, 10, 5, 15, 0, tzinfo=timezone.utc)
    lead = get_next_eligible_lead(conn, current_dt=eval_dt)
    assert lead is not None
    assert lead["domain"] == "us-brand.com"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/pytest tests/test_dispatcher.py -k "test_get_next_eligible_lead_timezone_skipping" -v`
Expected: FAIL (cannot import `get_next_eligible_lead`)

- [ ] **Step 3: Implement `is_within_business_hours` normalization and `get_next_eligible_lead` in `src/dispatcher/scheduler.py`**

```python
from datetime import datetime, timezone
import sqlite3
from typing import Dict, Optional, Tuple

COUNTRY_BUSINESS_HOURS_UTC: Dict[str, Tuple[int, int]] = {
    "US": (13, 22),
    "UK": (9, 17),
    "AU": (0, 8),
    "AE": (5, 13),
}


def is_within_business_hours(country: Optional[str], dt: Optional[datetime] = None) -> bool:
    if not country:
        return True

    allowed_range = COUNTRY_BUSINESS_HOURS_UTC.get(country.upper())
    if not allowed_range:
        return True

    now_utc = dt.astimezone(timezone.utc) if dt else datetime.now(timezone.utc)
    start_hour, end_hour = allowed_range
    return start_hour <= now_utc.hour <= end_hour


def get_next_eligible_lead(
    conn: sqlite3.Connection,
    current_dt: Optional[datetime] = None,
) -> Optional[sqlite3.Row]:
    cursor = conn.execute(
        """
        SELECT id, domain, brand_name, country, contact_name, contact_email,
               generated_subject, generated_pitch
        FROM leads
        WHERE status = 'approved' AND sent_at IS NULL
        ORDER BY id ASC
        """
    )
    for lead in cursor.fetchall():
        if is_within_business_hours(lead["country"], current_dt):
            return lead
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `./.venv/bin/pytest tests/test_dispatcher.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dispatcher/scheduler.py tests/test_dispatcher.py
git commit -m "feat(dispatcher): add timezone business hours filtering and lead selection"
```

---

### Task 2: Dispatcher Lead Processing & Timezone Integration

**Files:**
- Modify: `src/dispatcher/smtp_client.py`
- Test: `tests/test_dispatcher.py`

**Interfaces:**
- Consumes:
  - `get_next_eligible_lead` from `src.dispatcher.scheduler`
  - `get_db_connection` from `src.database.connection`
- Produces:
  - `count_emails_sent_last_24h(conn: Optional[sqlite3.Connection] = None) -> int`
  - `dispatch_next_approved_lead(conn: Optional[sqlite3.Connection] = None, current_dt: Optional[datetime] = None) -> bool`

- [ ] **Step 1: Write failing test for dispatcher integrating `get_next_eligible_lead` and handling DB connection injection**

```python
from unittest.mock import patch

def test_dispatch_next_approved_lead_integrates_timezone():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)

    with conn:
        conn.execute(
            """
            INSERT INTO leads (domain, country, contact_name, contact_email, status, generated_subject, generated_pitch)
            VALUES ('au-brand.com', 'AU', 'Mate', 'mate@au-brand.com', 'approved', 'AU Subject', 'Pitch'),
                   ('us-brand.com', 'US', 'John', 'john@us-brand.com', 'approved', 'US Subject', 'Pitch')
            """
        )

    eval_dt = datetime(2026, 10, 5, 15, 0, tzinfo=timezone.utc)
    with patch("src.dispatcher.smtp_client.send_plain_text_email") as mock_send, \
         patch("time.sleep"):
        dispatched = dispatch_next_approved_lead(conn=conn, current_dt=eval_dt)

        assert dispatched is True
        mock_send.assert_called_once_with(to_email="john@us-brand.com", subject="US Subject", body="Pitch")

        # Verify AU remains approved and US is sent
        au_row = conn.execute("SELECT status, sent_at FROM leads WHERE domain = 'au-brand.com'").fetchone()
        us_row = conn.execute("SELECT status, sent_at FROM leads WHERE domain = 'us-brand.com'").fetchone()
        assert au_row["status"] == "approved"
        assert au_row["sent_at"] is None
        assert us_row["status"] == "sent"
        assert us_row["sent_at"] is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/pytest tests/test_dispatcher.py -k "test_dispatch_next_approved_lead_integrates_timezone" -v`
Expected: FAIL

- [ ] **Step 3: Update `src/dispatcher/smtp_client.py` to use `get_next_eligible_lead` and injected `conn`**

Refactor `count_emails_sent_last_24h` and `dispatch_next_approved_lead` to:
1. Accept optional `conn: Optional[sqlite3.Connection] = None` and `current_dt: Optional[datetime] = None`.
2. Check 24-hour limit using `count_emails_sent_last_24h(active_conn)`.
3. Fetch candidate via `get_next_eligible_lead(active_conn, current_dt)`.
4. If no eligible lead, return `False`.
5. Guard against missing `contact_email`: set `status = 'failed'`, `error_log = 'Missing contact_email'`, return `True`.
6. Dispatch with `send_plain_text_email`, update `status = 'sent'`, `sent_at = CURRENT_TIMESTAMP`, sleep random jitter `[dispatch_min_delay_seconds, dispatch_max_delay_seconds]`, return `True`.
7. Catch `(smtplib.SMTPAuthenticationError, smtplib.SMTPDataError, smtplib.SMTPException, OSError)`: update `status = 'failed'`, `error_log = str(exc)`, return `True`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `./.venv/bin/pytest tests/test_dispatcher.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dispatcher/smtp_client.py tests/test_dispatcher.py
git commit -m "feat(dispatcher): integrate timezone selection and injectable connection in dispatcher"
```

---

### Task 3: Robust SMTP & Error Handling Test Suite

**Files:**
- Modify: `tests/test_dispatcher.py`

**Interfaces:**
- Consumes:
  - `send_plain_text_email`, `dispatch_next_approved_lead`, `count_emails_sent_last_24h` from `src.dispatcher.smtp_client`

- [ ] **Step 1: Add unit tests for SMTP transport & error handling in `tests/test_dispatcher.py`**

Implement:
1. `test_send_plain_text_email_success`: Mock `smtplib.SMTP` and verify `starttls`, `login`, and sent `MIMEText` (payload plain text, utf-8, Subject, From, To).
2. `test_send_plain_text_email_missing_credentials`: Unset credentials and verify `ValueError` is raised.
3. `test_dispatch_lead_missing_email`: Insert lead without email; verify transition to `failed` and `error_log = 'Missing contact_email'`.
4. `test_dispatch_smtp_auth_error`: Mock `send_plain_text_email` raising `smtplib.SMTPAuthenticationError(535, b'Invalid credentials')`; verify status updated to `failed` and exception logged.
5. `test_dispatch_smtp_data_or_network_error`: Mock `send_plain_text_email` raising `OSError('Connection refused')`; verify status updated to `failed` and exception logged.
6. `test_dispatch_daily_limit_reached`: Insert 25 leads with `status = 'sent'` and `sent_at = CURRENT_TIMESTAMP`; verify dispatcher returns `False` and does not process next approved lead.
7. `test_dispatch_jitter_delay_range`: Mock `time.sleep` and verify jitter sleep value is within configured bounds.

- [ ] **Step 2: Run all tests in the repository**

Run: `./.venv/bin/pytest -v`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_dispatcher.py
git commit -m "test(dispatcher): add robust test suite for SMTP transport, error handling, and rate limits"
```
