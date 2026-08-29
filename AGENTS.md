# Agent Instructions

## Objective

Maintain a public, reusable and privacy-conscious student-housing decision-support toolkit.

## Non-negotiable boundaries

1. Never add real housing-search records, addresses, contact information, lease terms, applicant documents or user-specific profiles.
2. Every committed example listing must use `is_synthetic=true` and a `synthetic://` source.
3. Never remove a failed option without preserving its constraint reason.
4. Never imply that a score predicts safety, approval or the objectively best home.
5. Every run and source record must retain explicit dates.
6. Do not add network scraping or credentialed integrations to the core package.
7. Do not weaken tests, privacy scanning or deterministic verification merely to make CI pass.

## Required context before edits

Read, in order:

- `.agent/brief.md`
- `.agent/plan.md`
- `.agent/status.md`
- `.agent/decisions.md`
- `.agent/handoff.md`
- `MODEL_CARD.md`
- `DATA_CARD.md`

## Required verification

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/privacy_scan.py
make demo
python scripts/verify_demo.py
```

Update `.agent/status.md` and `.agent/handoff.md` after material work.
