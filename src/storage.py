import sqlite3
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
from config import DB_PATH

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT,
    url TEXT UNIQUE NOT NULL,
    source TEXT NOT NULL,
    category TEXT,
    title TEXT NOT NULL,
    published_at TEXT,
    fetched_at TEXT NOT NULL,
    raw_summary TEXT,
    executive_summary TEXT,
    impact_rating TEXT NOT NULL,
    impact_justification TEXT,
    regions_affected TEXT, -- JSON Array
    strategic_tags TEXT,   -- JSON Array
    strategic_implications TEXT, -- JSON Array
    related_sources TEXT,  -- JSON Array
    analyzer TEXT,
    is_read INTEGER DEFAULT 0,
    is_bookmarked INTEGER DEFAULT 0,
    fingerprint TEXT
);

CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url);
CREATE INDEX IF NOT EXISTS idx_articles_impact ON articles(impact_rating);
CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_bookmarked ON articles(is_bookmarked);
"""

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Optional[str] = None) -> None:
    """Initialize SQLite database with required tables and indexes."""
    with get_connection(db_path) as conn:
        conn.executescript(CREATE_TABLE_SQL)
        conn.commit()
    logger.info("Database schema initialized.")

def insert_article(article_data: Dict[str, Any], db_path: Optional[str] = None) -> Optional[int]:
    """Insert a summarized article into the database. Returns article id or None if duplicate."""
    init_db(db_path)
    
    url = article_data.get("link") or article_data.get("url")
    if not url:
        return None

    fetched_at = datetime.now(timezone.utc).isoformat()
    published_at = article_data.get("published_at") or fetched_at

    regions_json = json.dumps(article_data.get("regions_affected", []))
    tags_json = json.dumps(article_data.get("strategic_tags", []))
    implications_json = json.dumps(article_data.get("strategic_implications", []))
    related_json = json.dumps(article_data.get("related_sources", []))

    sql = """
    INSERT INTO articles (
        guid, url, source, category, title, published_at, fetched_at,
        raw_summary, executive_summary, impact_rating, impact_justification,
        regions_affected, strategic_tags, strategic_implications, related_sources,
        analyzer, fingerprint
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        article_data.get("guid", url),
        url,
        article_data.get("source", "Unknown"),
        article_data.get("category", "General"),
        article_data.get("title", "Untitled"),
        published_at,
        fetched_at,
        article_data.get("raw_summary", ""),
        article_data.get("executive_summary", ""),
        article_data.get("impact_rating", "MEDIUM").upper(),
        article_data.get("impact_justification", ""),
        regions_json,
        tags_json,
        implications_json,
        related_json,
        article_data.get("analyzer", "heuristic_fallback"),
        article_data.get("fingerprint", "")
    )

    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        logger.debug(f"Article with URL '{url}' already exists in database.")
        return None
    except Exception as e:
        logger.error(f"Failed to insert article: {e}")
        return None

def get_existing_urls(db_path: Optional[str] = None) -> Set[str]:
    """Retrieve all existing article URLs to assist in ingestion filtering."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM articles")
        return {row[0] for row in cursor.fetchall()}

def get_existing_titles(limit: int = 1000, db_path: Optional[str] = None) -> List[str]:
    """Retrieve recent article titles to assist in title similarity deduplication."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM articles ORDER BY id DESC LIMIT ?", (limit,))
        return [row[0] for row in cursor.fetchall()]

def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert an SQLite Row object to a clean Python dictionary with unpacked JSON fields."""
    d = dict(row)
    for json_col in ["regions_affected", "strategic_tags", "strategic_implications", "related_sources"]:
        if d.get(json_col):
            try:
                d[json_col] = json.loads(d[json_col])
            except Exception:
                d[json_col] = []
        else:
            d[json_col] = []
    return d

def get_articles(
    impact_filter: Optional[str] = None,
    region_filter: Optional[str] = None,
    tag_filter: Optional[str] = None,
    search_query: Optional[str] = None,
    bookmarked_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieve filtered articles for the dashboard and reports."""
    init_db(db_path)
    conditions = []
    params: List[Any] = []

    if impact_filter and impact_filter != "ALL":
        conditions.append("impact_rating = ?")
        params.append(impact_filter.upper())

    if region_filter and region_filter != "ALL":
        conditions.append("regions_affected LIKE ?")
        params.append(f"%{region_filter}%")

    if tag_filter and tag_filter != "ALL":
        conditions.append("strategic_tags LIKE ?")
        params.append(f"%{tag_filter}%")

    if bookmarked_only:
        conditions.append("is_bookmarked = 1")

    if search_query:
        query_pattern = f"%{search_query.strip()}%"
        conditions.append("(title LIKE ? OR raw_summary LIKE ? OR executive_summary LIKE ?)")
        params.extend([query_pattern, query_pattern, query_pattern])

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    sql = f"""
    SELECT * FROM articles
    {where_clause}
    ORDER BY published_at DESC, id DESC
    LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [row_to_dict(r) for r in rows]

def toggle_bookmark(article_id: int, db_path: Optional[str] = None) -> bool:
    """Toggle bookmark status for an article. Returns new status (True = bookmarked)."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_bookmarked FROM articles WHERE id = ?", (article_id,))
        row = cursor.fetchone()
        if not row:
            return False
        new_val = 0 if row["is_bookmarked"] == 1 else 1
        cursor.execute("UPDATE articles SET is_bookmarked = ? WHERE id = ?", (new_val, article_id))
        conn.commit()
        return bool(new_val)

def toggle_read(article_id: int, db_path: Optional[str] = None) -> bool:
    """Toggle read status for an article."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_read FROM articles WHERE id = ?", (article_id,))
        row = cursor.fetchone()
        if not row:
            return False
        new_val = 0 if row["is_read"] == 1 else 1
        cursor.execute("UPDATE articles SET is_read = ? WHERE id = ?", (new_val, article_id))
        conn.commit()
        return bool(new_val)

def get_analytics_summary(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Compute aggregate analytics for dashboard visualizations."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Total counts
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]

        # By impact
        cursor.execute("SELECT impact_rating, COUNT(*) FROM articles GROUP BY impact_rating")
        impact_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # By source
        cursor.execute("SELECT source, COUNT(*) FROM articles GROUP BY source ORDER BY COUNT(*) DESC LIMIT 8")
        source_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # Unpack tags & regions
        cursor.execute("SELECT regions_affected, strategic_tags FROM articles")
        rows = cursor.fetchall()
        
        region_counts: Dict[str, int] = {}
        tag_counts: Dict[str, int] = {}

        for r in rows:
            try:
                regs = json.loads(r[0]) if r[0] else []
                for reg in regs:
                    region_counts[reg] = region_counts.get(reg, 0) + 1
            except Exception:
                pass
            
            try:
                tgs = json.loads(r[1]) if r[1] else []
                for tg in tgs:
                    tag_counts[tg] = tag_counts.get(tg, 0) + 1
            except Exception:
                pass

        return {
            "total_articles": total_articles,
            "impact_counts": impact_counts,
            "source_counts": source_counts,
            "top_regions": dict(sorted(region_counts.items(), key=lambda x: x[1], reverse=True)[:8]),
            "top_tags": dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:8])
        }
