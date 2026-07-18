"""HackerNews 'Ask HN: Who is hiring?' scraper.

Uses the public HN Algolia search API (no auth required).
A new thread appears on the first business day of each month.
"""

from __future__ import annotations

from datetime import UTC, datetime

import requests

from .base import Job
from .utils import save_jobs

HN_SEARCH = "https://hn.algolia.com/api/v1/search_by_date"

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _get_latest_thread() -> dict | None:
    """Find the most recent 'Ask HN: Who is hiring?' story.

    The HN Algolia search is fuzzy, so we filter results to only stories whose
    title starts with 'Ask HN: Who is hiring' (case-insensitive).
    """
    try:
        resp = requests.get(
            HN_SEARCH,
            params={"tags": "story", "query": "Ask HN: Who is hiring"},
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        resp.raise_for_status()
        stories = resp.json().get("hits", [])
    except (requests.RequestException, ValueError) as exc:
        print(f"[hackernews] story search failed: {exc}")
        return None

    for story in stories:
        title = (story.get("title") or "").lower()
        # Match "Ask HN: Who is hiring? (Month Year)" but reject variants like
        # "Who is hiring freelance developers?" or "Who is hiring remote workers?"
        if title.startswith("ask hn: who is hiring?") or title.startswith("ask hn: who is hiring "):
            # Reject if the title contains words that indicate a non-monthly thread
            if any(word in title for word in ["freelance", "remote worker"]):
                continue
            return story

    return None


def _get_comments(story_id: str) -> list[dict]:
    """Fetch all comments under a story."""
    try:
        resp = requests.get(
            HN_SEARCH,
            params={"tags": f"comment,story_{story_id}", "hitsPerPage": 1000},
            headers={"User-Agent": USER_AGENT},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("hits", [])
    except (requests.RequestException, ValueError) as exc:
        print(f"[hackernews] comments fetch failed: {exc}")
        return []


def _parse_comment(comment: dict) -> Job:
    """Convert an HN comment into a Job dict.

    HN Who's Hiring convention: first line is usually
    `Company | Position | Location | Remote | Salary`.
    """
    text = comment.get("comment_text", "") or ""
    first_line = text.split("\n")[0] if text else "Unknown"
    parts = [p.strip() for p in first_line.split("|")]
    company = parts[0] if parts else "Unknown"
    title = parts[1] if len(parts) > 1 else first_line[:80]

    created_at_i = comment.get("created_at_i", 0)
    date_posted = datetime.fromtimestamp(created_at_i).isoformat() if created_at_i else ""

    return Job(
        source="hackernews",
        id=str(comment.get("objectID", "")),
        title=title[:120],
        company=company[:80],
        url=f"https://news.ycombinator.com/item?id={comment.get('objectID', '')}",
        description=text[:3000],
        location="See post",
        salary=None,
        tags=[],
        date_posted=date_posted,
        scraped_at=datetime.now(UTC).isoformat(),
    )


def _is_relevant(job: Job, keywords: list[str]) -> bool:
    text = f"{job['title']} {job['description']}".lower()
    return any(kw in text for kw in keywords)


def scrape(
    keywords: list[str] | None = None,
    save: bool = True,
) -> list[Job]:
    """Fetch the latest Who's Hiring thread and filter comments.

    Args:
        keywords: case-insensitive keywords to match. Defaults to a
            security/Python/remote set.
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
            "remote",
            "ics",
            "ot",
            "scada",
            "junior",
            "entry",
            "graduate",
        ]

    thread = _get_latest_thread()
    if not thread:
        print("[hackernews] no thread found")
        return []

    print(f"[hackernews] thread: {thread.get('title', '?')} ({thread.get('objectID', '')})")

    comments = _get_comments(thread["objectID"])
    print(f"[hackernews] {len(comments)} comments fetched")

    jobs: list[Job] = []
    for c in comments:
        if not c.get("objectID") or not c.get("comment_text"):
            continue
        job = _parse_comment(c)
        if _is_relevant(job, keywords):
            jobs.append(job)

    print(f"[hackernews] {len(jobs)} relevant of {len(comments)} total")

    if save and jobs:
        added = save_jobs(jobs)
        print(f"[hackernews] +{added} new persisted")

    return jobs


if __name__ == "__main__":
    scrape()
