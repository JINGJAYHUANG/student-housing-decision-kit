# Data Dictionary

## Listing CSV

| Field | Type | Required | Meaning |
|---|---:|:---:|---|
| `listing_id` | string | yes | Stable unique identifier |
| `name` | string | yes | Display label; use a pseudonym or synthetic name in public data |
| `area` | string | yes | Neighborhood or broad area label |
| `housing_mode` | enum | yes | `solo` or `shared` |
| `bedrooms` | number | yes | Bedroom count; studio may be `0` |
| `bathrooms` | number | yes | Positive bathroom count |
| `sqft` | number/null | no | Approximate unit area |
| `monthly_rent_total` | number | yes | Total monthly rent for the unit |
| `monthly_required_fees_total` | number | yes | Mandatory recurring fees for the unit |
| `monthly_utilities_estimate` | number | yes | Estimated monthly utilities for the unit |
| `occupants` | integer | yes | Number of people sharing unit-level costs |
| `commute_minutes` | number | yes | Consistently measured one-way commute |
| `safety_score` | 0–10 | yes | Evidence-backed user assessment, not a guarantee |
| `convenience_score` | 0–10 | yes | Access to daily needs and transport |
| `management_score` | 0–10 | yes | Management, maintenance and building operations |
| `quiet_score` | 0–10 | yes | Expected suitability for sleep and study |
| `space_score` | 0–10 | yes | Layout and usable-space assessment |
| `application_score` | 0–10 | yes | Fit with the applicant's documentation situation |
| `available_date` | date | yes | Earliest usable move-in date, `YYYY-MM-DD` |
| `source_checked_at` | date | yes | Date the evidence was last checked |
| `source_url` | string | yes | Evidence locator; public fixture uses `synthetic://` |
| `is_synthetic` | boolean | yes | Explicit publication boundary flag |
| `first_month_required` | boolean | yes | Whether first month is due at signing |
| `last_month_required` | boolean | yes | Whether last month is due at signing |
| `security_deposit_months` | number | yes | Deposit as rent-share months |
| `broker_fee_months` | number | yes | Nonrefundable fee as rent-share months |
| `one_time_fees` | number | yes | Other one-time unit-level charges |
| `notes` | string | no | Evidence summary and uncertainty; no personal data |

## Preference JSON

| Field | Type | Meaning |
|---|---:|---|
| `profile_name` | string | Generic label for the profile |
| `target_label` | string | Destination label, not necessarily a real institution |
| `target_move_in` | date | Preferred move-in date |
| `max_move_in_delay_days` | integer | Maximum tolerated late move-in |
| `max_all_in_monthly` | number | Planning budget used by affordability scoring |
| `enforce_budget_cap` | boolean | Whether budget is also a hard constraint |
| `max_upfront_cash` | number | Signing-cash hard cap |
| `min_safety_score` | 0–10 | Safety hard floor |
| `max_commute_minutes` | number | Commute hard cap |
| `allowed_housing_modes` | array | Any of `solo`, `shared` |
| `max_source_age_days` | integer | Source freshness policy |
| `require_fresh_source` | boolean | Whether stale evidence fails eligibility |
| `home_currency` | string | Display currency code for first-year conversion |
| `usd_to_home_rate` | number | Planning conversion rate |
| `sensitivity_delta` | 0–1 | Relative weight perturbation size |
| `weights` | object | One nonnegative weight for every criterion |

## Derived output fields

| Field | Meaning |
|---|---|
| `eligible` | True when no hard constraint fails |
| `constraint_reasons` | Complete list of failed constraints |
| `total_score` | Weighted score from 0 to 10 |
| `all_in_monthly` | Per-person rent, required fees and utilities |
| `cash_needed_at_signing` | Planning estimate of initial cash |
| `refundable_deposit` | Security-deposit component |
| `first_year_nonrefundable_cost` | Twelve-month recurring cost plus nonrefundable upfront fees |
| `source_age_days` | Analysis date minus source-check date |
| `pareto_efficient` | Non-dominated among eligible options on cost, commute and score |
| `robustness_score` | Descriptive rank-and-eligibility stability measure |
