from datetime import datetime, timezone
from src.database.models import is_valid_transition
from src.dispatcher.scheduler import is_within_business_hours
from src.dispatcher.smtp_client import build_subject


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
