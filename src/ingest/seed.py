import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from src.database.connection import get_db_connection

VALID_COUNTRIES = {"US", "UK", "AU", "AE"}


def clean_domain(raw_domain: str) -> str:
    domain = raw_domain.strip().lower()
    if domain.startswith(("http://", "https://")):
        parsed = urlparse(domain)
        domain = parsed.netloc
    return domain.removeprefix("www.")


def normalize_country(country: Optional[str]) -> str:
    if not country:
        return "OTHER"
    code = country.strip().upper()
    return code if code in VALID_COUNTRIES else "OTHER"


def load_records_from_file(file_path: Path) -> List[Dict[str, Any]]:
    # ponytail: stdlib csv.DictReader and json.load cover CSV/JSON with zero external deps
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else [data]

    with file_path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def seed_leads(file_path: str | Path, db_path: Optional[str | Path] = None) -> int:
    source_path = Path(file_path).resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Seed source not found: {source_path}")

    raw_records = load_records_from_file(source_path)
    inserted_count = 0

    with get_db_connection(db_path) as conn:
        for record in raw_records:
            raw_domain = record.get("domain") or record.get("url") or ""
            domain = clean_domain(raw_domain)
            if not domain:
                continue

            brand_name = record.get("brand_name") or record.get("name")
            country = normalize_country(record.get("country"))
            contact_name = record.get("contact_name")
            contact_email = record.get("contact_email") or record.get("email")
            instagram_handle = (record.get("instagram_handle") or record.get("instagram") or "").lstrip("@")

            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO leads (
                    domain, brand_name, country, contact_name, contact_email, instagram_handle, status
                ) VALUES (?, ?, ?, ?, ?, ?, 'queued')
                """,
                (domain, brand_name, country, contact_name, contact_email, instagram_handle),
            )
            inserted_count += cursor.rowcount

    return inserted_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed initial brands into leads database")
    parser.add_argument("--input", required=True, help="Path to seed CSV or JSON file")
    parser.add_argument("--db-path", type=str, default=None, help="Optional database file path")
    args = parser.parse_args()

    count = seed_leads(args.input, args.db_path)
    print(f"Seeded {count} new lead(s) into database.")


if __name__ == "__main__":
    main()
