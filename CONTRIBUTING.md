# Contributing

Contributions are welcome when they preserve the project's core guarantees: transparency, explicit dates, auditable constraints and privacy-conscious examples.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -e .
make all
```

## Contribution rules

1. **Never commit real applicant records or active housing searches.** Use synthetic or properly licensed public fixtures.
2. **Never hide exclusions.** A listing that fails a hard constraint must remain visible with a reason.
3. **Make time explicit.** Listing research must include `source_checked_at`, and every run must include `--as-of`.
4. **Document model changes.** Any scoring-curve or constraint change requires tests and a methodology update.
5. **Keep the core dependency-free.** New runtime dependencies require a clear benefit and review.
6. **Do not present scores as objective truth.** Qualitative inputs and uncertainty must remain visible.

## Pull request checklist

- [ ] Tests pass with `python -m unittest discover -s tests -v`.
- [ ] `python scripts/privacy_scan.py` passes.
- [ ] The deterministic demo regenerates and `python scripts/verify_demo.py` passes.
- [ ] New fields are documented in `docs/data_dictionary.md` and the JSON schemas.
- [ ] No current listing, personal identifier, contact detail, lease document or credential is included.
