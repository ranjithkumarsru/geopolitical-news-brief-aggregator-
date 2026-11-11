import os
import json
import logging
import re
from typing import Dict, Any, List, Optional
from config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

# Heuristic Knowledge Base for Offline Fallback & Testing
REGION_KEYWORDS = {
    "Middle East": ["israel", "gaza", "iran", "lebanon", "syria", "yemen", "saudi", "uae", "red sea", "tehran", "beirut", "tel aviv", "iraq"],
    "Eastern Europe": ["ukraine", "russia", "kyiv", "moscow", "poland", "belarus", "baltic", "crimea", "donbas", "nato"],
    "Indo-Pacific": ["china", "taiwan", "beijing", "taipei", "japan", "tokyo", "south korea", "seoul", "north korea", "pyongyang", "south china sea", "philippines", "indo-pacific"],
    "South Asia": ["india", "pakistan", "delhi", "islamabad", "bangladesh", "afghanistan", "kabul"],
    "Europe & EU": ["eu", "european union", "germany", "berlin", "france", "paris", "uk", "london", "brussels", "britain"],
    "North America": ["united states", "u.s.", "usa", "washington", "pentagon", "white house", "canada", "ottawa"],
    "Sub-Saharan Africa": ["sudan", "congo", "drc", "niger", "mali", "kenya", "somalia", "ethiopia", "sahel"],
    "Latin America": ["venezuela", "brazil", "argentina", "colombia", "mexico", "caracas"],
}

DOMAIN_KEYWORDS = {
    "Defense & Military": ["military", "missile", "troop", "weapon", "defense", "arms", "strike", "war", "army", "navy", "air force", "combat"],
    "Sanctions & Trade": ["sanction", "tariff", "trade", "embargo", "export", "import", "wto", "customs", "currency"],
    "Diplomacy & Treaties": ["diplomacy", "envoy", "ambassador", "summit", "treaty", "talks", "ceasefire", "peace", "agreement", "un general assembly"],
    "Energy & Resources": ["oil", "gas", "pipeline", "opec", "energy", "petroleum", "lithium", "uranium", "critical minerals"],
    "Cyber & Espionage": ["cyber", "espionage", "hack", "surveillance", "intelligence", "spy", "telecom"],
    "Maritime Security": ["maritime", "strait", "shipping", "vessel", "carrier", "naval", "blockade", "red sea", "taiwan strait"],
    "Elections & Stability": ["election", "parliament", "protest", "coup", "referendum", "regime", "unrest"]
}

CRITICAL_TERMS = ["nuclear", "declared war", "invasion", "ballistic missile", "martial law", "regime overthrow", "blockade", "full-scale"]
HIGH_TERMS = ["airstrike", "mobilization", "sweeping sanctions", "clash", "escalation", "expulsion", "offensive", "casualt"]
MEDIUM_TERMS = ["bilateral talks", "summit", "warning", "drills", "negotiations", "joint statement", "dispute", "investigation"]

def heuristic_summarize(title: str, raw_summary: str) -> Dict[str, Any]:
    """
    Intelligent heuristic fallback analyzer when Gemini API key is not present or offline.
    Extracts impact rating, regions, tags, and generates clean brief summary.
    """
    full_text = f"{title} {raw_summary}".lower()

    # Determine impact rating
    if any(term in full_text for term in CRITICAL_TERMS):
        impact_rating = "CRITICAL"
        impact_justification = "Direct involvement of high-yield weapons, invasion threats, or acute state-level destabilization."
    elif any(term in full_text for term in HIGH_TERMS):
        impact_rating = "HIGH"
        impact_justification = "Significant regional military action, high-level diplomatic friction, or heavy economic sanctions."
    elif any(term in full_text for term in MEDIUM_TERMS):
        impact_rating = "MEDIUM"
        impact_justification = "Diplomatic posturing, standard military drills, or scheduled high-stakes negotiations."
    else:
        impact_rating = "LOW"
        impact_justification = "Standard bilateral discourse, routine statements, or localized political commentary."

    # Identify affected regions
    regions = []
    for region, keywords in REGION_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(k)}\b", full_text) for k in keywords):
            regions.append(region)
    if not regions:
        regions = ["Global / Multilateral"]

    # Identify strategic domains/tags
    tags = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(k)}\b", full_text) for k in keywords):
            tags.append(domain)
    if not tags:
        tags = ["International Affairs"]

    # Formulate executive summary
    clean_summary = raw_summary.strip() if raw_summary else title
    if len(clean_summary) > 300:
        clean_summary = clean_summary[:297] + "..."
    executive_summary = f"{title}. {clean_summary}"
    if len(executive_summary) > 350:
        executive_summary = executive_summary[:347] + "..."

    implications = [
        f"Potential shifts in policy posture across {', '.join(regions[:2])}.",
        f"Heightened scrutiny in {tags[0]} frameworks.",
        "Monitored for subsequent diplomatic or operational countermeasures."
    ]

    return {
        "headline": title,
        "executive_summary": executive_summary,
        "impact_rating": impact_rating,
        "impact_justification": impact_justification,
        "regions_affected": regions[:4],
        "strategic_tags": tags[:4],
        "strategic_implications": implications,
        "analyzer": "heuristic_fallback"
    }

