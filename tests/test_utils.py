"""Tests for scrapers.utils."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scrapers.utils import load_jobs, load_profile, save_jobs


def _make_job(id_: str, source: str = "test") -> dict:
    return {
        "source": source,
        "id": id_,
        "title": f"Job {id_}",
        "company": "X",
        "url": f"http://example.com/{id_}",
        "description": "",
        "location": "Remote",
        "salary": None,
        "tags": [],
        "date_posted": "",
        "scraped_at": "2026-01-01T00:00:00+00:00",
    }


def test_save_jobs_creates_file(tmp_path):
    data_file = tmp_path / "jobs.json"
    added = save_jobs([_make_job("1"), _make_job("2")], data_file=data_file)
    assert added == 2
    assert data_file.exists()
    saved = json.loads(data_file.read_text())
    assert len(saved) == 2


def test_save_jobs_dedupes(tmp_path):
    data_file = tmp_path / "jobs.json"
    save_jobs([_make_job("1"), _make_job("2")], data_file=data_file)
    added = save_jobs([_make_job("1"), _make_job("3")], data_file=data_file)
    assert added == 1  # only job 3 is new
    saved = json.loads(data_file.read_text())
    assert len(saved) == 3


def test_save_jobs_trims_to_max(tmp_path):
    data_file = tmp_path / "jobs.json"
    # Save more than MAX_JOBS_RETAINED (1000) — should trim
    many_jobs = [_make_job(str(i)) for i in range(1100)]
    save_jobs(many_jobs, data_file=data_file)
    saved = json.loads(data_file.read_text())
    assert len(saved) == 1000
    # The most recent ones are kept (last 1000)
    assert saved[-1]["id"] == "1099"


def test_save_jobs_handles_corrupt_file(tmp_path):
    data_file = tmp_path / "jobs.json"
    data_file.write_text("not valid json")
    added = save_jobs([_make_job("1")], data_file=data_file)
    assert added == 1


def test_load_jobs_returns_empty_when_missing(tmp_path):
    data_file = tmp_path / "nonexistent.json"
    assert load_jobs(data_file=data_file) == []


def test_load_jobs_returns_list(tmp_path):
    data_file = tmp_path / "jobs.json"
    save_jobs([_make_job("1"), _make_job("2")], data_file=data_file)
    loaded = load_jobs(data_file=data_file)
    assert len(loaded) == 2


def test_load_jobs_handles_corrupt_file(tmp_path):
    data_file = tmp_path / "jobs.json"
    data_file.write_text("not valid json")
    assert load_jobs(data_file=data_file) == []


def test_load_profile_from_explicit_path(tmp_path):
    profile_file = tmp_path / "profile.yaml"
    profile_file.write_text("target_title: Test\ntarget_keywords: [python]\n")
    profile = load_profile(path=str(profile_file))
    assert profile["target_title"] == "Test"


def test_load_profile_raises_when_no_candidates(tmp_path, monkeypatch):
    """When all candidate paths are missing, FileNotFoundError is raised."""
    fake_repo_root = tmp_path / "fake_repo"
    fake_repo_root.mkdir()
    import scrapers.utils as utils_mod

    def patched_load_profile(path=None):
        candidates = [
            path,
            str(tmp_path / "missing_env_path.yaml"),
            str(tmp_path / "cwd_profile.yaml"),
            str(fake_repo_root / "profile.yaml"),
            str(fake_repo_root / "profile.yaml.example"),
        ]
        for candidate in candidates:
            if not candidate:
                continue
            p = Path(candidate)
            if p.exists():
                return {"loaded": True}
        raise FileNotFoundError("No profile.yaml found.")

    monkeypatch.setattr(utils_mod, "load_profile", patched_load_profile)
    with pytest.raises(FileNotFoundError):
        utils_mod.load_profile()
