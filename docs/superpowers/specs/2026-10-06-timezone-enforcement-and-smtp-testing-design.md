# Design Specification: Timezone Business Hours Enforcement and Robust SMTP Testing

## Overview
This specification details the integration of timezone-aware business hours scheduling and comprehensive SMTP test coverage for the autonomous export engine dispatcher.

The implementation strictly adheres to the clean code principles outlined in `docs/principle.md` (modularity, separation of concerns, zero line-by-line spam comments, atomic git commits) and the architectural constraints in `docs/agent.md`.

## Architecture & Modules

### 1. `src/dispatcher/scheduler.py`
Responsible for evaluating country-specific business hours and selecting the next eligible lead from the SQLite database.

- **`COUNTRY_BUSINESS_HOURS_UTC`**: UTC business hour lookup table:
  - `US`: `(13, 22)` (09:00 - 18:00 Eastern / Central / Pacific coverage)
  - `UK`: `(9, 17)` (09:00 - 17:00 GMT / BST)
  - `AU`: `(0, 8)` (09:00 - 17:00 AEST)
  - `AE`: `(5, 13)` (09:00 - 17:00 GST / UTC+4)
- **`is_within_business_hours(country: Optional[str], dt: Optional[datetime] = None) -> bool`**:
  - Normalizes `dt` to UTC.
  - Returns `True` if `country` is missing, unrecognized, or `OTHER`.
  - Checks if `start_hour <= dt.hour <= end_hour`.
- **`get_next_eligible_lead(conn: sqlite3.Connection, current_dt: Optional[datetime] = None) -> Optional[sqlite3.Row]`**:
  - Executes query:
    ```sql
    SELECT id, domain, brand_name, country, contact_name, contact_email,
           generated_subject, generated_pitch
    FROM leads
    WHERE status = 'approved' AND sent_at IS NULL
    ORDER BY id ASC
    ```
  - Iterates over pending candidate rows in FIFO order.
  - Evaluates `is_within_business_hours(row["country"], current_dt)`.
  - Returns the first lead satisfying business hours, or `None` if no lead is currently eligible.

### 2. `src/dispatcher/smtp_client.py`
Responsible for rate-limiting verification, MIME message construction, STARTTLS transport, jitter delay, and updating lead states.

- **`build_subject(contact_name: Optional[str], brand_name: Optional[str]) -> str`**:
  - Returns `"quick question - {contact_name}"` or `"{brand_name} knit sourcing"` or default `"garment knit sourcing trial"`.
- **`send_plain_text_email(to_email: str, subject: str, body: str) -> None`**:
  - Requires `smtp_user` and `smtp_password` in settings.
  - Generates `MIMEText(body, "plain", "utf-8")` (strictly plain text, no HTML/pixels).
  - Connects to `smtp_host:smtp_port` with STARTTLS and issues login and message delivery.
- **`count_emails_sent_last_24h(conn: Optional[sqlite3.Connection] = None) -> int`**:
  - Accepts optional SQLite connection or opens connection from settings.
  - Counts rows where `status = 'sent' AND sent_at >= datetime('now', '-24 hours')`.
- **`dispatch_next_approved_lead(conn: Optional[sqlite3.Connection] = None, current_dt: Optional[datetime] = None) -> bool`**:
  - Returns `False` if 24-hour limit (`dispatch_daily_limit`, 25) is reached.
  - Calls `get_next_eligible_lead(conn, current_dt)`. If `None`, returns `False`.
  - If lead is missing `contact_email`, sets `status = 'failed'` and `error_log = 'Missing contact_email'`, returning `True`.
  - Calls `send_plain_text_email`.
    - On success: marks `status = 'sent'`, sets `sent_at = CURRENT_TIMESTAMP`, applies randomized sleep `[dispatch_min_delay_seconds, dispatch_max_delay_seconds]`, returns `True`.
    - On `(SMTPAuthenticationError, SMTPDataError, SMTPException, OSError)`: marks `status = 'failed'`, records exception in `error_log`, returns `True`.
- **`run_dispatcher_loop(poll_interval: float = 30.0, once: bool = False) -> None`**:
  - Continually polls until interrupted or once processed if `once=True`.

### 3. Testing Suite (`tests/test_dispatcher.py`)
Provides complete coverage across all paths:
- MIME message creation and SMTP handshake mocking (STARTTLS, login, headers).
- Missing credential assertion (`ValueError`).
- State transitions (`approved` -> `sent` with `sent_at`).
- Failed state transitions with error logs for missing emails, authentication errors, data errors, and network timeouts.
- Daily limit cap (25 sent emails in last 24h prevents new sends).
- Timezone matrix verification for all target countries.
- Lead queue selection with timezone skipping (skipping out-of-hours leads and picking eligible leads).
