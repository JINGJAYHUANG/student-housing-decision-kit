# Architecture

## Design goals

- local-first execution;
- no runtime dependencies outside the Python standard library;
- explicit temporal context;
- deterministic outputs when timestamps are fixed;
- machine-readable and human-readable artifacts from the same run;
- no silent filtering;
- public examples that cannot expose a real search.

## Module responsibilities

| Module | Responsibility |
|---|---|
| `models.py` | Typed domain models and derived cost definitions |
| `io.py` | CSV/JSON parsing, deterministic hashes and writers |
| `validation.py` | Structural, range, date and publication-boundary checks |
| `scoring.py` | Component curves, constraints, ranking and Pareto front |
| `sensitivity.py` | Scenario generation and rank-stability diagnostics |
| `budget.py` | Recurring-cost, signing-cash and FX stress scenarios |
| `sqlite_export.py` | Relational schema and downstream analytical export |
| `report.py` | Self-contained HTML decision report |
| `cli.py` | Orchestration, exit codes and output manifest |

## Processing sequence

```text
load → validate → stop on error
                 ↓
         score + constraints
                 ↓
          eligible-first rank
                 ↓
   Pareto + sensitivity + budget stress
                 ↓
  CSV + JSON + HTML + SQLite + manifest
```

## Exit behavior

- `0`: validation/evaluation succeeded;
- `2`: validation errors or invalid CLI date/timestamp input;
- other nonzero values: unhandled runtime or filesystem failure.

## Reproducibility boundary

A fixed input hash does not prove the source was true. It proves which bytes produced the outputs. Source truth and computational reproducibility are related but distinct controls.

## Extension points

Future adapters may populate inputs from geocoding, transit, listing or public-safety sources. They should remain outside the core scoring package so network access, licensing, authentication and data freshness are separately reviewable.
