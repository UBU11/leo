import argparse
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Generator, Optional

from src.config import get_settings
from src.database.models import SCHEMA_SQL


def get_db_path(custom_path: Optional[str | Path] = None) -> Path:
    if custom_path:
        return Path(custom_path).resolve()
    return get_settings().resolved_database_path


def init_db(custom_path: Optional[str | Path] = None) -> Path:
    target_path = get_db_path(custom_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(target_path) as conn:
        conn.executescript(SCHEMA_SQL)
    return target_path


@contextmanager
def get_db_connection(custom_path: Optional[str | Path] = None) -> Generator[sqlite3.Connection, None, None]:
    target_path = get_db_path(custom_path)
    # ponytail: stdlib sqlite3 context manager handles transaction commit/rollback
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        with conn:
            yield conn
    finally:
        conn.close()


# ponytail: alias get_db to get_db_connection for convenient imports
get_db = get_db_connection



def main() -> None:
    parser = argparse.ArgumentParser(description="Database management utility")
    parser.add_argument("--init", action="store_true", help="Initialize database schema")
    parser.add_argument("--db-path", type=str, default=None, help="Custom database file path")
    args = parser.parse_args()

    if args.init:
        db_path = init_db(args.db_path)
        print(f"Database initialized successfully at: {db_path}")


if __name__ == "__main__":
    main()
