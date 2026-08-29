"""Core data models for the decision engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

CRITERIA: tuple[str, ...] = (
    "affordability",
    "safety",
    "commute",
    "convenience",
    "management",
    "quiet",
    "space",
    "application",
    "timing",
    "freshness",
    "completeness",
)

ALLOWED_HOUSING_MODES: tuple[str, ...] = ("solo", "shared")


@dataclass(frozen=True, slots=True)
class Listing:
    listing_id: str
    name: str
    area: str
    housing_mode: str
    bedrooms: float
    bathrooms: float
    sqft: float | None
    monthly_rent_total: float
    monthly_required_fees_total: float
    monthly_utilities_estimate: float
    occupants: int
    commute_minutes: float
    safety_score: float
    convenience_score: float
    management_score: float
    quiet_score: float
    space_score: float
    application_score: float
    available_date: date
    source_checked_at: date
    source_url: str
    is_synthetic: bool
    first_month_required: bool = True
    last_month_required: bool = True
    security_deposit_months: float = 1.0
    broker_fee_months: float = 0.0
    one_time_fees: float = 0.0
    notes: str = ""

    @property
    def rent_share(self) -> float:
        return self.monthly_rent_total / self.occupants

    @property
    def required_fees_share(self) -> float:
        return self.monthly_required_fees_total / self.occupants

    @property
    def utilities_share(self) -> float:
        return self.monthly_utilities_estimate / self.occupants

    @property
    def all_in_monthly(self) -> float:
        return self.rent_share + self.required_fees_share + self.utilities_share

    @property
    def refundable_deposit(self) -> float:
        return self.rent_share * self.security_deposit_months

    @property
    def cash_needed_at_signing(self) -> float:
        rent_months = (
            int(self.first_month_required)
            + int(self.last_month_required)
            + self.security_deposit_months
            + self.broker_fee_months
        )
        return self.rent_share * rent_months + (self.one_time_fees / self.occupants)

    @property
    def first_year_nonrefundable_cost(self) -> float:
        return (
            self.all_in_monthly * 12
            + self.rent_share * self.broker_fee_months
            + (self.one_time_fees / self.occupants)
        )

    def public_dict(self) -> dict[str, Any]:
        return {
            "listing_id": self.listing_id,
            "name": self.name,
            "area": self.area,
            "housing_mode": self.housing_mode,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "sqft": self.sqft,
            "monthly_rent_total": self.monthly_rent_total,
            "monthly_required_fees_total": self.monthly_required_fees_total,
            "monthly_utilities_estimate": self.monthly_utilities_estimate,
            "occupants": self.occupants,
            "commute_minutes": self.commute_minutes,
            "safety_score": self.safety_score,
            "convenience_score": self.convenience_score,
            "management_score": self.management_score,
            "quiet_score": self.quiet_score,
            "space_score": self.space_score,
            "application_score": self.application_score,
            "available_date": self.available_date.isoformat(),
            "source_checked_at": self.source_checked_at.isoformat(),
            "source_url": self.source_url,
            "is_synthetic": self.is_synthetic,
            "first_month_required": self.first_month_required,
            "last_month_required": self.last_month_required,
            "security_deposit_months": self.security_deposit_months,
            "broker_fee_months": self.broker_fee_months,
            "one_time_fees": self.one_time_fees,
            "notes": self.notes,
        }


@dataclass(frozen=True, slots=True)
class Preferences:
    profile_name: str
    target_label: str
    target_move_in: date
    max_move_in_delay_days: int
    max_all_in_monthly: float
    enforce_budget_cap: bool
    max_upfront_cash: float
    min_safety_score: float
    max_commute_minutes: float
    allowed_housing_modes: tuple[str, ...]
    max_source_age_days: int
    require_fresh_source: bool
    home_currency: str
    usd_to_home_rate: float
    sensitivity_delta: float
    weights: dict[str, float]

    def normalized_weights(self) -> dict[str, float]:
        total = sum(self.weights.values())
        if total <= 0:
            raise ValueError("At least one positive weight is required.")
        return {criterion: self.weights[criterion] / total for criterion in CRITERIA}

    def public_dict(self) -> dict[str, Any]:
        return {
            "profile_name": self.profile_name,
            "target_label": self.target_label,
            "target_move_in": self.target_move_in.isoformat(),
            "max_move_in_delay_days": self.max_move_in_delay_days,
            "max_all_in_monthly": self.max_all_in_monthly,
            "enforce_budget_cap": self.enforce_budget_cap,
            "max_upfront_cash": self.max_upfront_cash,
            "min_safety_score": self.min_safety_score,
            "max_commute_minutes": self.max_commute_minutes,
            "allowed_housing_modes": list(self.allowed_housing_modes),
            "max_source_age_days": self.max_source_age_days,
            "require_fresh_source": self.require_fresh_source,
            "home_currency": self.home_currency,
            "usd_to_home_rate": self.usd_to_home_rate,
            "sensitivity_delta": self.sensitivity_delta,
            "weights": self.normalized_weights(),
        }


@dataclass(slots=True)
class ScoreRecord:
    listing_id: str
    name: str
    area: str
    housing_mode: str
    eligible: bool
    constraint_reasons: tuple[str, ...]
    total_score: float
    component_scores: dict[str, float]
    contributions: dict[str, float]
    all_in_monthly: float
    rent_share: float
    cash_needed_at_signing: float
    refundable_deposit: float
    first_year_nonrefundable_cost: float
    first_year_home_currency: float
    source_age_days: int
    rank: int = 0
    pareto_efficient: bool = False

    def public_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "listing_id": self.listing_id,
            "name": self.name,
            "area": self.area,
            "housing_mode": self.housing_mode,
            "eligible": self.eligible,
            "constraint_reasons": list(self.constraint_reasons),
            "total_score": self.total_score,
            "component_scores": dict(self.component_scores),
            "contributions": dict(self.contributions),
            "all_in_monthly": self.all_in_monthly,
            "rent_share": self.rent_share,
            "cash_needed_at_signing": self.cash_needed_at_signing,
            "refundable_deposit": self.refundable_deposit,
            "first_year_nonrefundable_cost": self.first_year_nonrefundable_cost,
            "first_year_home_currency": self.first_year_home_currency,
            "source_age_days": self.source_age_days,
            "pareto_efficient": self.pareto_efficient,
        }


@dataclass(frozen=True, slots=True)
class ValidationMessage:
    severity: str
    code: str
    message: str
    row: int | None = None
    listing_id: str | None = None

    def public_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "row": self.row,
            "listing_id": self.listing_id,
        }


@dataclass(frozen=True, slots=True)
class SensitivitySummary:
    listing_id: str
    name: str
    baseline_rank: int
    best_rank: int
    worst_rank: int
    average_rank: float
    top_one_count: int
    eligible_scenarios: int
    scenario_count: int
    robustness_score: float

    def public_dict(self) -> dict[str, Any]:
        return {
            "listing_id": self.listing_id,
            "name": self.name,
            "baseline_rank": self.baseline_rank,
            "best_rank": self.best_rank,
            "worst_rank": self.worst_rank,
            "average_rank": self.average_rank,
            "top_one_count": self.top_one_count,
            "eligible_scenarios": self.eligible_scenarios,
            "scenario_count": self.scenario_count,
            "robustness_score": self.robustness_score,
        }


@dataclass(frozen=True, slots=True)
class SensitivityMatrixRow:
    scenario: str
    listing_id: str
    rank: int
    eligible: bool
    total_score: float

    def public_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "listing_id": self.listing_id,
            "rank": self.rank,
            "eligible": self.eligible,
            "total_score": self.total_score,
        }


@dataclass(frozen=True, slots=True)
class RunMetadata:
    generated_at: str
    as_of: str
    input_hash: str
    package_version: str
    listing_count: int
    eligible_count: int
    all_data_synthetic: bool
    output_files: dict[str, str] = field(default_factory=dict)

    def public_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "as_of": self.as_of,
            "input_hash": self.input_hash,
            "package_version": self.package_version,
            "listing_count": self.listing_count,
            "eligible_count": self.eligible_count,
            "all_data_synthetic": self.all_data_synthetic,
            "output_files": dict(self.output_files),
        }
