"""Shared utilities for savers, loaders, and profile access."""

from __future__ import annotations

import json
import os
from pathlib import Path

import yaml

from .base import Job

DEFAULT_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "jobs.json"
DEFAULT_PROFILE_FILE = Path("profile.yaml")
MAX_JOBS_RETAINED = 1000


def save_jobs(jobs: list[Job], data_file: Path | str = DEFAULT_DATA_FILE) -> int:
    """Append new jobs to the JSON store, deduping by (source, id).

    Returns the number of new jobs actually added.
    """
    data_path = Path(data_file)
    data_path.parent.mkdir(parents=True, exist_ok=True)

    existing: list[Job] = []
    if data_path.exists():
        try:
            existing = json.loads(data_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            existing = []

    seen = {(j["source"], j["id"]) for j in existing}
    new_count = 0
    for j in jobs:
        key = (j["source"], j["id"])
        if key in seen:
            continue
        existing.append(j)
        seen.add(key)
        new_count += 1

    # Trim to last N entries to avoid unbounded growth
    if len(existing) > MAX_JOBS_RETAINED:
        existing = existing[-MAX_JOBS_RETAINED:]

    data_path.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return new_count


def load_jobs(data_file: Path | str = DEFAULT_DATA_FILE) -> list[Job]:
    """Load all stored jobs."""
    data_path = Path(data_file)
    if not data_path.exists():
        return []
    try:
        return json.loads(data_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError):
        return []


def load_profile(path: str | None = None) -> dict:
    """Load the user's target profile YAML.

    Resolution order:
        1. Explicit `path` argument
        2. `PROFILE_PATH` env var
        3. `profile.yaml` in cwd
        4. `profile.yaml.example` in repo root (fallback for tests)
    """
    candidates = [
        path,
        os.environ.get("PROFILE_PATH"),
        str(Path.cwd() / "profile.yaml"),
        str(Path(__file__).resolve().parent.parent / "profile.yaml"),
        str(Path(__file__).resolve().parent.parent / "profile.yaml.example"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        p = Path(candidate)
        if p.exists():
            return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    raise FileNotFoundError(
        "No profile.yaml found. Copy profile.yaml.example to profile.yaml and edit it."
    )
