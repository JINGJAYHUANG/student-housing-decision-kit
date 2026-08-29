# Handoff

## Entry point

Run `make all` from the repository root.

## Key files

- CLI: `src/housing_decision_kit/cli.py`
- scoring and constraints: `src/housing_decision_kit/scoring.py`
- sensitivity: `src/housing_decision_kit/sensitivity.py`
- synthetic inputs: `examples/synthetic_city/`
- expected outputs: `examples/synthetic_city/output/`
- privacy controls: `scripts/privacy_scan.py`
- deterministic verification: `scripts/verify_demo.py`, `scripts/compare_demo.py`

## Do not do

- Do not replace the synthetic fixture with a redacted real search.
- Do not use the package to make claims about current prices or safety.
- Do not push this project into the unrelated `try` repository.

## Next action

Publish the prepared history to a new repository named `student-housing-decision-kit` when repository creation is available.
