# 🌐 Geopolitical News Brief Aggregator

An automated, intelligence-grade geopolitical news aggregator that fetches feeds from leading international sources, deduplicates cross-outlet reporting, evaluates global strategic impact using **Google Gemini**, and presents actionable intelligence through an interactive **Streamlit dashboard** and daily **Markdown briefings**.

---

## ⚡ Core Capabilities

- **Multilateral RSS Ingestion:** Continuously monitors premier global sources including BBC World, Al Jazeera English, Deutsche Welle (DW), UN News, NPR World, and France 24.
- **Smart Semantic Deduplication:** Combines canonical URL filtering, title normalization, and token overlap similarity algorithms to detect and cluster multi-outlet coverage of identical global events without redundant noise.
- **Gemini Strategic Assessment:** Analyzes developments using Google Gemini (`gemini-2.5-flash`), producing structured intelligence:
  - **Executive Summary:** 2–3 sentence high-level brief.
  - **Geopolitical Impact Rating:** `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW`.
  - **Impact Justification:** Clear explanation of strategic stakes.
  - **Affected Regions:** (e.g., *Middle East*, *Eastern Europe*, *Indo-Pacific*).
  - **Strategic Domain Tags:** (e.g., *Defense & Military*, *Sanctions & Trade*, *Maritime Security*, *Energy & Resources*).
  - **Strategic Implications:** Key watchpoints for intelligence and policy analysts.
- **Zero-Crash Heuristic Fallback:** If `GEMINI_API_KEY` is not configured, the system automatically falls back to an internal heuristic intelligence engine, ensuring offline tests and local development run smoothly.
- **Interactive Streamlit Dashboard (`app.py`):**
  - Real-time search & multi-faceted filtering (Impact, Region, Strategic Domain).
  - One-click RSS ingestion trigger.
  - Interactive charts (Impact level distribution, flashpoint regions, strategic domains).
  - Article bookmarking and direct markdown briefing reader/downloader.
- **Automated GitHub Actions (`daily_brief.yml`):** Runs daily at `06:00 UTC` to test, fetch feeds, perform AI analysis, commit daily markdown reports to `briefs/`, and upload workflow artifacts.
- **Enterprise-Grade Security:** Safe configuration via environment variables with `.env.example` and strict `.gitignore` rules preventing any API key or credential leaks.

---

## 📁 Project Architecture

```
geopolitical-news-brief-aggregator/
├── .github/
│   └── workflows/
│       └── daily_brief.yml       # Daily automated cron job
├── briefs/                       # Generated daily markdown briefings
├── data/                         # SQLite database (geopolitical_news.db)
├── src/
│   ├── __init__.py
│   ├── rss_fetcher.py            # RSS fetching, HTML cleanup, URL canonicalization
│   ├── deduplicator.py           # Multi-source clustering & semantic deduplication
│   ├── summarizer.py             # Gemini API analysis with heuristic fallback
│   ├── storage.py                # SQLite schema, queries, bookmarks, and analytics
│   ├── pipeline.py               # Main CLI ingestion orchestrator
│   └── reporter.py               # Markdown daily briefing report generator
├── tests/
│   ├── test_rss_fetcher.py       # Fetching & URL cleanup tests
│   ├── test_deduplicator.py      # Deduplication & token overlap tests
│   ├── test_summarizer.py        # Gemini & heuristic analyzer tests
│   ├── test_storage.py           # SQLite CRUD & analytics tests
│   └── test_pipeline.py          # End-to-end pipeline execution tests
├── app.py                        # Streamlit interactive dashboard
├── config.py                     # Centralized settings & feed registry
├── requirements.txt              # Dependencies
├── .env.example                  # Environment variable template
├── .gitignore                    # Git exclusions
└── README.md                     # Documentation
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.12)
- Git

### 2. Setup & Virtual Environment

```bash
# Clone the repository (once pushed to your GitHub)
git clone https://github.com/<your-username>/geopolitical-news-brief-aggregator.git
cd geopolitical-news-brief-aggregator

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example configuration file:
```bash
cp .env.example .env
```

Edit `.env` to supply your Google Gemini API Key:
```env
# Obtain from Google AI Studio: https://aistudio.google.com/
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```
*(Note: If `GEMINI_API_KEY` is empty, the application runs using the built-in heuristic analysis engine).*

---

## 💻 Running the Application

### A. Run Ingestion Pipeline via CLI
Fetch the latest feeds, deduplicate, analyze, store in SQLite, and compile today's intelligence brief:

```bash
python -m src.pipeline
```

CLI options:
- `--max-per-feed 10`: Limit articles fetched per RSS feed.
- `--dry-run`: Test fetching and deduplicating without making Gemini API calls or saving to SQLite.
- `--no-report`: Ingest without generating the markdown briefing file.

### B. Launch the Streamlit Dashboard
Start the web dashboard locally:

```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501` to view live intelligence feeds, metrics, and interactive charts.

---

## 🧪 Running Unit Tests

The test suite covers RSS parsing, URL canonicalization, Jaccard/overlap deduplication, Gemini mock calls, SQLite storage operations, and end-to-end pipeline execution:

```bash
pytest -v
```

All tests run without requiring network access or a live Gemini API key.

---

## 🤖 GitHub Actions Daily Workflow

The repository includes `.github/workflows/daily_brief.yml` which executes automatically every day at **06:00 UTC**.

### Setting Up GitHub Repository Secrets:
1. Go to your repository on GitHub.
2. Navigate to **Settings** > **Secrets and variables** > **Actions**.
3. Click **New repository secret**.
4. Name: `GEMINI_API_KEY`
5. Value: Your Gemini API Key from Google AI Studio.
6. Click **Add secret**.

The workflow will run the test suite, fetch fresh news, run Gemini summarization, publish an updated markdown report under `briefs/`, and upload it as a downloadable GitHub Action artifact.

---

## 🛡️ Security & Privacy Notice
- **Never commit `.env` or API keys.** The `.gitignore` file is pre-configured to exclude all environment files, local SQLite databases, and virtual environments.
- API keys are read strictly through environment variables.
