"""RemoteOK job board scraper.

Uses the public RemoteOK JSON API (no auth required).
Docs: https://remoteok.com/api
"""

from __future__ import annotations

from datetime import UTC, datetime

import requests

from .base import Job
from .utils import save_jobs

REMOTEOK_API = "https://remoteok.com/api"

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _is_relevant(job_raw: dict, keywords: list[str]) -> bool:
    text = " ".join(
        [
            str(job_raw.get("position", "")),
            str(job_raw.get("description", "")),
            " ".join(job_raw.get("tags", []) or []),
            str(job_raw.get("company", "")),
        ]
    ).lower()
    return any(kw in text for kw in keywords)


def _normalise(job_raw: dict) -> Job:
    salary = None
    if job_raw.get("salary_min"):
        salary = f"${job_raw['salary_min']}"
        if job_raw.get("salary_max"):
            salary += f"-{job_raw['salary_max']}"

    return Job(
        source="remoteok",
        id=str(job_raw.get("id", "")),
        title=job_raw.get("position", "Unknown"),
        company=job_raw.get("company", "Unknown"),
        url=job_raw.get("url", ""),
        description=(job_raw.get("description", "") or "")[:2000],
        location=job_raw.get("location", "Remote"),
        salary=salary,
        tags=job_raw.get("tags", []) or [],
        date_posted=str(job_raw.get("date", "")),
        scraped_at=datetime.now(UTC).isoformat(),
    )


def scrape(
    keywords: list[str] | None = None,
    save: bool = True,
) -> list[Job]:
    """Fetch RemoteOK listings, filter, optionally save.

    Args:
        keywords: list of case-insensitive keywords to match. Defaults to a
            sensible security/Python/remote set.
        save: if True, persist results to data/jobs.json (deduped).

    Returns:
        List of relevant Job dicts.
    """
    if keywords is None:
        keywords = [
            "security",
            "cyber",
            "infosec",
            "devsecops",
            "osint",
            "python",
            "typescript",
            "fastapi",
            "react",
            "remote",
            "ics",
            "ot",
            "scada",
            "junior",
            "entry",
            "graduate",
        ]

    try:
        resp = requests.get(
            REMOTEOK_API,
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        print(f"[remoteok] fetch failed: {exc}")
        return []

    if not isinstance(data, list) or len(data) < 2:
        print("[remoteok] unexpected response shape")
        return []

    # First element is API metadata, the rest are listings
    listings = data[1:]
    relevant: list[Job] = []
    for raw in listings:
        if not isinstance(raw, dict) or not raw.get("id"):
            continue
        if not _is_relevant(raw, keywords):
            continue
        relevant.append(_normalise(raw))

    print(f"[remoteok] {len(relevant)} relevant of {len(listings)} total")

    if save and relevant:
        added = save_jobs(relevant)
        print(f"[remoteok] +{added} new persisted")

    return relevant


if __name__ == "__main__":
    scrape()
