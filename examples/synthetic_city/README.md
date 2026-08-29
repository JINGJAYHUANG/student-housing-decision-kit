# Synthetic City Example

This example is intentionally fictional.

- Every row is marked `is_synthetic=true`.
- Property names, areas, prices, dates and source identifiers do not describe real listings.
- The example exists to exercise scoring, hard constraints, stale-source handling, budget stress tests, Pareto analysis and sensitivity analysis.
- The fixed analysis date is `2026-06-15`, so the output can be reproduced consistently.

Run:

```bash
housing-decision evaluate \
  --listings examples/synthetic_city/listings.csv \
  --preferences examples/synthetic_city/preferences.json \
  --as-of 2026-06-15 \
  --generated-at 2026-06-15T12:00:00Z \
  --output-dir examples/synthetic_city/output
```
