import sqlite3
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

# Approximate UTC business hours (09:00 - 17:00 local time)
# ponytail: lightweight UTC hour ranges satisfy timezone constraints without heavy pytz/zoneinfo mapping
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

