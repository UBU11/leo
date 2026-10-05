import asyncio
from pathlib import Path
import random
from typing import List, Optional

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

from src.config import get_settings
from src.database.connection import get_db_connection
from src.scraper.filters import clean_markdown_or_text

DEFAULT_DESKTOP_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def load_proxies(proxy_file_path: str | Path) -> List[str]:
    path = Path(proxy_file_path).resolve()
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        # ponytail: filter comments and blank lines with inline list comprehension
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


async def scrape_domain(
    domain: str,
    crawler: AsyncWebCrawler,
    proxy: Optional[str] = None,
) -> str:
    url = domain if domain.startswith(("http://", "https://")) else f"https://{domain}"
    run_config = CrawlerRunConfig(
        word_count_threshold=10,
        remove_overlay_elements=True,
    )
    result = await crawler.arun(url=url, config=run_config)
    if not result.success:
        raise RuntimeError(f"Crawl failed for {url}: {result.error_message}")
    
    raw_content = result.markdown or result.cleaned_html or ""
    return clean_markdown_or_text(raw_content)


async def process_next_lead(crawler: AsyncWebCrawler, proxies: List[str]) -> bool:
    settings = get_settings()
    lead_id: Optional[int] = None
    domain: Optional[str] = None

    with get_db_connection(settings.database_path) as conn:
        row = conn.execute(
            """
            SELECT id, domain FROM leads 
            WHERE status = 'queued' 
            ORDER BY id ASC LIMIT 1
            """
        ).fetchone()

        if not row:
            return False

        lead_id = row["id"]
        domain = row["domain"]
        conn.execute("UPDATE leads SET status = 'scraping', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (lead_id,))

    proxy = random.choice(proxies) if proxies else None

    try:
        markdown_text = await scrape_domain(domain, crawler, proxy)
        with get_db_connection(settings.database_path) as conn:
            conn.execute(
                """
                UPDATE leads 
                SET raw_markdown = ?, status = 'classified', updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
                """,
                (markdown_text, lead_id),
            )
        print(f"[CRAWLER] Scraped successfully: {domain}")
    except Exception as exc:
        with get_db_connection(settings.database_path) as conn:
            conn.execute(
                """
                UPDATE leads 
                SET status = 'failed', error_log = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
                """,
                (str(exc), lead_id),
            )
        print(f"[CRAWLER] Error scraping {domain}: {exc}")

    return True


async def run_crawler_daemon(poll_interval: float = 5.0, once: bool = False) -> None:
    settings = get_settings()
    proxies = load_proxies(settings.proxies_file)
    browser_config = BrowserConfig(
        headless=settings.headless,
        user_agent=DEFAULT_DESKTOP_UA,
        verbose=False,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        print("[CRAWLER] Crawler daemon started. Polling queue...")
        while True:
            processed = await process_next_lead(crawler, proxies)
            if once and not processed:
                break
            if not processed:
                await asyncio.sleep(poll_interval)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Autonomous web crawler runner")
    parser.add_argument("--once", action="store_true", help="Process available queue and exit")
    parser.add_argument("--interval", type=float, default=5.0, help="Polling interval in seconds")
    args = parser.parse_args()

    asyncio.run(run_crawler_daemon(poll_interval=args.interval, once=args.once))


if __name__ == "__main__":
    main()
