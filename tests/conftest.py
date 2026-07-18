"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_remoteok_payload() -> list[dict]:
    """Simulated RemoteOK API response (metadata + 2 listings)."""
    return [
        {"api": "remoteok", "count": 2},
        {
            "id": 12345,
            "company": "Acme Corp",
            "position": "Security Engineer (Remote)",
            "url": "https://remoteok.com/r/12345",
            "description": "We need a Python security engineer for our remote team.",
            "tags": ["python", "security", "remote"],
            "location": "Remote",
            "salary_min": 60000,
            "salary_max": 90000,
            "date": 1700000000,
        },
        {
            "id": 12346,
            "company": "Other Co",
            "position": "Senior Marketing Lead",
            "url": "https://remoteok.com/r/12346",
            "description": "Looking for a marketing expert.",
            "tags": ["marketing"],
            "location": "New York",
            "date": 1700000001,
        },
    ]


@pytest.fixture
def sample_hackernews_thread() -> dict:
    return {
        "objectID": "999",
        "title": "Ask HN: Who is hiring? (January 2026)",
        "created_at_i": 1700000000,
    }


@pytest.fixture
def sample_hackernews_comments() -> list[dict]:
    return [
        {
            "objectID": "1001",
            "comment_text": "Acme Corp | Security Engineer | Remote | Remote | $80k-$120k\n\nWe're hiring a Python security engineer.",
            "created_at_i": 1700000010,
        },
        {
            "objectID": "1002",
            "comment_text": "MarketingPro | Senior Marketing Lead | NYC | Onsite\n\nNeed a senior marketer.",
            "created_at_i": 1700000020,
        },
        {
            "objectID": "1003",
            "comment_text": "",  # empty comment, should be skipped
            "created_at_i": 1700000030,
        },
    ]
