"""Tests for the HackerNews scraper."""

from __future__ import annotations

from unittest.mock import patch

from scrapers import hackernews


def test_parse_comment_extracts_company_and_title(sample_hackernews_comments):
    job = hackernews._parse_comment(sample_hackernews_comments[0])
    assert job["source"] == "hackernews"
    assert job["id"] == "1001"
    assert job["company"] == "Acme Corp"
    assert "Security Engineer" in job["title"]
    assert job["url"].startswith("https://news.ycombinator.com/item?id=")
    assert job["date_posted"]  # ISO timestamp


def test_parse_comment_handles_missing_text():
    job = hackernews._parse_comment({"objectID": "1", "comment_text": ""})
    assert job["title"] == "Unknown"
    assert job["company"] == "Unknown"


def test_is_relevant_matches_security_keywords():
    job = {"title": "Security Engineer", "description": "Python remote role"}
    assert hackernews._is_relevant(job, ["security", "python"]) is True


def test_is_relevant_rejects_marketing_only():
    job = {"title": "Marketing Lead", "description": "Senior NYC onsite"}
    assert hackernews._is_relevant(job, ["security", "python"]) is False


@patch("scrapers.hackernews._get_comments")
@patch("scrapers.hackernews._get_latest_thread")
@patch("scrapers.hackernews.save_jobs")
def test_scrape_filters_comments(
    mock_save, mock_thread, mock_comments, sample_hackernews_thread, sample_hackernews_comments
):
    mock_thread.return_value = sample_hackernews_thread
    mock_comments.return_value = sample_hackernews_comments

    jobs = hackernews.scrape(save=False)
    assert len(jobs) == 1
    assert "Security Engineer" in jobs[0]["title"]


@patch("scrapers.hackernews._get_latest_thread")
def test_scrape_returns_empty_when_no_thread(mock_thread):
    mock_thread.return_value = None
    jobs = hackernews.scrape(save=False)
    assert jobs == []
