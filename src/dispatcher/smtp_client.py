from contextlib import contextmanager
from datetime import datetime
from email.mime.text import MIMEText
import random
import smtplib
import ssl
import sqlite3
import time
from typing import Generator, Optional

from src.config import get_settings
from src.database.connection import get_db_connection
from src.dispatcher.scheduler import get_next_eligible_lead


def build_subject(contact_name: Optional[str], brand_name: Optional[str]) -> str:
    if contact_name and contact_name.strip():
        return f"quick question - {contact_name.strip()}"
    if brand_name and brand_name.strip():
        return f"{brand_name.strip()} knit sourcing"
    return "garment knit sourcing trial"


def send_plain_text_email(
    to_email: str,
    subject: str,
    body: str,
) -> None:
    settings = get_settings()
    if not settings.smtp_user or not settings.smtp_password:
        raise ValueError("SMTP_USER and SMTP_PASSWORD must be configured in environment")

    # ponytail: stdlib smtplib + email.mime.text enforces strictly text/plain without html or trackers
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = f"{settings.sender_name} <{settings.smtp_user}>" if settings.sender_name else settings.smtp_user
    msg["To"] = to_email

    context = ssl.create_default_context()
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30.0) as server:
        server.starttls(context=context)
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)


@contextmanager
def _active_connection(conn: Optional[sqlite3.Connection] = None) -> Generator[sqlite3.Connection, None, None]:
    if conn is not None:
        yield conn
        return
    settings = get_settings()
    with get_db_connection(settings.database_path) as active_conn:
        yield active_conn


def count_emails_sent_last_24h(conn: Optional[sqlite3.Connection] = None) -> int:
    with _active_connection(conn) as active_conn:
        row = active_conn.execute(
            """
            SELECT COUNT(*) as sent_count 
            FROM leads 
            WHERE status = 'sent' AND sent_at >= datetime('now', '-24 hours')
            """
        ).fetchone()
        return row["sent_count"] if row else 0


def dispatch_next_approved_lead(
    conn: Optional[sqlite3.Connection] = None,
    current_dt: Optional[datetime] = None,
) -> bool:
    settings = get_settings()

    with _active_connection(conn) as active_conn:
        if count_emails_sent_last_24h(active_conn) >= settings.dispatch_daily_limit:
            print("[DISPATCHER] Daily sending limit reached (25/24h). Pausing.")
            return False

        lead = get_next_eligible_lead(active_conn, current_dt)
        if not lead:
            return False

        lead_id = lead["id"]
        to_email = lead["contact_email"]
        if not to_email:
            active_conn.execute(
                """
                UPDATE leads 
                SET status = 'failed', error_log = 'Missing contact_email', updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
                """,
                (lead_id,),
            )
            active_conn.commit()
            return True

        subject = lead["generated_subject"] or build_subject(lead["contact_name"], lead["brand_name"])
        body = lead["generated_pitch"] or ""

        try:
            send_plain_text_email(to_email=to_email, subject=subject, body=body)
            active_conn.execute(
                """
                UPDATE leads 
                SET status = 'sent', sent_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
                """,
                (lead_id,),
            )
            active_conn.commit()
            print(f"[DISPATCHER] Sent email to {to_email} ({lead['domain']})")

            delay = random.uniform(settings.dispatch_min_delay_seconds, settings.dispatch_max_delay_seconds)
            print(f"[DISPATCHER] Enforcing randomized jitter delay of {delay:.1f}s")
            time.sleep(delay)
        except (smtplib.SMTPAuthenticationError, smtplib.SMTPDataError, smtplib.SMTPException, OSError) as exc:
            active_conn.execute(
                """
                UPDATE leads 
                SET status = 'failed', error_log = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
                """,
                (str(exc), lead_id),
            )
            active_conn.commit()
            print(f"[DISPATCHER] Failed sending to {to_email}: {exc}")

        return True


def run_dispatcher_loop(poll_interval: float = 30.0, once: bool = False) -> None:
    print("[DISPATCHER] Outbound dispatcher daemon started.")
    while True:
        processed = dispatch_next_approved_lead()
        if once and not processed:
            break
        if not processed:
            time.sleep(poll_interval)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Outbound plain-text SMTP dispatcher")
    parser.add_argument("--once", action="store_true", help="Dispatch single approved lead and exit")
    parser.add_argument("--poll-interval", type=float, default=30.0, help="Polling interval in seconds")
    args = parser.parse_args()

    run_dispatcher_loop(poll_interval=args.poll_interval, once=args.once)


if __name__ == "__main__":
    main()
