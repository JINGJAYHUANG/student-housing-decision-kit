# Changelog

All notable changes to this project are documented here.

The format follows Keep a Changelog, and this project uses semantic versioning.

## [Unreleased]

### Planned

- Optional geospatial adapters for user-supplied commute and neighborhood data.
- Workbook export through a separately maintained adapter.
- Configurable scoring curves beyond the built-in transparent defaults.

## [0.1.0] - 2026-08-29

### Added

- Dependency-free Python CLI with `validate` and `evaluate` commands.
- Explicit hard constraints for housing mode, safety, commute, timing, signing cash, optional monthly budget and source freshness.
- Eleven-component weighted score with per-component contributions.
- All-in monthly, signing cash, refundable deposit and first-year cost calculations.
- Pareto-front analysis across cost, commute and total score.
- Twenty-eight deterministic sensitivity scenarios.
- Four budget stress scenarios.
- CSV, JSON, HTML and SQLite output bundle.
- Synthetic, fixed-date example containing fourteen fictional listings.
- Unit and integration tests, privacy scanning and deterministic demo verification.