def summarize_with_gemini(
    title: str,
    raw_summary: str,
    source: str,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Summarize and evaluate geopolitical impact using Google Gemini API.
    Gracefully falls back to heuristic analyzer if key is missing or API errors occur.
    """
    key = (api_key or GEMINI_API_KEY).strip()
    model = (model_name or GEMINI_MODEL).strip()

    if not key:
        logger.info("GEMINI_API_KEY not configured. Using heuristic analyzer fallback.")
        return heuristic_summarize(title, raw_summary)

    prompt = f"""You are a senior geopolitical intelligence analyst. Analyze the following news item:

Source: {source}
Headline: {title}
Article Excerpt: {raw_summary}

Provide a structured strategic briefing in valid JSON format with the following exact keys:
{{
  "headline": "A sharp, clear geopolitical title",
  "executive_summary": "A 2 to 3 sentence concise executive brief highlighting the core development.",
  "impact_rating": "One of: CRITICAL, HIGH, MEDIUM, LOW",
  "impact_justification": "One sentence explaining why this impact rating was assigned.",
  "regions_affected": ["List of countries or geopolitical regions directly affected"],
  "strategic_tags": ["List of strategic domains e.g., Defense & Military, Sanctions & Trade, Diplomacy & Treaties, Energy & Resources, Maritime Security, Cyber & AI, Elections & Stability"],
  "strategic_implications": [
    "Bullet point 1: Immediate diplomatic or operational consequence",
    "Bullet point 2: Medium-term systemic or trade consequence",
    "Bullet point 3: Key watchpoints for analysts"
  ]
}}

Impact Rating Definitions:
- CRITICAL: Active conflict outbreak, nuclear threats, full-scale military invasions, state-collapse emergencies.
- HIGH: Substantial military strikes, heavy cross-border sanctions, alliance realignments, major maritime blockades.
- MEDIUM: Bilateral summits, moderate tariff actions, non-fatal skirmishes, major diplomatic protests.
- LOW: Routine diplomatic rhetoric, bureaucratic changes, ceremonial visits.

Return ONLY the raw JSON object, without backticks or markdown preamble.
"""

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            )
        )

        response_text = response.text.strip()
        # Clean backticks if any
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        parsed = json.loads(response_text.strip())

        # Validate mandatory fields
        required_keys = ["executive_summary", "impact_rating", "regions_affected", "strategic_tags"]
        for rk in required_keys:
            if rk not in parsed:
                raise ValueError(f"Missing required key in Gemini output: {rk}")

        rating = str(parsed.get("impact_rating", "MEDIUM")).upper()
        if rating not in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}:
            rating = "MEDIUM"

        return {
            "headline": parsed.get("headline", title),
            "executive_summary": parsed.get("executive_summary", raw_summary),
            "impact_rating": rating,
            "impact_justification": parsed.get("impact_justification", "Assessed via Gemini strategic model."),
            "regions_affected": parsed.get("regions_affected", ["Global"]),
            "strategic_tags": parsed.get("strategic_tags", ["Geopolitics"]),
            "strategic_implications": parsed.get("strategic_implications", []),
            "analyzer": "gemini"
        }
    except Exception as e:
        logger.warning(f"Gemini API analysis failed ({e}). Falling back to heuristic analyzer.")
        res = heuristic_summarize(title, raw_summary)
        res["analyzer_fallback_reason"] = str(e)
        return res
