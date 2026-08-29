# Data Card

## Dataset name

Synthetic City Student Housing Example, version 0.1.0.

## Purpose

The dataset exercises every major code path without publishing a real housing search. It is designed to demonstrate:

- solo and shared housing modes;
- cost sharing;
- safety, commute, timing and freshness constraints;
- stale evidence;
- high upfront cash;
- late move-in;
- over-limit commute;
- Pareto trade-offs;
- rank sensitivity.

## Composition

- 14 fictional listing rows;
- 28 CSV columns;
- 1 fictional preference profile;
- fixed analysis date: 2026-06-15;
- fixed target move-in date: 2026-08-20.

## Provenance

The records were authored specifically for this repository. Names, areas, prices, dates, notes and `synthetic://` identifiers are fictional. They were not copied from a live listing service.

## Privacy

Every row has `is_synthetic=true`. The fixture contains no real name, address, phone number, email address, university, landlord, lease, application record or active listing.

## Labels and scores

Qualitative fields use a 0–10 scale. They are constructed test inputs, not measured truths. The values were chosen to create realistic trade-offs and constraint failures.

## Recommended use

- documentation examples;
- unit and integration tests;
- demonstrations of the output bundle;
- experimentation with weights and constraints.

## Prohibited interpretation

Do not treat the data as current market intelligence, price guidance, safety evidence or a recommendation about any real location.

## Maintenance

Changes to the example must preserve synthetic status, pass the privacy scanner and regenerate the deterministic outputs and manifest.
