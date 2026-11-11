from src.storage import (
    init_db,
    insert_article,
    get_articles,
    get_existing_urls,
    get_existing_titles,
    toggle_bookmark,
    toggle_read,
    get_analytics_summary
)

def test_storage_crud(temp_db):
    article1 = {
        "guid": "guid-1",
        "url": "https://example.com/art1",
        "source": "Global Post",
        "category": "Diplomacy",
        "title": "Summit Concludes in Vienna",
        "published_at": "2026-11-10T10:00:00Z",
        "raw_summary": "Envoys agreed on monitoring frameworks.",
        "executive_summary": "Vienna summit yielded technical protocols on verification.",
        "impact_rating": "MEDIUM",
        "impact_justification": "Diplomatic dialogue without immediate binding treaties.",
        "regions_affected": ["Europe & EU", "Middle East"],
        "strategic_tags": ["Diplomacy & Treaties"],
        "strategic_implications": ["Follow-up talks in 30 days."],
        "related_sources": [],
        "analyzer": "heuristic_fallback"
    }

    article2 = {
        "guid": "guid-2",
        "url": "https://example.com/art2",
        "source": "Defense Daily",
        "category": "Military",
        "title": "Air Defense Maneuvers Over Baltic Border",
        "published_at": "2026-11-10T12:00:00Z",
        "raw_summary": "Fighter jets scramble in response to unannounced patrol.",
        "executive_summary": "Airspace confrontation triggers joint alert protocols.",
        "impact_rating": "HIGH",
        "impact_justification": "Direct military interception risk.",
        "regions_affected": ["Eastern Europe"],
        "strategic_tags": ["Defense & Military"],
        "strategic_implications": ["Heightened readiness levels across Baltic airbases."],
        "related_sources": [],
        "analyzer": "gemini"
    }

    # Insert
    id1 = insert_article(article1, db_path=temp_db)
    id2 = insert_article(article2, db_path=temp_db)
    assert id1 is not None
    assert id2 is not None

    # Duplicate URL insertion should return None
    dup_id = insert_article(article1, db_path=temp_db)
    assert dup_id is None

    # Verify existing URLs & Titles
    urls = get_existing_urls(temp_db)
    assert "https://example.com/art1" in urls
    assert "https://example.com/art2" in urls

    titles = get_existing_titles(limit=10, db_path=temp_db)
    assert len(titles) == 2

    # Query with filters
    all_arts = get_articles(db_path=temp_db)
    assert len(all_arts) == 2

    high_arts = get_articles(impact_filter="HIGH", db_path=temp_db)
    assert len(high_arts) == 1
    assert high_arts[0]["title"] == "Air Defense Maneuvers Over Baltic Border"

    baltic_arts = get_articles(region_filter="Eastern Europe", db_path=temp_db)
    assert len(baltic_arts) == 1

    search_arts = get_articles(search_query="Vienna", db_path=temp_db)
    assert len(search_arts) == 1

    # Bookmarking
    assert toggle_bookmark(id1, db_path=temp_db) is True
    bm_arts = get_articles(bookmarked_only=True, db_path=temp_db)
    assert len(bm_arts) == 1
    assert bm_arts[0]["id"] == id1

    # Analytics summary
    stats = get_analytics_summary(db_path=temp_db)
    assert stats["total_articles"] == 2
    assert stats["impact_counts"]["HIGH"] == 1
    assert stats["impact_counts"]["MEDIUM"] == 1
    assert "Eastern Europe" in stats["top_regions"]
