import argparse
import logging
import sys
import time
from typing import Dict, Any, List, Optional
from config import (
    DEFAULT_RSS_FEEDS,
    MAX_ARTICLES_PER_FEED,
    SIMILARITY_THRESHOLD,
    DB_PATH,
    GEMINI_API_KEY
)
from src.rss_fetcher import fetch_all_feeds
from src.deduplicator import deduplicate_articles
from src.summarizer import summarize_with_gemini
from src.storage import (
    init_db,
    insert_article,
    get_existing_urls,
    get_existing_titles,
    get_analytics_summary
)
from src.reporter import generate_daily_brief_markdown

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("pipeline")

def run_pipeline(
    feeds: Optional[List[Dict[str, str]]] = None,
    max_per_feed: int = MAX_ARTICLES_PER_FEED,
    threshold: float = SIMILARITY_THRESHOLD,
    db_path: Optional[str] = None,
    generate_report: bool = True,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Execute full ingestion pipeline:
    Fetch -> Deduplicate -> Gemini Summarize & Tag -> Store -> Report
    """
    target_db = db_path or DB_PATH
    logger.info("Starting Geopolitical Intelligence Ingestion Pipeline...")
    init_db(target_db)

    # 1. Fetch
    logger.info("Step 1: Fetching articles from RSS feeds...")
    raw_articles = fetch_all_feeds(feeds=feeds, max_articles_per_feed=max_per_feed)
    logger.info(f"Total raw items fetched: {len(raw_articles)}")

    if not raw_articles:
        logger.warning("No articles fetched from RSS feeds.")
        return {"status": "empty", "fetched": 0, "ingested": 0}

    # 2. Existing items check
    existing_urls = get_existing_urls(target_db)
    existing_titles = get_existing_titles(limit=1000, db_path=target_db)
    logger.info(f"Existing database baseline: {len(existing_urls)} URLs, {len(existing_titles)} titles.")

    # 3. Deduplicate
    logger.info("Step 2: Executing deduplication and semantic clustering...")
    unique_articles = deduplicate_articles(
        articles=raw_articles,
        existing_urls=existing_urls,
        existing_titles=existing_titles,
        threshold=threshold
    )
    logger.info(f"Articles remaining after deduplication: {len(unique_articles)}")

    if dry_run:
        logger.info("[Dry Run] Skipping AI summarization and database commits.")
        return {
            "status": "dry_run_success",
            "fetched": len(raw_articles),
            "deduplicated": len(unique_articles),
            "ingested": 0
        }

    # 4. Summarize and Store
    ingested_count = 0
    critical_count = 0
    high_count = 0

    if not GEMINI_API_KEY:
        logger.warning("Notice: GEMINI_API_KEY is not set. Pipeline will use heuristic intelligence analyzer.")

    logger.info("Step 3: Running Strategic Summarization and Impact Assessment...")
    for idx, art in enumerate(unique_articles, 1):
        title = art.get("title", "")
        summary_raw = art.get("raw_summary", "")
        source = art.get("source", "Unknown")

        logger.info(f"[{idx}/{len(unique_articles)}] Analyzing: {title[:60]}...")
        
        # Analyze with Gemini / fallback
        analysis = summarize_with_gemini(
            title=title,
            raw_summary=summary_raw,
            source=source
        )

        # Merge analysis into article
        art.update(analysis)

        # Track impact
        if art.get("impact_rating") == "CRITICAL":
            critical_count += 1
        elif art.get("impact_rating") == "HIGH":
            high_count += 1

        # Save to database
        saved_id = insert_article(art, db_path=target_db)
        if saved_id:
            ingested_count += 1

        # Gentle pause to avoid potential rate-limit spikes
        time.sleep(0.1)

    logger.info(f"Step 4: Successfully ingested {ingested_count} new analyzed articles ({critical_count} CRITICAL, {high_count} HIGH).")

    # 5. Generate Daily Brief Report
    report_path = None
    if generate_report:
        logger.info("Step 5: Generating Daily Markdown Intelligence Brief...")
        report_path = generate_daily_brief_markdown(db_path=target_db)
        logger.info(f"Report generated: {report_path}")

    analytics = get_analytics_summary(db_path=target_db)
    
    return {
        "status": "success",
        "fetched": len(raw_articles),
        "deduplicated": len(unique_articles),
        "ingested": ingested_count,
        "critical_count": critical_count,
        "high_count": high_count,
        "report_path": report_path,
        "total_in_db": analytics.get("total_articles", 0)
    }

def main():
    parser = argparse.ArgumentParser(description="Geopolitical News Brief Aggregator CLI")
    parser.add_argument("--max-per-feed", type=int, default=MAX_ARTICLES_PER_FEED, help="Maximum articles to fetch per feed")
    parser.add_argument("--threshold", type=float, default=SIMILARITY_THRESHOLD, help="Deduplication similarity threshold (0-1)")
    parser.add_argument("--db-path", type=str, default=None, help="Custom SQLite database path")
    parser.add_argument("--no-report", action="store_true", help="Disable automatic markdown report generation")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and deduplicate without summarizing or writing to DB")
    args = parser.parse_args()

    result = run_pipeline(
        max_per_feed=args.max_per_feed,
        threshold=args.threshold,
        db_path=args.db_path,
        generate_report=not args.no_report,
        dry_run=args.dry_run
    )
    print("\n--- Pipeline Execution Summary ---")
    for k, v in result.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
