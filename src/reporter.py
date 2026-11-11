import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import BRIEFS_DIR
from src.storage import get_articles, get_analytics_summary

def generate_daily_brief_markdown(
    target_date: Optional[str] = None,
    db_path: Optional[str] = None,
    output_dir: Optional[Path] = None
) -> str:
    """
    Generate an executive-level Geopolitical Daily Brief in Markdown format.
    Saves the report to output_dir and returns the file path.
    """
    now = datetime.now(timezone.utc)
    date_str = target_date or now.strftime("%Y-%m-%d")
    out_dir = output_dir or BRIEFS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    file_path = out_dir / f"{date_str}-geopolitical-brief.md"

    # Fetch articles
    all_articles = get_articles(limit=100, db_path=db_path)
    analytics = get_analytics_summary(db_path=db_path)

    critical_articles = [a for a in all_articles if a.get("impact_rating") == "CRITICAL"]
    high_articles = [a for a in all_articles if a.get("impact_rating") == "HIGH"]
    medium_articles = [a for a in all_articles if a.get("impact_rating") == "MEDIUM"]
    low_articles = [a for a in all_articles if a.get("impact_rating") == "LOW"]

    md_lines: List[str] = []
    md_lines.append(f"# 🌐 Executive Geopolitical Intelligence Briefing")
    md_lines.append(f"**Date:** {date_str} | **Generated at:** {now.strftime('%H:%M:%S UTC')}")
    md_lines.append(f"**Coverage:** {analytics.get('total_articles', 0)} total analyzed events across multilateral sources.\n")

    # Metrics Summary Box
    md_lines.append("## 📊 Strategic Risk Dashboard")
    md_lines.append("| Metric | Count |")
    md_lines.append("| :--- | :--- |")
    md_lines.append(f"| 🚨 **Critical Impact Events** | **{len(critical_articles)}** |")
    md_lines.append(f"| ⚠️ **High Impact Events** | **{len(high_articles)}** |")
    md_lines.append(f"| ℹ️ **Medium Impact Events** | **{len(medium_articles)}** |")
    md_lines.append(f"| 🌐 **Low / Routine Diplomatic Events** | **{len(low_articles)}** |")
    md_lines.append(f"| 📰 **Total Active Monitored Items** | **{len(all_articles)}** |\n")

    # Top Regions & Strategic Tags
    top_regions = analytics.get("top_regions", {})
    if top_regions:
        md_lines.append("### Active Flashpoint Regions")
        md_lines.append(", ".join([f"`{r} ({c})`" for r, c in top_regions.items()]) + "\n")

    # Critical & High Alerts Section
    md_lines.append("---")
    md_lines.append("## 🚨 Priority Flashpoints (Critical & High Impact)")
    
    priority_list = critical_articles + high_articles
    if not priority_list:
        md_lines.append("_No critical or high-level military/geopolitical alerts detected in this briefing window._\n")
    else:
        for idx, art in enumerate(priority_list, 1):
            badge = "🚨 CRITICAL" if art["impact_rating"] == "CRITICAL" else "⚠️ HIGH"
            md_lines.append(f"### {idx}. [{badge}] {art['title']}")
            md_lines.append(f"**Source:** {art['source']} | **Published:** {art['published_at']} | **Analyzer:** `{art.get('analyzer', 'system')}`")
            
            regions = ", ".join(art.get("regions_affected", [])) or "Global"
            tags = ", ".join([f"`{t}`" for t in art.get("strategic_tags", [])]) or "`Geopolitics`"
            md_lines.append(f"**Regions:** {regions} | **Domains:** {tags}\n")

            md_lines.append(f"> **Executive Summary:** {art['executive_summary']}\n")
            if art.get("impact_justification"):
                md_lines.append(f"**Impact Justification:** *{art['impact_justification']}*\n")

            implications = art.get("strategic_implications", [])
            if implications:
                md_lines.append("**Key Strategic Implications:**")
                for imp in implications:
                    md_lines.append(f"- {imp}")
                md_lines.append("")

            md_lines.append(f"🔗 [Read Primary Source Document]({art['url']})")
            
            related = art.get("related_sources", [])
            if related:
                md_lines.append("↳ **Corroborating Outlets:** " + ", ".join([f"[{r['source']}]({r['link']})" for r in related]))
            md_lines.append("")

    # Medium Level Developments
    md_lines.append("---")
    md_lines.append("## 🌐 Diplomatic & Strategic Developments (Medium Impact)")
    if not medium_articles:
        md_lines.append("_No medium-impact diplomatic briefs recorded._\n")
    else:
        for idx, art in enumerate(medium_articles[:10], 1):
            md_lines.append(f"#### {idx}. {art['title']}")
            md_lines.append(f"*{art['source']}* — {art['executive_summary']} ([Source]({art['url']}))\n")

    # Low / Routine Developments
    if low_articles:
        md_lines.append("---")
        md_lines.append("## 📋 Regional & Routine Diplomatic Coverage (Low Impact)")
        for idx, art in enumerate(low_articles[:10], 1):
            md_lines.append(f"- **{art['title']}** (*{art['source']}*) — {art['executive_summary'][:150]}... [Link]({art['url']})")
        md_lines.append("")

    # Footer
    md_lines.append("---")
    md_lines.append("Generated by **Geopolitical News Brief Aggregator** | Powered by Google Gemini & Python")

    content = "\n".join(md_lines)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return str(file_path)
