"""Shared types and the scraper protocol every source implements."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol, TypedDict


class Job(TypedDict):
    """Normalised representation of a job posting from any source."""

    source: str
    id: str
    title: str
    company: str
    url: str
    description: str
    location: str
    salary: str | None
    tags: list[str]
    date_posted: str
    scraped_at: str


class Scraper(Protocol):
    """Every scraper module exposes a `scrape()` returning a list of Jobs."""

    def scrape(self) -> list[Job]: ...


def empty_job(source: str, id_: str) -> Job:
    """Helper to build a Job with all required fields defaulted."""
    return Job(
        source=source,
        id=id_,
        title="",
        company="",
        url="",
        description="",
        location="Remote",
        salary=None,
        tags=[],
        date_posted="",
        scraped_at=datetime.now(UTC).isoformat(),
    )
