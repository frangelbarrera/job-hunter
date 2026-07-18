# Contributing

Thanks for considering a contribution. This is a small personal automation repo, so the bar is low but a few conventions help.

## Setup

```bash
git clone https://github.com/frangelbarrera/job-hunter.git
cd job-hunter
pip install -r requirements-dev.txt
pre-commit install
cp .env.example .env  # edit with your keys
cp profile.yaml.example profile.yaml  # edit with your profile
pytest
```

## Workflow

1. Open an issue describing what you want to change and why
2. Fork the repo, create a branch named `feat/<short-description>` or `fix/<short-description>`
3. Make your changes. Keep commits focused. Conventional Commits style is appreciated (`feat:`, `fix:`, `docs:`, `ci:`, `chore:`)
4. Run `pre-commit run --all-files` and `pytest` locally. Both must be green
5. Open a PR referencing the issue

## Code style

- Python 3.11+
- Formatter and linter: `ruff` (configured in `pyproject.toml`)
- Type hints encouraged for public functions
- Docstrings: triple-double-quote, first line imperative, blank line, details
- No emojis in code or commit messages
- Tests live in `tests/`, mirror the module path (`scrapers/remoteok.py` → `tests/test_remoteok.py`)

## Adding a new scraper

1. Implement the scraper in `scrapers/<source>.py`
2. It must expose a `scrape()` function returning `list[Job]` (see `scrapers/base.py` for the `Job` TypedDict)
3. Add tests in `tests/test_<source>.py`. At minimum: parse a saved fixture and assert the output structure
4. Register it in `.github/workflows/scrape.yml` (one new `python -m scrapers.<source>` line)
5. Update the README architecture section if the source is non-obvious

## Adding a new LLM provider

1. Implement a function with the signature `(job: Job, profile: Profile) -> str | None` in `scripts/generate_email.py`
2. Add it to the fallback chain in `generate_email_robust()`
3. Test that it gracefully fails (network error, quota exceeded) so the fallback kicks in

## Commit message conventions

```
<type>(<scope>): <subject>

<body optional>

<footer optional>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `ci`, `chore`, `perf`, `build`, `revert`

Examples:
- `feat(scrapers): add web3.career source`
- `fix(hackernews): handle empty comment_text`
- `docs(readme): clarify Gmail OAuth setup steps`

## What I won't accept

- Scrapers that bypass authentication or violate a site's ToS
- Features that store applicant PII in the repo
- "Cute" code that optimises for cleverness over readability
- Dependencies that duplicate stdlib functionality
