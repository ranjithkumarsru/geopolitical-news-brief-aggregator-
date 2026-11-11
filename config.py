import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
BRIEFS_DIR = BASE_DIR / "briefs"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
BRIEFS_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

# Database Configuration
DEFAULT_DB_PATH = str(DATA_DIR / "geopolitical_news.db")
DB_PATH = os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)

# Deduplication Configuration
# Jaccard title token similarity threshold (0.0 to 1.0)
SIMILARITY_THRESHOLD = float(os.getenv("DEDUPLICATION_THRESHOLD", "0.72"))

# Ingestion Settings
MAX_ARTICLES_PER_FEED = int(os.getenv("MAX_ARTICLES_PER_FEED", "15"))
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "12"))

# Curated Geopolitical News Feeds (Reliable, high-impact international outlets)
DEFAULT_RSS_FEEDS = [
    {
        "source": "BBC News - World",
        "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "category": "Global Politics"
    },
    {
        "source": "Al Jazeera English",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "category": "International & Middle East"
    },
    {
        "source": "Deutsche Welle (DW) - World",
        "url": "https://rss.dw.com/rdf/rss-en-world",
        "category": "European & Global Affairs"
    },
    {
        "source": "UN News",
        "url": "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
        "category": "Multilateral Diplomacy"
    },
    {
        "source": "NPR World",
        "url": "https://feeds.npr.org/1004/rss.xml",
        "category": "World Affairs"
    },
    {
        "source": "France 24 World",
        "url": "https://www.france24.com/en/rss",
        "category": "International Security"
    }
]
