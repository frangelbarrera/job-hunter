## Summary

Brief description of the change.

## Type

- [ ] feat — new functionality
- [ ] fix — defect correction
- [ ] docs — documentation only
- [ ] ci — CI/build only
- [ ] refactor — no behaviour change
- [ ] test — test additions only

## Checklist

- [ ] `pytest` passes locally
- [ ] `ruff check scrapers/ scripts/ tests/` is clean
- [ ] `ruff format --check scrapers/ scripts/ tests/` is clean
- [ ] No secrets, credentials, or PII committed
- [ ] If adding a scraper: tests cover parsing + edge cases
- [ ] If changing CI: workflow validates locally with `act` or a manual dry run

## Notes

Any extra context for the reviewer.
