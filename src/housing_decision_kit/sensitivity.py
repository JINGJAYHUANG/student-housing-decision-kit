"""Sensitivity and stress-scenario analysis."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from statistics import mean

from .models import (
    CRITERIA,
    Listing,
    Preferences,
    SensitivityMatrixRow,
    SensitivitySummary,
)
from .scoring import rank_listings


def _normalize(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    return {key: value / total for key, value in weights.items()}


def build_scenarios(preferences: Preferences) -> list[tuple[str, Preferences]]:
    scenarios: list[tuple[str, Preferences]] = [("baseline", preferences)]
    delta = preferences.sensitivity_delta
    baseline_weights = preferences.normalized_weights()

    for criterion in CRITERIA:
        low = dict(baseline_weights)
        low[criterion] *= 1.0 - delta
        scenarios.append(
            (
                f"weight_{criterion}_minus_{int(delta * 100)}pct",
                replace(preferences, weights=_normalize(low)),
            )
        )
        high = dict(baseline_weights)
        high[criterion] *= 1.0 + delta
        scenarios.append(
            (
                f"weight_{criterion}_plus_{int(delta * 100)}pct",
                replace(preferences, weights=_normalize(high)),
            )
        )

    scenarios.extend(
        [
            (
                "budget_minus_10pct",
                replace(preferences, max_all_in_monthly=preferences.max_all_in_monthly * 0.9),
            ),
            (
                "budget_plus_10pct",
                replace(preferences, max_all_in_monthly=preferences.max_all_in_monthly * 1.1),
            ),
            (
                "commute_cap_minus_20pct",
                replace(preferences, max_commute_minutes=preferences.max_commute_minutes * 0.8),
            ),
            (
                "safety_floor_plus_1",
                replace(preferences, min_safety_score=min(10.0, preferences.min_safety_score + 1.0)),
            ),
            (
                "move_in_tolerance_halved",
                replace(
                    preferences,
                    max_move_in_delay_days=max(0, preferences.max_move_in_delay_days // 2),
                ),
            ),
        ]
    )
    return scenarios


def run_sensitivity(
    listings: list[Listing],
    preferences: Preferences,
    *,
    as_of: date,
) -> tuple[list[SensitivitySummary], list[SensitivityMatrixRow]]:
    scenarios = build_scenarios(preferences)
    matrix: list[SensitivityMatrixRow] = []
    baseline_records = rank_listings(listings, preferences, as_of=as_of)
    baseline_rank = {record.listing_id: record.rank for record in baseline_records}
    names = {record.listing_id: record.name for record in baseline_records}

    ranks_by_listing: dict[str, list[int]] = {listing.listing_id: [] for listing in listings}
    eligible_by_listing: dict[str, int] = {listing.listing_id: 0 for listing in listings}
    top_one_by_listing: dict[str, int] = {listing.listing_id: 0 for listing in listings}

    for scenario_name, scenario_preferences in scenarios:
        records = rank_listings(listings, scenario_preferences, as_of=as_of)
        eligible_records = [record for record in records if record.eligible]
        top_eligible_id = eligible_records[0].listing_id if eligible_records else None
        for record in records:
            ranks_by_listing[record.listing_id].append(record.rank)
            eligible_by_listing[record.listing_id] += int(record.eligible)
            if record.listing_id == top_eligible_id:
                top_one_by_listing[record.listing_id] += 1
            matrix.append(
                SensitivityMatrixRow(
                    scenario=scenario_name,
                    listing_id=record.listing_id,
                    rank=record.rank,
                    eligible=record.eligible,
                    total_score=record.total_score,
                )
            )

    listing_count = len(listings)
    scenario_count = len(scenarios)
    summaries: list[SensitivitySummary] = []
    for listing_id, ranks in ranks_by_listing.items():
        best = min(ranks)
        worst = max(ranks)
        eligible_scenarios = eligible_by_listing[listing_id]
        eligible_share = eligible_scenarios / scenario_count
        rank_stability = 1.0 if listing_count <= 1 else 1.0 - (worst - best) / (listing_count - 1)
        robustness = 10.0 * max(0.0, rank_stability) * eligible_share
        summaries.append(
            SensitivitySummary(
                listing_id=listing_id,
                name=names[listing_id],
                baseline_rank=baseline_rank[listing_id],
                best_rank=best,
                worst_rank=worst,
                average_rank=round(mean(ranks), 3),
                top_one_count=top_one_by_listing[listing_id],
                eligible_scenarios=eligible_scenarios,
                scenario_count=scenario_count,
                robustness_score=round(robustness, 3),
            )
        )

    summaries.sort(key=lambda item: (item.baseline_rank, -item.robustness_score, item.listing_id))
    matrix.sort(key=lambda item: (item.scenario, item.rank, item.listing_id))
    return summaries, matrix
