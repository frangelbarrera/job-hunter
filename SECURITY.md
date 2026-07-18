# Security Policy

## Supported versions

This is a personal automation tool. Only the latest `main` branch receives updates.

| Version | Supported |
|---------|-----------|
| `main`  | ✓         |
| tagged releases | ✓ (latest only) |

## Reporting a vulnerability

**Do not open a public issue for security reports.**

Email the maintainer privately at **frangel.barrera.dev@gmail.com** with the subject `job-hunter security report`. Include:

1. Description of the issue and its impact
2. Reproduction steps (commands, inputs, expected vs actual behaviour)
3. Affected commit hash
4. Suggested fix (optional)

You should receive an acknowledgement within 7 days. If confirmed, a fix will be prepared and a coordinated disclosure date agreed.

## Threat model

This tool processes:

- **Public job postings** scraped from RemoteOK and HackerNews. No credentials, no PII.
- **Your own profile** (`profile.yaml`) — name, target role, stack. Treat this file as semi-public; do not put secrets in it.
- **Your OAuth credentials** (`credentials.json`, `token.json`) — these grant full access to the Gmail account they're issued for. **Never commit these files.** They are listed in `.gitignore` and the README explicitly warns against committing them.

The Gmail OAuth scopes requested are intentionally minimal:

- `gmail.send` — to send drafted cold emails
- `gmail.readonly` — to detect replies for follow-up logic

We do **not** request `gmail.modify` (can delete emails) or `gmail.compose` (can create drafts without your review). If you need broader scopes, file an issue first.

## Disclosure timeline

- Day 0 — Private report received
- Day 1–7 — Triage and acknowledgement
- Day 7–30 — Fix developed. Critical issues (RCE, secret leak) are expedited
- Day 30 (or earlier for critical) — Fix committed and public disclosure coordinated

## Scope

In scope:
- Bugs in `scrapers/`, `scripts/`, `tests/` that compromise the host running the tool or expose secrets
- OAuth scope misuse or excessive permissions
- Dependency vulnerabilities with a known exploit path
- GitHub Actions workflow misconfigurations that leak secrets

Out of scope:
- "The scraper can read a job posting I didn't apply to." Yes — that's its purpose.
- "The cold email template sounds spammy." That's a UX complaint, not a security issue.
- Reports about dependencies that have no exploit path in this codebase.
