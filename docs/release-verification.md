# Release Verification Record

Date: 2026-08-29  
Release candidate: 0.1.0

## Local verification

| Check | Result |
|---|---|
| Python syntax compilation | Passed on Python 3.13.5 |
| Unit and integration tests | 26 passed |
| Public-fixture validation | 0 errors, 0 warnings, 1 informational synthetic-data message |
| Privacy and secret scan | Passed across 66 text files |
| Generated artifact verification | Passed |
| Portable deterministic regeneration | 8 text/JSON/CSV/HTML artifacts byte-identical; SQLite schema/data and normalized manifest equivalent across runtime versions |
| Wheel build | Passed |
| Clean virtual-environment wheel install | Passed without downloading runtime dependencies |
| Installed CLI evaluation | Passed and reproduced the committed bundle |
| Desktop visual render | Passed at 1440 × 1000 viewport |
| Narrow visual render | Passed at 390 × 844 viewport; no body-level horizontal overflow |
| HTML escaping tests | Passed for user-controlled text and source attributes |

## Demonstration invariants

- 14 fictional listings;
- all rows marked synthetic;
- all public sources use `synthetic://` identifiers;
- 8 options eligible in the baseline run;
- 28 sensitivity scenarios;
- 4 budget stress scenarios;
- fixed input hash and fixed generation timestamp;
- top eligible option remains `Scholars Landing` in the baseline fixture.

## Pending external verification

GitHub-hosted verification is required on Python 3.11, 3.12 and 3.13 with read-only repository permissions and pinned action revisions before merge.

## Environment note

A global `pip check` reported an unrelated pre-existing package conflict between `moviepy` and `pillow` in the working container. The project has no runtime dependencies, and the clean virtual-environment wheel installation passed. The unrelated global conflict does not affect this release candidate.
