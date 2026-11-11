import pytest
import tempfile
from pathlib import Path
from src.storage import init_db

SAMPLE_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Sample Geopolitical News</title>
    <link>https://example.com/world</link>
    <description>Global strategic updates</description>
    <item>
      <title>Diplomats Meet in Geneva Over Maritime Security Dispute</title>
      <link>https://example.com/articles/geneva-talks?utm_source=feed&amp;utm_medium=rss</link>
      <description>&lt;p&gt;Envoys from multiple nations met today in &lt;b&gt;Geneva&lt;/b&gt; to discuss escalating naval tensions in the Red Sea.&lt;/p&gt;</description>
      <pubDate>Mon, 10 Nov 2026 12:00:00 GMT</pubDate>
      <guid>https://example.com/articles/geneva-talks</guid>
    </item>
    <item>
      <title>Sanctions Imposed on High-Tech Semiconductor Exports</title>
      <link>https://example.com/articles/tech-sanctions</link>
      <description>New multilateral export controls restrict advanced microchips and dual-use components.</description>
      <pubDate>Mon, 10 Nov 2026 14:30:00 GMT</pubDate>
      <guid>https://example.com/articles/tech-sanctions</guid>
    </item>
  </channel>
</rss>
"""

@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name
    init_db(temp_path)
    yield temp_path
    try:
        Path(temp_path).unlink(missing_ok=True)
    except Exception:
        pass

@pytest.fixture
def sample_rss_xml():
    return SAMPLE_RSS_XML
