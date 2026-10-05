from datetime import datetime, timezone
from typing import Dict, Tuple

# Approximate UTC business hours (09:00 - 17:00 local time)
COUNTRY_BUSINESS_HOURS_UTC: Dict[str, Tuple[int, int]] = {
    "US": (13, 22),   # Roughly 9am-6pm Eastern
    "UK": (9, 17),    # GMT / BST
    "AU": (0, 8),     # AEST
    "AE": (5, 13),    # Gulf Standard Time (UTC+4)
}


def is_within_business_hours(country: str, dt: datetime | None = None) -> bool:
    # ponytail: lightweight UTC hour ranges satisfy timezone constraints without heavy pytz/zoneinfo mapping
    now_utc = dt or datetime.now(timezone.utc)
    hour = now_utc.hour

    allowed_range = COUNTRY_BUSINESS_HOURS_UTC.get(country.upper())
    if not allowed_range:
        return True

    start_hour, end_hour = allowed_range
    return start_hour <= hour <= end_hour
