"""Explainable scoring, constraints and Pareto analysis."""

from __future__ import annotations

from datetime import date

from .models import CRITERIA, Listing, Preferences, ScoreRecord


def clamp(value: float, minimum: float = 0.0, maximum: float = 10.0) -> float:
    return min(maximum, max(minimum, value))


def affordability_score(all_in_monthly: float, budget: float) -> float:
    """Score affordability on an asymmetric 0-10 curve.

    - At or below 75% of budget: 10.
    - At exactly 100% of budget: 7.
    - At 120% of budget or above: 0.

    The curve avoids making cost the only objective while still penalizing
    materially over-budget options.
    """

    ratio = all_in_monthly / budget
    if ratio <= 0.75:
        return 10.0
    if ratio <= 1.0:
        return 10.0 - ((ratio - 0.75) / 0.25) * 3.0
    if ratio <= 1.2:
        return 7.0 - ((ratio - 1.0) / 0.2) * 7.0
    return 0.0


def commute_score(commute_minutes: float, max_commute_minutes: float) -> float:
    optimal = max(5.0, min(15.0, max_commute_minutes * 0.4))
    if commute_minutes <= optimal:
        return 10.0
    if commute_minutes <= max_commute_minutes:
        span = max_commute_minutes - optimal
        return 10.0 - ((commute_minutes - optimal) / span) * 5.0
    over_span = max(max_commute_minutes * 0.5, 1.0)
    return clamp(5.0 - ((commute_minutes - max_commute_minutes) / over_span) * 5.0)


def timing_score(available_date: date, target_move_in: date, max_delay_days: int) -> float:
    delta = (available_date - target_move_in).days
    if delta <= 0:
        early_days = abs(delta)
        return clamp(10.0 - min(2.0, early_days / 30.0))
    if max_delay_days == 0:
        return 0.0
    if delta <= max_delay_days:
        return clamp(10.0 * (1.0 - delta / max_delay_days))
    return 0.0


