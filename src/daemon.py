import time
import logging
import sys
import argparse
from datetime import datetime
from src.pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [daemon]: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("daemon")

def start_daemon(interval_minutes: int = 60, max_per_feed: int = 5):
    """
    Continuous background service that periodically pulls RSS feeds,
    deduplicates, runs strategic analysis, updates SQLite, and compiles daily reports.
    """
    logger.info(f"Geopolitical News Background Daemon started. Checking feeds every {interval_minutes} minutes.")
    
    while True:
        try:
            logger.info("Executing periodic background news aggregation cycle...")
            res = run_pipeline(max_per_feed=max_per_feed, generate_report=True)
            logger.info(
                f"Cycle completed. Ingested: {res.get('ingested', 0)} new items "
                f"({res.get('critical_count', 0)} Critical, {res.get('high_count', 0)} High). "
                f"Total in Database: {res.get('total_in_db', 0)}."
            )
        except Exception as e:
            logger.error(f"Error during background ingestion: {e}", exc_info=True)

        logger.info(f"Cycle finished. Next check in {interval_minutes} minutes...")
        time.sleep(interval_minutes * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Geopolitical News Background Ingestion Daemon")
    parser.add_argument("--interval", type=int, default=60, help="Interval between runs in minutes (default: 60)")
    parser.add_argument("--max-per-feed", type=int, default=5, help="Max articles per feed per cycle")
    args = parser.parse_args()

    start_daemon(interval_minutes=args.interval, max_per_feed=args.max_per_feed)
