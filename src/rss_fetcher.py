import re
import html
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import feedparser
import requests
from config import DEFAULT_RSS_FEEDS, MAX_ARTICLES_PER_FEED, REQUEST_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "GeopoliticalNewsAggregator/1.0 (Research Analyst Project; +https://github.com)"
)

# Parameters to strip from URLs to normalize them across syndications
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "at_medium", "at_campaign", "ocid", "cmpid", "feed", "rss", "ref"
}

def clean_html(raw_html: Optional[str]) -> str:
    """Strip HTML tags and unescape HTML entities to produce clean plain text."""
    if not raw_html:
        return ""
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", raw_html)
    # Unescape entities (&amp; -> &, &quot; -> ", etc.)
    cleaned = html.unescape(cleaned)
    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def canonicalize_url(raw_url: str) -> str:
    """
    Standardize URL by lowercasing hostname, removing tracking params, and stripping trailing slashes.
    """
    if not raw_url:
        return ""
    try:
        parsed = urlparse(raw_url.strip())
        query_pairs = parse_qsl(parsed.query, keep_blank_values=False)
        filtered_queries = [
            (k, v) for k, v in query_pairs if k.lower() not in TRACKING_PARAMS
        ]
        # Rebuild query string
        new_query = urlencode(filtered_queries)
        # Strip trailing slash from path if it's not root
        path = parsed.path.rstrip("/") if parsed.path != "/" else parsed.path
        
        canonical = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            parsed.params,
            new_query,
            "" # strip fragment (#)
        ))
        return canonical
    except Exception as e:
        logger.warning(f"Failed to canonicalize URL '{raw_url}': {e}")
        return raw_url.strip()

def parse_published_date(entry: Any) -> str:
    """Parse feed entry timestamp into standard ISO 8601 UTC string."""
    try:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            return dt.isoformat()
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            return dt.isoformat()
    except Exception:
        pass
    return datetime.now(timezone.utc).isoformat()

def fetch_feed_articles(
    feed_config: Dict[str, str],
    max_articles: int = MAX_ARTICLES_PER_FEED,
    timeout: int = REQUEST_TIMEOUT_SECONDS
) -> List[Dict[str, Any]]:
    """
    Fetch articles from a single RSS feed source with timeout and custom headers.
    """
    source_name = feed_config.get("source", "Unknown Source")
    feed_url = feed_config.get("url", "")
    category = feed_config.get("category", "General")

    if not feed_url:
        return []

    articles: List[Dict[str, Any]] = []
    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8"
        }
        response = requests.get(feed_url, headers=headers, timeout=timeout)
        response.raise_for_status()

        parsed_feed = feedparser.parse(response.content)
        if parsed_feed.bozo and not parsed_feed.entries:
            logger.warning(f"Failed to parse XML for {source_name}: {parsed_feed.bozo_exception}")
            return []

        for entry in parsed_feed.entries[:max_articles]:
            raw_title = getattr(entry, "title", "").strip()
            title = clean_html(raw_title)
            raw_link = getattr(entry, "link", "").strip()
            link = canonicalize_url(raw_link)

            if not title or not link:
                continue

            # Extract raw summary or description
            raw_summary = ""
            if hasattr(entry, "summary"):
                raw_summary = entry.summary
            elif hasattr(entry, "description"):
                raw_summary = entry.description
            elif hasattr(entry, "content") and entry.content:
                raw_summary = entry.content[0].value

            cleaned_summary = clean_html(raw_summary)
            published_at = parse_published_date(entry)
            guid = getattr(entry, "id", link)

            articles.append({
                "guid": str(guid),
                "source": source_name,
                "category": category,
                "title": title,
                "link": link,
                "raw_summary": cleaned_summary,
                "published_at": published_at,
            })
            
        logger.info(f"Fetched {len(articles)} articles from {source_name}")
    except Exception as e:
        logger.error(f"Error fetching RSS feed '{source_name}' ({feed_url}): {e}")

    return articles

def fetch_all_feeds(
    feeds: Optional[List[Dict[str, str]]] = None,
    max_articles_per_feed: int = MAX_ARTICLES_PER_FEED
) -> List[Dict[str, Any]]:
    """
    Fetch articles from all configured RSS feeds.
    """
    active_feeds = feeds if feeds is not None else DEFAULT_RSS_FEEDS
    all_articles: List[Dict[str, Any]] = []
    
    for feed in active_feeds:
        articles = fetch_feed_articles(feed, max_articles=max_articles_per_feed)
        all_articles.extend(articles)
        
    return all_articles
