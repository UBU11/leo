import sqlite3
from datetime import datetime, timezone

from unittest.mock import patch

from src.database.models import SCHEMA_SQL, is_valid_transition
from src.dispatcher.scheduler import get_next_eligible_lead, is_within_business_hours
from src.dispatcher.smtp_client import build_subject, dispatch_next_approved_lead



def test_build_subject_variants():
    assert build_subject("Alex", "Solitude") == "quick question - Alex"
    assert build_subject("", "Solitude") == "Solitude knit sourcing"
    assert build_subject(None, None) == "garment knit sourcing trial"


def test_lead_state_transitions():
    assert is_valid_transition("queued", "scraping") is True
    assert is_valid_transition("scraping", "classified") is True
    assert is_valid_transition("pending_approval", "approved") is True
    assert is_valid_transition("approved", "sent") is True
    # Disallowed direct jump
    assert is_valid_transition("queued", "sent") is False


def test_business_hours_filter():
    # 15:00 UTC is within US (13-22) and UK (9-17)
    test_dt = datetime(2026, 10, 5, 15, 0, tzinfo=timezone.utc)
    assert is_within_business_hours("US", test_dt) is True
    assert is_within_business_hours("UK", test_dt) is True


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

        au_row = conn.execute("SELECT status, sent_at FROM leads WHERE domain = 'au-brand.com'").fetchone()
        us_row = conn.execute("SELECT status, sent_at FROM leads WHERE domain = 'us-brand.com'").fetchone()
        assert au_row["status"] == "approved"
        assert au_row["sent_at"] is None
        assert us_row["status"] == "sent"
        assert us_row["sent_at"] is not None


