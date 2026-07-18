# Job Hunter

Automated job scraping pipeline for security engineer roles. Aggregates listings from multiple remote-first job boards, scores them against a target profile, and drafts personalised outreach with LLM assistance.

[![CI](https://github.com/frangelbarrera/job-hunter/actions/workflows/ci.yml/badge.svg)](https://github.com/frangelbarrera/job-hunter/actions/workflows/ci.yml)
[![Scrape](https://github.com/frangelbarrera/job-hunter/actions/workflows/scrape.yml/badge.svg)](https://github.com/frangelbarrera/job-hunter/actions/workflows/scrape.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)

## Features

- **Multi-source scraping** — RemoteOK, HackerNews "Ask HN: Who is hiring?", with a pluggable interface for new sources
- **Profile matching** — scores each listing (0–1) against a YAML profile so the noise floor stays low
- **LLM-assisted outreach** — drafts cold emails via Gemini (with Groq fallback) using a strict template
- **Scheduled** — GitHub Actions runs every 6h on public runners, no local bandwidth cost
- **Self-contained** — output is a single JSON file you can grep, pipe, or import anywhere
- **No PII** — scrapers store only public job metadata, no applicant data ever persisted

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub Actions (cron 6h)                   │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  RemoteOK    │    │  HackerNews  │    │   (pluggable)│       │
│  │  scraper     │    │  scraper     │    │   scrapers   │       │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘       │
│         │                   │                   │               │
│         └──────────┬────────┴───────────────────┘               │
│                    ▼                                            │
│           ┌─────────────────┐                                   │
│           │  utils.save()   │ → data/jobs.json (deduped)        │
│           └─────────────────┘                                   │
└─────────────────────────────────────────────────────────────────┘
                              │ git push
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Local laptop (manual)                        │
│                                                                 │
│  git pull → match_score.py → generate_email.py → review → send  │
│                                                                 │
│  LLM: Gemini API (primary) → Groq API (fallback)               │
│  Mail: Gmail API (read-only + send scopes only)                │
└─────────────────────────────────────────────────────────────────┘
```

## Quick start

```bash
git clone https://github.com/frangelbarrera/job-hunter.git
cd job-hunter
pip install -r requirements-dev.txt
cp .env.example .env  # then edit .env with your keys
cp profile.yaml.example profile.yaml  # then edit with your details
pytest  # should pass green
python -m scrapers.remoteok
python -m scrapers.hackernews
cat data/jobs.json | python -m json.tool | head -40
```

## Configuration

### Environment variables (`.env`)

| Variable | Purpose | Required |
|---|---|---|
| `GEMINI_API_KEY` | Primary LLM (cold email drafts) | For `generate_email.py` |
| `GROQ_API_KEY` | Fallback LLM | For `generate_email.py` |
| `GMAIL_CREDENTIALS_PATH` | Path to OAuth `credentials.json` | For `scripts/send_email.py` |
| `GMAIL_TOKEN_PATH` | Path to cached `token.json` | For `scripts/send_email.py` |
| `PROFILE_PATH` | YAML with your target profile | Defaults to `profile.yaml` |

### Profile (`profile.yaml`)

A YAML file describing the role you're targeting. The match scorer uses this to weight listings.

```yaml
# See profile.yaml.example for the full template
target_title: Security Engineer
seniority: junior  # junior | mid | senior
remote_only: true
stack: [python, typescript, fastapi, react]
domains: [security, osint, ics, ml]
keywords:
  - security
  - python
  - remote
  - junior
exclude_keywords:
  - senior
  - lead
  - manager
```

## Usage

### Scrape (automatic via GitHub Actions)

The workflow `.github/workflows/scrape.yml` runs every 6h. You can also trigger it manually from the Actions tab, or run locally:

```bash
python -m scrapers.remoteok
python -m scrapers.hackernews
```

Results land in `data/jobs.json` (deduped, last 1000 entries kept).

### Score and rank

```bash
python -m scripts.match_score
# prints top 20 matches to stdout
# writes data/ranked_jobs.json for downstream use
```

### Draft cold emails

```bash
python -m scripts.generate_email --top 5
# prints 5 drafted emails to stdout, asks for confirmation before saving
# drafts saved to data/drafts/ (gitignored)
```

### Send (optional, requires Gmail API setup)

```bash
python -m scripts.send_email --dry-run  # prints what would be sent
python -m scripts.send_email            # actually sends, requires confirmation per email
```

## Project structure

```
job-hunter/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml              # lint + test on push & PR
│   │   └── scrape.yml          # scheduled scraping every 6h
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       └── feature_request.md
├── .gitignore
├── .pre-commit-config.yaml
├── .env.example
├── LICENSE
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── profile.yaml.example
├── scrapers/
│   ├── __init__.py
│   ├── base.py                 # ScraperProtocol + shared types
│   ├── remoteok.py
│   ├── hackernews.py
│   └── utils.py                # save_jobs(), dedupe(), load_profile()
├── scripts/
│   ├── __init__.py
│   ├── match_score.py
│   ├── generate_email.py
│   └── send_email.py
├── data/
│   └── .gitkeep
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_remoteok.py
    ├── test_hackernews.py
    └── test_match_score.py
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). PRs welcome but this is primarily a personal automation repo — features land when they scratch my own itch.

## Security

See [SECURITY.md](SECURITY.md). Short version: never commit secrets, the scrapers store no PII, and the Gmail integration requests only `gmail.send` + `gmail.readonly` scopes.

## License

MIT — see [LICENSE](LICENSE).

## Disclaimer

This tool scrapes publicly available job postings for personal use only. It does not bypass authentication, violate ToS, or attempt to deceive job platforms. Automated outreach is the user's responsibility — follow CAN-SPAM (US), GDPR (EU), and your local regulations. Don't be a spammer.
