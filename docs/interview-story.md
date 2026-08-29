# Project Story for Interviews and Portfolio Reviews

## Problem

Housing comparison is usually handled with ad hoc tabs and spreadsheets. The resulting decision is difficult to audit because current and stale evidence are mixed, costs are incomplete, preferences are hidden inside a single score and excluded options disappear.

## Engineering response

This project turns that workflow into a local, deterministic decision system:

- a formal data contract;
- validation before analysis;
- hard constraints separated from weighted trade-offs;
- component-level explanations;
- sensitivity and Pareto analysis;
- multiple analytical exports;
- a committed synthetic fixture instead of private records;
- automated tests, privacy checks and CI.

## What this demonstrates

- translating an ambiguous real-world decision into explicit requirements;
- multi-criteria decision analysis without false machine-learning claims;
- data validation and temporal provenance;
- local-first privacy design;
- reproducible reporting and relational exports;
- product judgment about what must remain private.

## Defensible claim

> Built a dependency-free Python decision-support toolkit that validates housing inputs, separates hard constraints from weighted scoring, runs 28 sensitivity scenarios, produces Pareto and budget diagnostics, and exports an auditable HTML/CSV/JSON/SQLite bundle using synthetic public data.

## Claims to avoid

- that the tool predicts the safest neighborhood;
- that it guarantees an optimal housing choice;
- that the synthetic demonstration reflects a current market;
- that a high robustness score is a probability;
- that any real user's private housing search is included in the repository.
