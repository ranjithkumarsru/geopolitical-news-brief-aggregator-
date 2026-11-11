from unittest.mock import patch, MagicMock
from src.pipeline import run_pipeline

def test_pipeline_dry_run(temp_db, sample_rss_xml):
    mock_resp = MagicMock()
    mock_resp.content = sample_rss_xml.encode("utf-8")
    mock_resp.raise_for_status.return_value = None

    test_feeds = [{
        "source": "Mock Wire",
        "url": "https://example.com/mock-rss",
        "category": "Diplomacy"
    }]

    with patch("requests.get", return_value=mock_resp):
        res = run_pipeline(
            feeds=test_feeds,
            max_per_feed=5,
            db_path=temp_db,
            generate_report=False,
            dry_run=True
        )

    assert res["status"] == "dry_run_success"
    assert res["fetched"] == 2
    assert res["deduplicated"] == 2
    assert res["ingested"] == 0

def test_pipeline_e2e_ingestion(temp_db, sample_rss_xml):
    mock_resp = MagicMock()
    mock_resp.content = sample_rss_xml.encode("utf-8")
    mock_resp.raise_for_status.return_value = None

    test_feeds = [{
        "source": "Mock Wire",
        "url": "https://example.com/mock-rss",
        "category": "Diplomacy"
    }]

    with patch("requests.get", return_value=mock_resp):
        res = run_pipeline(
            feeds=test_feeds,
            max_per_feed=5,
            db_path=temp_db,
            generate_report=False,
            dry_run=False
        )

    assert res["status"] == "success"
    assert res["fetched"] == 2
    assert res["ingested"] == 2
    assert res["total_in_db"] == 2
