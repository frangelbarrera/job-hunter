"""Tests for the RemoteOK scraper."""

from __future__ import annotations

from unittest.mock import patch

from scrapers import remoteok


def test_normalise_builds_full_job_dict(sample_remoteok_payload):
    raw = sample_remoteok_payload[1]
    job = remoteok._normalise(raw)
    assert job["source"] == "remoteok"
    assert job["id"] == "12345"
    assert job["title"] == "Security Engineer (Remote)"
    assert job["company"] == "Acme Corp"
    assert job["salary"] == "$60000-90000"
    assert "python" in job["tags"]
    assert job["scraped_at"]  # ISO timestamp present


def test_normalise_handles_missing_salary():
    raw = {"id": 1, "position": "X", "company": "Y", "url": "z", "tags": []}
    job = remoteok._normalise(raw)
    assert job["salary"] is None


def test_is_relevant_matches_keywords():
    raw = {"position": "Security Engineer", "description": "", "tags": [], "company": ""}
    assert remoteok._is_relevant(raw, ["security"]) is True


def test_is_relevant_rejects_irrelevant():
    raw = {"position": "Senior Marketing Lead", "description": "", "tags": [], "company": ""}
    assert remoteok._is_relevant(raw, ["security", "python"]) is False


@patch("scrapers.remoteok.requests.get")
@patch("scrapers.remoteok.save_jobs")
def test_scrape_filters_and_returns_relevant(mock_save, mock_get, sample_remoteok_payload):
    mock_get.return_value.json.return_value = sample_remoteok_payload
    mock_get.return_value.raise_for_status.return_value = None

    # Use a narrow keyword set so the marketing listing is filtered out
    jobs = remoteok.scrape(keywords=["security", "python"], save=False)
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Security Engineer (Remote)"


@patch("scrapers.remoteok.requests.get")
def test_scrape_handles_network_error(mock_get):
    mock_get.side_effect = remoteok.requests.RequestException("boom")
    jobs = remoteok.scrape(save=False)
    assert jobs == []


@patch("scrapers.remoteok.requests.get")
def test_scrape_handles_malformed_json(mock_get):
    mock_get.return_value.json.return_value = {"not": "a list"}
    mock_get.return_value.raise_for_status.return_value = None
    jobs = remoteok.scrape(save=False)
    assert jobs == []
