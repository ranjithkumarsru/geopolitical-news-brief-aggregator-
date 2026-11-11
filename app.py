import streamlit as st
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import GEMINI_API_KEY, GEMINI_MODEL, DB_PATH, DEFAULT_RSS_FEEDS, BRIEFS_DIR
from src.storage import (
    init_db,
    get_articles,
    get_analytics_summary,
    toggle_bookmark,
    toggle_read
)
from src.pipeline import run_pipeline
from src.reporter import generate_daily_brief_markdown

st.set_page_config(
    page_title="Geopolitical Intelligence Brief Aggregator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Analyst Dashboard
st.markdown("""
<style>
    .metric-card {
        background-color: #1e293b;
        color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
    }
    .badge-critical {
        background-color: #ef4444;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .badge-high {
        background-color: #f97316;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .badge-medium {
        background-color: #3b82f6;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .badge-low {
        background-color: #10b981;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .tag-badge {
        background-color: #334155;
        color: #e2e8f0;
        padding: 2px 7px;
        border-radius: 3px;
        font-size: 0.75rem;
        margin-right: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize DB
init_db()

# --- SIDEBAR CONTROLS ---
st.sidebar.title("🌐 Geopolitical Intel")
st.sidebar.caption("Automated News Aggregation & Strategic Analysis")

# API Status Badge
if GEMINI_API_KEY:
    st.sidebar.success(f"🟢 Gemini Active (`{GEMINI_MODEL}`)")
else:
    st.sidebar.warning("🟡 Heuristic Fallback Active\n(Set `GEMINI_API_KEY` in `.env` to enable Gemini)")

st.sidebar.markdown("---")

# Refresh / Ingestion button
st.sidebar.subheader("📡 Feed Ingestion")
col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    if st.button("🔄 Fetch News", use_container_width=True):
        with st.spinner("Fetching RSS feeds and analyzing developments..."):
            res = run_pipeline(max_per_feed=5, generate_report=True)
            st.sidebar.success(f"Ingested {res['ingested']} new items!")
            st.rerun()

with col_btn2:
    if st.button("📑 Gen Brief", use_container_width=True):
        with st.spinner("Compiling daily intelligence report..."):
            generate_daily_brief_markdown()
            st.sidebar.success("Brief generated!")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filters")

# Filter Controls
search_query = st.sidebar.text_input("Search Intel", placeholder="Keywords, leaders, weapons...")

impact_choice = st.sidebar.selectbox(
    "Impact Rating",
    ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"]
)

# Region filter
available_regions = [
    "ALL", "Middle East", "Eastern Europe", "Indo-Pacific", "South Asia",
    "Europe & EU", "North America", "Sub-Saharan Africa", "Latin America", "Global / Multilateral"
]
region_choice = st.sidebar.selectbox("Region", available_regions)

# Domain / Tag filter
available_tags = [
    "ALL", "Defense & Military", "Sanctions & Trade", "Diplomacy & Treaties",
    "Energy & Resources", "Cyber & Espionage", "Maritime Security", "Elections & Stability"
]
tag_choice = st.sidebar.selectbox("Strategic Domain", available_tags)

bookmarked_only = st.sidebar.checkbox("⭐ Bookmarked Only", value=False)

# --- MAIN CONTENT ---
st.title("🌐 Geopolitical News Brief Aggregator")
st.markdown("Real-time strategic news collection, deduplication, and automated AI impact assessment.")

# Top Metrics Bar
analytics = get_analytics_summary()
impact_counts = analytics.get("impact_counts", {})
total_events = analytics.get("total_articles", 0)
crit_count = impact_counts.get("CRITICAL", 0)
high_count = impact_counts.get("HIGH", 0)
med_count = impact_counts.get("MEDIUM", 0)

m_col1, m_col2, m_col3, m_col4 = st.columns(4)
m_col1.metric("Total Events", total_events)
m_col2.metric("🚨 Critical Alerts", crit_count)
m_col3.metric("⚠️ High Impact", high_count)
m_col4.metric("ℹ️ Medium Impact", med_count)

st.markdown("---")

# Navigation Tabs
tab_feed, tab_analytics, tab_brief, tab_config = st.tabs([
    "📰 Strategic Intel Feed",
    "📊 Global Analytics",
    "📑 Daily Briefing Report",
    "⚙️ Source Feeds & Setup"
])

# TAB 1: STRATEGIC INTEL FEED
with tab_feed:
    articles = get_articles(
        impact_filter=impact_choice,
        region_filter=region_choice,
        tag_filter=tag_choice,
        search_query=search_query,
        bookmarked_only=bookmarked_only,
        limit=50
    )

    if not articles:
        st.info("No geopolitical events match the current filter criteria. Click **'Fetch News'** in the sidebar to ingest latest updates.")
    else:
        st.write(f"Showing **{len(articles)}** strategic intelligence items:")

        for art in articles:
            rating = art.get("impact_rating", "MEDIUM")
            badge_class = f"badge-{rating.lower()}"
            
            with st.container():
                col_header, col_bm = st.columns([0.88, 0.12])
                with col_header:
                    badge_html = f"<span class='{badge_class}'>{rating}</span>"
                    st.markdown(f"### {badge_html} {art['title']}", unsafe_allow_html=True)
                    st.caption(f"**Source:** {art['source']} | **Category:** {art.get('category', 'Global')} | **Published:** {art['published_at']} | **Analyzer:** `{art.get('analyzer', 'system')}`")
                
                with col_bm:
                    bm_label = "⭐ Saved" if art.get("is_bookmarked") else "☆ Save"
                    if st.button(bm_label, key=f"bm_{art['id']}"):
                        toggle_bookmark(art["id"])
                        st.rerun()

                # Executive Summary Box
                st.info(f"**Executive Summary:** {art['executive_summary']}")

                # Tags & Regions
                regions = art.get("regions_affected", [])
                tags = art.get("strategic_tags", [])
                
                tag_badges = "".join([f"<span class='tag-badge'>🏷️ {t}</span>" for t in tags])
                region_badges = "".join([f"<span class='tag-badge'>🌍 {r}</span>" for r in regions])
                st.markdown(f"{region_badges} {tag_badges}", unsafe_allow_html=True)

                if art.get("impact_justification"):
                    st.markdown(f"**Impact Justification:** *{art['impact_justification']}*")

                # Implications Expandable
                implications = art.get("strategic_implications", [])
                if implications:
                    with st.expander("🔍 Strategic Implications & Analyst Watchpoints"):
                        for imp in implications:
                            st.markdown(f"- {imp}")
                        
                        related = art.get("related_sources", [])
                        if related:
                            st.markdown("**Cross-Source Coverage:**")
                            for r in related:
                                st.markdown(f"- [{r.get('source')}]({r.get('link')}): {r.get('title')}")

                st.markdown(f"[🔗 Read Original Source Article]({art['url']})")
                st.markdown("---")

# TAB 2: GLOBAL ANALYTICS
with tab_analytics:
    st.subheader("Global Geopolitical Impact Breakdown")
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.write("#### Events by Impact Level")
        if impact_counts:
            st.bar_chart(impact_counts)
        else:
            st.caption("No data recorded yet.")

    with col_chart2:
        st.write("#### Top Flashpoint Regions")
        top_regions = analytics.get("top_regions", {})
        if top_regions:
            st.bar_chart(top_regions)
        else:
            st.caption("No data recorded yet.")

    col_chart3, col_chart4 = st.columns(2)
    with col_chart3:
        st.write("#### Active Strategic Domains")
        top_tags = analytics.get("top_tags", {})
        if top_tags:
            st.bar_chart(top_tags)
        else:
            st.caption("No data recorded yet.")

    with col_chart4:
        st.write("#### Coverage by News Organization")
        source_counts = analytics.get("source_counts", {})
        if source_counts:
            st.bar_chart(source_counts)
        else:
            st.caption("No data recorded yet.")

# TAB 3: DAILY BRIEFING REPORT
with tab_brief:
    st.subheader("Executive Markdown Briefings")
    
    brief_files = sorted(list(BRIEFS_DIR.glob("*-geopolitical-brief.md")), reverse=True)
    if not brief_files:
        st.info("No briefings generated yet. Click **'Gen Brief'** in the sidebar to generate today's briefing.")
    else:
        selected_file = st.selectbox("Select Briefing Date", [f.name for f in brief_files])
        if selected_file:
            brief_path = BRIEFS_DIR / selected_file
            with open(brief_path, "r", encoding="utf-8") as f:
                brief_content = f.read()

            st.download_button(
                label="📥 Download Markdown Brief",
                data=brief_content,
                file_name=selected_file,
                mime="text/markdown"
            )
            st.markdown(brief_content)

# TAB 4: FEEDS & SETUP
with tab_config:
    st.subheader("Configured Geopolitical Intelligence Feeds")
    st.table(DEFAULT_RSS_FEEDS)

    st.subheader("Environment & API Configuration")
    st.markdown("""
    **Environment Variables:**
    - `GEMINI_API_KEY`: Google Gemini API Key. If unset, heuristic fallback analysis is used.
    - `GEMINI_MODEL`: Model identifier (Default: `gemini-2.5-flash`).
    - `DATABASE_PATH`: Custom SQLite database path (Default: `data/geopolitical_news.db`).
    - `DEDUPLICATION_THRESHOLD`: Jaccard token similarity cutoff (Default: `0.72`).
    - `MAX_ARTICLES_PER_FEED`: Max articles per RSS feed per run (Default: `15`).

    **Safe Secret Handling:**
    - Never commit `.env` or API keys to GitHub.
    - Add `GEMINI_API_KEY` to your repository's GitHub Actions Secrets (`Settings -> Secrets and variables -> Actions`).
    """)
