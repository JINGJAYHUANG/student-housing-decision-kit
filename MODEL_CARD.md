# Model Card

## Model name

Student Housing Decision Kit scoring model, version 0.1.0.

## Model type

Deterministic multi-criteria decision analysis with explicit hard constraints, piecewise scoring curves, weighted aggregation, Pareto analysis and scenario-based sensitivity testing.

It is not a statistical, machine-learning or generative model.

## Intended use

- Compare a manageable set of student-housing options.
- Make cost, timing, freshness and non-negotiable constraints explicit.
- Document how a ranking changes when assumptions change.
- Produce an auditable local report for personal decision support.

## Out-of-scope use

- Predicting crime, applicant approval, rent growth or lease outcomes.
- Replacing current official data, inspection, legal review or professional advice.
- Automatically rejecting applicants or making decisions for another person.
- Publishing a real person's private search data.
- Treating a qualitative safety score as a guarantee.

## Inputs

A listing contains objective-style fields such as cost and dates, plus user-assessed 0–10 fields such as management and quiet. A preference profile contains hard limits and criterion weights.

See `docs/data_dictionary.md` for the complete contract.

## Outputs

- eligibility and explicit reasons;
- total score and component scores;
- per-criterion weighted contributions;
- eligible-first rank;
- Pareto indicator;
- rank stability across 28 scenarios;
- cost stress scenarios;
- CSV, JSON, HTML and SQLite exports.

## Core assumptions

1. Input costs and dates are accurate for the declared analysis date.
2. Qualitative scores are created consistently and supported by evidence.
3. Occupancy shares costs equally among occupants.
4. Weights represent relative preferences, not causal importance.
5. Hard constraints are truly non-negotiable for the current run.

## Scoring behavior

All components are bounded from 0 to 10. Weights are normalized before aggregation.

```text
total_score = Σ(component_score × normalized_weight)
```

Hard constraints do not alter the numeric score. They determine eligibility separately, which avoids hiding a veto inside an average.

## Evaluation

The release is tested with deterministic synthetic fixtures. Tests cover scoring anchor points, constraint accumulation, ranking order, Pareto marking, validation, hashing, sensitivity coverage, budget scenarios, CLI artifacts and SQLite queries.

The demonstration is not a benchmark of real-world decision quality.

## Known risks

- Subjective scores may encode bias or inconsistent evidence.
- Weight choices can create false precision.
- A source can be recent yet inaccurate.
- Equal cost-sharing may not match a real roommate agreement.
- The freshness threshold is a policy choice, not proof of availability.
- Rank robustness does not measure the probability that a listing is suitable.

## Risk controls

- required analysis date;
- source-check date per row;
- explicit validation messages;
- separate hard constraints;
- retained filtered options and reasons;
- component contribution export;
- sensitivity analysis;
- synthetic public fixture;
- privacy scanner and publication policy.

## Human oversight

A user should inspect source evidence, update costs and availability, review the lease, verify the route and neighborhood, and make the final decision. The tool supports that process; it does not automate it.
