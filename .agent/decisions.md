# Decisions

## D-001 — Clean-room public implementation

The historical one-off analysis contained real institutions, properties, contacts, stale prices, personal preferences and workstation paths. None are copied into the public repository. The public implementation uses fictional records while preserving the general decision logic.

## D-002 — Python standard library only

The core uses no runtime dependencies. This reduces installation friction and supply-chain surface while keeping the logic inspectable.

## D-003 — Hard constraints remain separate

Safety, commute, timing, signing cash, optional monthly budget, housing mode and freshness are evaluated as vetoes. They are not blended into an average.

## D-004 — Filtered records remain visible

Failed options remain in outputs with cumulative reasons. Auditability takes precedence over a cleaner-looking shortlist.

## D-005 — Explicit temporal reference

`--as-of` is required. The program never silently treats a saved listing as current.

## D-006 — Multi-format outputs

The same run produces human-readable HTML and machine-readable CSV, JSON and SQLite, plus hashes. No separate manual report calculation is allowed.

## D-007 — No public workbook dependency in v0.1

The historical workflow used a specialized spreadsheet library. The public alpha prioritizes a dependency-free core. Spreadsheet export is a future adapter rather than a runtime requirement.
