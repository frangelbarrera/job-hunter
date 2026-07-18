"""Draft cold emails for top-ranked jobs using Gemini (with Groq fallback).

Both providers are optional — the script degrades gracefully if a key is missing.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from scrapers.utils import load_profile

RANKED_FILE = Path(__file__).resolve().parent.parent / "data" / "ranked_jobs.json"

DEFAULT_PROFILE_SUMMARY = """
Cybersecurity and AI engineer. Stack: Python (FastAPI, pytest), TypeScript (Next.js),
C++. Open-source contributor (5 merged PRs upstream including kubescape on ICS/OT
Kubernetes hardening). Author of OSINT-BIBLE (600+ stars). Looking for junior
security engineer roles, remote-first.
GitHub: https://github.com/frangelbarrera
Portfolio: https://frangelbarrera.vercel.app
"""

EMAIL_RULES = """
Write a cold email for a job application. STRICT RULES:
- Length: 100-180 words
- Hook in the first sentence referencing something specific about the company or product
- Body: 1-2 sentences mapping my profile to their stated problem
- Call to action: ask for a 15-minute intro call
- PS line: link to my GitHub profile
- No fluff ("passionate", "results-driven", "team player")
- No emojis
- Tone: confident but not arrogant, professional but human
- Sign: "Best,\\nFrangel"
"""


def _build_prompt(job: dict, profile: dict) -> str:
    profile_summary = profile.get("summary", DEFAULT_PROFILE_SUMMARY)
    return f"""
{EMAIL_RULES}

MY PROFILE:
{profile_summary}

JOB POSTING:
Title: {job.get("title", "Unknown")}
Company: {job.get("company", "Unknown")}
URL: {job.get("url", "")}
Description: {(job.get("description") or "N/A")[:2000]}

Write the email now.
"""


def _generate_with_gemini(prompt: str) -> str | None:
    try:
        import google.generativeai as genai
    except ImportError:
        return None

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as exc:
        print(f"[gemini] failed: {exc}", file=sys.stderr)
        return None


def _generate_with_groq(prompt: str) -> str | None:
    try:
        from groq import Groq
    except ImportError:
        return None

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-70b-instruct",
            messages=[
                {
                    "role": "system",
                    "content": "You write concise cold emails for job applications.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as exc:
        print(f"[groq] failed: {exc}", file=sys.stderr)
        return None


def generate_email(job: dict, profile: dict | None = None) -> str | None:
    """Generate a cold email draft for a single job.

    Tries Gemini first, falls back to Groq, returns None if both fail.
    """
    if profile is None:
        profile = load_profile()

    prompt = _build_prompt(job, profile)

    email = _generate_with_gemini(prompt)
    if email:
        return email

    email = _generate_with_groq(prompt)
    if email:
        return email

    print(
        "[generate_email] no LLM provider available (set GEMINI_API_KEY or GROQ_API_KEY)",
        file=sys.stderr,
    )
    return None


def main(top: int = 5) -> int:
    if not RANKED_FILE.exists():
        print(f"Ranked file not found: {RANKED_FILE}", file=sys.stderr)
        print("Run `python -m scripts.match_score` first.", file=sys.stderr)
        return 1

    jobs = json.loads(RANKED_FILE.read_text(encoding="utf-8"))
    if not jobs:
        print("No ranked jobs available.", file=sys.stderr)
        return 1

    profile = load_profile()
    selected = jobs[:top]

    print(f"Drafting {len(selected)} emails...\n")
    for i, job in enumerate(selected, 1):
        print(f"=== [{i}] {job.get('title', '?')} @ {job.get('company', '?')} ===")
        print(f"URL: {job.get('url', '')}")
        print(f"Score: {job.get('score', 0):.2f}\n")
        email = generate_email(job, profile)
        if email:
            print(email)
        else:
            print("[no email generated]")
        print("\n" + "=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    top_n = 5
    if len(sys.argv) > 1:
        try:
            top_n = int(sys.argv[1])
        except ValueError:
            pass
    sys.exit(main(top_n))
