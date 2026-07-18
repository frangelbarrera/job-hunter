"""Score scraped jobs against the user's profile and rank the best matches."""

from __future__ import annotations

import json
import sys

from scrapers.base import Job
from scrapers.utils import DEFAULT_DATA_FILE, load_jobs, load_profile

RANKED_OUTPUT = DEFAULT_DATA_FILE.parent / "ranked_jobs.json"


def _text_of(job: Job) -> str:
    return " ".join(
        [
            job.get("title", ""),
            job.get("company", ""),
            job.get("description", ""),
            " ".join(job.get("tags", [])),
            job.get("location", ""),
        ]
    ).lower()


def _score(job: Job, profile: dict) -> float:
    """Compute a 0-1 match score for a job against a profile.

    Weighting:
        40% keyword hits (normalised)
        25% stack hits
        20% domain hits
        15% seniority alignment
    Negative: exclude_keywords drop the score by 0.5 each (floored at 0).
    """
    text = _text_of(job)
    if not text.strip():
        return 0.0

    keywords = [k.lower() for k in profile.get("keywords", [])]
    stack = [s.lower() for s in profile.get("stack", [])]
    domains = [d.lower() for d in profile.get("domains", [])]
    excludes = [e.lower() for e in profile.get("exclude_keywords", [])]
    seniority = profile.get("seniority", "junior").lower()

    kw_hits = sum(1 for k in keywords if k in text)
    stack_hits = sum(1 for s in stack if s in text)
    domain_hits = sum(1 for d in domains if d in text)
    exclude_hits = sum(1 for e in excludes if e in text)

    denom = max(len(keywords), 1)
    kw_score = kw_hits / denom

    denom = max(len(stack), 1)
    stack_score = stack_hits / denom

    denom = max(len(domains), 1)
    domain_score = domain_hits / denom

    # Seniority: if profile says junior and the posting looks senior, penalise
    seniority_score = 1.0
    if seniority == "junior":
        if any(
            s in text for s in ["senior", "lead", "principal", "staff", "10+ years", "7+ years"]
        ):
            seniority_score = 0.1

    base = 0.40 * kw_score + 0.25 * stack_score + 0.20 * domain_score + 0.15 * seniority_score
    return max(0.0, base - 0.5 * exclude_hits)


def rank(jobs: list[Job] | None = None, profile: dict | None = None) -> list[tuple[Job, float]]:
    """Rank jobs by match score. Returns list of (job, score) tuples."""
    if jobs is None:
        jobs = load_jobs()
    if profile is None:
        profile = load_profile()

    scored = [(job, _score(job, profile)) for job in jobs]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def main(top: int = 20) -> int:
    profile = load_profile()
    min_score = float(profile.get("min_score", 0.15))

    ranked = rank(profile=profile)
    filtered = [(j, s) for j, s in ranked if s >= min_score]

    print(f"Top {top} of {len(filtered)} listings scoring >= {min_score:.2f}:\n")
    for i, (job, score) in enumerate(filtered[:top], 1):
        print(f"{i:2d}. [{score:.2f}] {job['title']} @ {job['company']}")
        print(f"    {job['url']}")
        print()

    # Persist ranked output for downstream scripts
    payload = [{"score": round(s, 4), **job} for job, s in filtered]
    RANKED_OUTPUT.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Persisted {len(payload)} ranked jobs to {RANKED_OUTPUT}")
    return 0


if __name__ == "__main__":
    top_n = 20
    if len(sys.argv) > 1:
        try:
            top_n = int(sys.argv[1])
        except ValueError:
            pass
    sys.exit(main(top_n))
