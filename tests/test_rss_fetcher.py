import pytest
from unittest.mock import patch, MagicMock
from src.rss_fetcher import clean_html, canonicalize_url, fetch_feed_articles

def test_clean_html():
    raw = "<p>Tensions rise in <b>Eastern Europe</b> &amp; surrounding borders.<br/></p>"
    cleaned = clean_html(raw)
    assert cleaned == "Tensions rise in Eastern Europe & surrounding borders."
    assert clean_html(None) == ""

def test_canonicalize_url():
    raw_url = "https://WWW.EXAMPLE.COM/news/article-123/?utm_source=twitter&utm_medium=feed&ref=banner#comments"
    canonical = canonicalize_url(raw_url)
    assert canonical == "https://www.example.com/news/article-123"
    assert "utm_source" not in canonical
    assert "comments" not in canonical

def test_fetch_feed_articles_mock(sample_rss_xml):
    mock_resp = MagicMock()
    mock_resp.content = sample_rss_xml.encode("utf-8")
    mock_resp.raise_for_status.return_value = None

    feed_cfg = {
        "source": "Sample News",
        "url": "https://example.com/rss",
        "category": "Diplomacy"
    }

    with patch("requests.get", return_value=mock_resp):
        articles = fetch_feed_articles(feed_cfg)

    assert len(articles) == 2
    first = articles[0]
    assert first["source"] == "Sample News"
    assert first["title"] == "Diplomats Meet in Geneva Over Maritime Security Dispute"
    assert "Geneva" in first["raw_summary"]
    # Verify tracking params stripped
    assert "utm_source" not in first["link"]
