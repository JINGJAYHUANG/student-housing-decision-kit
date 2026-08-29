# Methodology

## 1. Decision framing

The engine separates three questions that are often incorrectly collapsed into one score:

1. **Is the evidence structurally valid?**
2. **Does the option violate a non-negotiable constraint?**
3. **How attractive is the option among the remaining trade-offs?**

This sequence reduces the chance that a high convenience score compensates for a true veto such as an unacceptable move-in date or signing-cash requirement.

## 2. Cost definitions

For a listing with `occupants = n`:

```text
rent_share = monthly_rent_total / n
required_fees_share = monthly_required_fees_total / n
utilities_share = monthly_utilities_estimate / n
all_in_monthly = rent_share + required_fees_share + utilities_share
```

Signing cash is:

```text
rent_share × (
  first_month_required
  + last_month_required
  + security_deposit_months
  + broker_fee_months
)
+ one_time_fees / n
```

The refundable deposit is reported separately. First-year nonrefundable cost excludes the refundable security deposit:

```text
all_in_monthly × 12
+ rent_share × broker_fee_months
+ one_time_fees / n
```

These are planning definitions, not a statement of local law or a specific lease.

## 3. Hard constraints

The following constraints are evaluated independently:

- allowed housing mode;
- minimum safety score;
- maximum commute;
- maximum move-in delay;
- maximum signing cash;
- optional enforced all-in monthly cap;
- optional required source freshness.

Every failed condition becomes a human-readable reason. Multiple reasons accumulate.

## 4. Component scoring

### Affordability

Let `r = all_in_monthly / max_all_in_monthly`.

- `r ≤ 0.75` → 10;
- `0.75 < r ≤ 1.00` → linearly declines from 10 to 7;
- `1.00 < r ≤ 1.20` → linearly declines from 7 to 0;
- `r > 1.20` → 0.

This curve allows an option near the planning budget to remain competitive when other characteristics are strong, while materially over-budget options are penalized sharply.

### Commute

The optimal commute threshold is bounded between 5 and 15 minutes and otherwise set to 40% of the configured maximum. Scores are:

- 10 at or below the optimal threshold;
- linearly decline to 5 at the configured cap;
- linearly decline toward 0 above the cap.

Eligibility still uses the hard commute cap.

### Timing

- available on the target date → 10;
- earlier availability receives a small penalty, capped at 2 points, to represent avoidable overlap cost;
- later availability declines linearly to 0 at the tolerated delay;
- later than the tolerance → 0 and a hard-constraint failure.

### Freshness

Evidence receives full credit through one-third of the configured maximum source age, then declines linearly. It reaches 0 at twice the configured maximum age. A separate hard constraint can reject evidence older than the maximum.

### Completeness

Completeness is the proportion of eight checks that are present or structurally usable: area, area size, bathroom count, source identifier, notes, required fees, utilities and one-time fees.

### User-assessed dimensions

Safety, convenience, management, quiet, space and application fit are accepted as 0–10 inputs. The engine does not pretend these are objectively observed. A real workflow should define evidence rubrics before scoring.

## 5. Weighted aggregation

Weights are normalized to sum to 1.0:

```text
normalized_weight_i = raw_weight_i / Σ(raw_weights)
total_score = Σ(component_score_i × normalized_weight_i)
```

The export includes both component scores and weighted contributions.

## 6. Ranking

Records are sorted by:

1. eligible before filtered;
2. higher total score;
3. lower all-in monthly cost;
4. listing ID as deterministic tie-breaker.

A filtered option can have a high score. It remains below all eligible options because it violates at least one declared veto.

## 7. Pareto analysis

Among eligible options, listing A dominates listing B when A is no worse on:

- all-in monthly cost;
- commute;
- total score;

and strictly better on at least one. Non-dominated options form the displayed Pareto front.

## 8. Sensitivity analysis

The 28 scenarios include the baseline, ±25% perturbations to each of 11 criterion weights and five constraint stresses. Weight perturbations are renormalized.

For each listing the engine reports:

- baseline rank;
- best and worst rank;
- average rank;
- number of first-place finishes;
- scenarios in which it remains eligible;
- robustness score.

The robustness score combines eligibility persistence and rank stability. It is a descriptive diagnostic, not a calibrated probability.

## 9. Reproducibility

The input hash combines the exact bytes of the listing CSV and preference JSON, including filenames, using SHA-256. The run manifest also hashes every generated artifact except itself.

The deterministic example fixes both `--as-of` and `--generated-at`.