def freshness_score(source_checked_at: date, as_of: date, max_source_age_days: int) -> float:
    age = max(0, (as_of - source_checked_at).days)
    full_credit_days = max(1, max_source_age_days // 3)
    if age <= full_credit_days:
        return 10.0
    if age >= max_source_age_days * 2:
        return 0.0
    return clamp(
        10.0
        * (1.0 - (age - full_credit_days) / (max_source_age_days * 2 - full_credit_days))
    )


def completeness_score(listing: Listing) -> float:
    checks = (
        bool(listing.area),
        listing.sqft is not None,
        listing.bathrooms > 0,
        bool(listing.source_url),
        bool(listing.notes),
        listing.monthly_required_fees_total >= 0,
        listing.monthly_utilities_estimate >= 0,
        listing.one_time_fees >= 0,
    )
    return 10.0 * sum(checks) / len(checks)


def constraint_reasons(listing: Listing, preferences: Preferences, *, as_of: date) -> tuple[str, ...]:
    reasons: list[str] = []
    source_age = max(0, (as_of - listing.source_checked_at).days)
    move_in_delay = (listing.available_date - preferences.target_move_in).days

    if listing.housing_mode not in preferences.allowed_housing_modes:
        reasons.append(f"housing mode {listing.housing_mode!r} is not allowed")
    if listing.safety_score < preferences.min_safety_score:
        reasons.append(
            f"safety {listing.safety_score:.1f} is below minimum {preferences.min_safety_score:.1f}"
        )
    if listing.commute_minutes > preferences.max_commute_minutes:
        reasons.append(
            f"commute {listing.commute_minutes:.0f} min exceeds maximum {preferences.max_commute_minutes:.0f} min"
        )
    if move_in_delay > preferences.max_move_in_delay_days:
        reasons.append(
            f"move-in is {move_in_delay} days late; maximum is {preferences.max_move_in_delay_days} days"
        )
    if listing.cash_needed_at_signing > preferences.max_upfront_cash:
        reasons.append(
            f"signing cash ${listing.cash_needed_at_signing:,.0f} exceeds cap ${preferences.max_upfront_cash:,.0f}"
        )
    if preferences.enforce_budget_cap and listing.all_in_monthly > preferences.max_all_in_monthly:
        reasons.append(
            f"all-in monthly cost ${listing.all_in_monthly:,.0f} exceeds enforced cap ${preferences.max_all_in_monthly:,.0f}"
        )
    if preferences.require_fresh_source and source_age > preferences.max_source_age_days:
        reasons.append(
            f"source age {source_age} days exceeds freshness cap {preferences.max_source_age_days} days"
        )
    return tuple(reasons)


def score_listing(listing: Listing, preferences: Preferences, *, as_of: date) -> ScoreRecord:
    weights = preferences.normalized_weights()
    source_age = max(0, (as_of - listing.source_checked_at).days)
    component_scores = {
        "affordability": affordability_score(listing.all_in_monthly, preferences.max_all_in_monthly),
        "safety": listing.safety_score,
        "commute": commute_score(listing.commute_minutes, preferences.max_commute_minutes),
        "convenience": listing.convenience_score,
        "management": listing.management_score,
        "quiet": listing.quiet_score,
        "space": listing.space_score,
        "application": listing.application_score,
        "timing": timing_score(
            listing.available_date,
            preferences.target_move_in,
            preferences.max_move_in_delay_days,
        ),
        "freshness": freshness_score(
            listing.source_checked_at,
            as_of,
            preferences.max_source_age_days,
        ),
        "completeness": completeness_score(listing),
    }
    contributions = {
        criterion: component_scores[criterion] * weights[criterion]
        for criterion in CRITERIA
    }
    reasons = constraint_reasons(listing, preferences, as_of=as_of)
    total_score = round(sum(contributions.values()), 4)
    return ScoreRecord(
        listing_id=listing.listing_id,
        name=listing.name,
        area=listing.area,
        housing_mode=listing.housing_mode,
        eligible=not reasons,
        constraint_reasons=reasons,
        total_score=total_score,
        component_scores={key: round(value, 4) for key, value in component_scores.items()},
        contributions={key: round(value, 4) for key, value in contributions.items()},
        all_in_monthly=round(listing.all_in_monthly, 2),
        rent_share=round(listing.rent_share, 2),
        cash_needed_at_signing=round(listing.cash_needed_at_signing, 2),
        refundable_deposit=round(listing.refundable_deposit, 2),
        first_year_nonrefundable_cost=round(listing.first_year_nonrefundable_cost, 2),
        first_year_home_currency=round(
            listing.first_year_nonrefundable_cost * preferences.usd_to_home_rate,
            2,
        ),
        source_age_days=source_age,
    )


def rank_listings(
    listings: list[Listing],
    preferences: Preferences,
    *,
    as_of: date,
) -> list[ScoreRecord]:
    records = [score_listing(listing, preferences, as_of=as_of) for listing in listings]
    records.sort(
        key=lambda record: (
            not record.eligible,
            -record.total_score,
            record.all_in_monthly,
            record.listing_id,
        )
    )
    for rank, record in enumerate(records, start=1):
        record.rank = rank

    efficient_ids = pareto_front(records, listings)
    for record in records:
        record.pareto_efficient = record.listing_id in efficient_ids
    return records


def pareto_front(records: list[ScoreRecord], listings: list[Listing]) -> set[str]:
    """Return eligible listings not dominated on cost, commute and total score."""

    listing_by_id = {listing.listing_id: listing for listing in listings}
    candidates = [record for record in records if record.eligible]
    efficient: set[str] = set()

    for candidate in candidates:
        listing = listing_by_id[candidate.listing_id]
        dominated = False
        for other in candidates:
            if other.listing_id == candidate.listing_id:
                continue
            other_listing = listing_by_id[other.listing_id]
            no_worse = (
                other.all_in_monthly <= candidate.all_in_monthly
                and other_listing.commute_minutes <= listing.commute_minutes
                and other.total_score >= candidate.total_score
            )
            strictly_better = (
                other.all_in_monthly < candidate.all_in_monthly
                or other_listing.commute_minutes < listing.commute_minutes
                or other.total_score > candidate.total_score
            )
            if no_worse and strictly_better:
                dominated = True
                break
        if not dominated:
            efficient.add(candidate.listing_id)
    return efficient
