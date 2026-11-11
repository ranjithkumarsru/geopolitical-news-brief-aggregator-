import json
from unittest.mock import patch, MagicMock
from src.summarizer import (
    heuristic_summarize,
    summarize_with_gemini
)

def test_heuristic_fallback_critical():
    title = "Full-Scale Military Invasion and Nuclear Threat Announced"
    raw_summary = "Troops advance across borders with high-yield weapons mobilized."
    res = heuristic_summarize(title, raw_summary)
    
    assert res["impact_rating"] == "CRITICAL"
    assert "heuristic_fallback" in res["analyzer"]
    assert len(res["strategic_tags"]) > 0
    assert "Defense & Military" in res["strategic_tags"]

def test_heuristic_fallback_regions_and_tags():
    title = "Diplomats in Kyiv and Moscow Discuss Pipeline Energy Supplies"
    raw_summary = "European gas shipments continue under negotiated monitoring regime."
    res = heuristic_summarize(title, raw_summary)
    
    assert "Eastern Europe" in res["regions_affected"]
    assert "Energy & Resources" in res["strategic_tags"]
    assert len(res["strategic_implications"]) > 0

def test_summarize_with_gemini_fallback_when_no_key():
    res = summarize_with_gemini(
        title="Bilateral Trade Talks in Tokyo",
        raw_summary="Officials discuss bilateral semiconductor tariffs.",
        source="Tokyo News",
        api_key=""
    )
    assert res["impact_rating"] in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
    assert "Indo-Pacific" in res["regions_affected"]

def test_summarize_with_gemini_mocked():
    mock_payload = {
        "headline": "Strategic Straits Accord Formalized",
        "executive_summary": "Maritime security protocol signed to secure international shipping corridors.",
        "impact_rating": "HIGH",
        "impact_justification": "Direct multilateral military cooperation in contested waterways.",
        "regions_affected": ["Middle East", "Indo-Pacific"],
        "strategic_tags": ["Maritime Security", "Diplomacy & Treaties"],
        "strategic_implications": ["Lowered commercial insurance premiums.", "Increased naval patrols."]
    }

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_payload)
    mock_client.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_client):
        res = summarize_with_gemini(
            title="Raw Title",
            raw_summary="Raw Description",
            source="Reuters",
            api_key="mock_test_key_123"
        )

    assert res["impact_rating"] == "HIGH"
    assert res["headline"] == "Strategic Straits Accord Formalized"
    assert "Maritime Security" in res["strategic_tags"]
    assert res["analyzer"] == "gemini"
