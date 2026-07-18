"""Tests for the match scorer."""

from __future__ import annotations

from scripts.match_score import _score, rank

PROFILE = {
    "keywords": ["security", "python", "remote"],
    "stack": ["python", "fastapi"],
    "domains": ["security", "osint"],
    "exclude_keywords": ["senior", "lead"],
    "seniority": "junior",
}


def _job(title, description, **extra):
    base = {
        "source": "test",
        "id": "1",
        "title": title,
        "company": "",
        "url": "",
        "description": description,
        "location": "",
        "salary": None,
        "tags": [],
        "date_posted": "",
        "scraped_at": "",
    }
    base.update(extra)
    return base


def test_score_zero_for_empty_job():
    assert _score(_job("", ""), PROFILE) == 0.0


def test_score_zero_for_whitespace_only_job():
    assert _score(_job("   ", "   "), PROFILE) == 0.0


def test_score_high_for_perfect_match():
    job = _job("Security Engineer", "Python security role, remote, fastapi")
    score = _score(job, PROFILE)
    assert score > 0.5


def test_score_low_for_senior_role_when_targeting_junior():
    job = _job("Senior Security Engineer", "Python, remote")
    score = _score(job, PROFILE)
    assert score < 0.3


def test_score_zero_with_exclude_keyword():
    job = _job("Security Engineer", "python remote senior lead")
    score = _score(job, PROFILE)
    assert score == 0.0


def test_rank_orders_by_score_desc():
    jobs = [
        _job("Marketing Lead", "needs marketing expert"),
        _job("Security Engineer", "python security remote"),
        _job("Junior Dev", "python"),
    ]
    ranked = rank(jobs, PROFILE)
    assert ranked[0][1] >= ranked[1][1] >= ranked[2][1]
    assert "Security Engineer" in ranked[0][0]["title"]
