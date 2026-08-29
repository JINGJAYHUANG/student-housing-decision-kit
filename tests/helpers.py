from __future__ import annotations

from datetime import date

from housing_decision_kit.models import Listing, Preferences


def make_listing(**overrides: object) -> Listing:
    payload: dict[str, object] = {
        "listing_id": "L-001",
        "name": "Example House",
        "area": "Campus District",
        "housing_mode": "solo",
        "bedrooms": 1.0,
        "bathrooms": 1.0,
        "sqft": 650.0,
        "monthly_rent_total": 3000.0,
        "monthly_required_fees_total": 150.0,
        "monthly_utilities_estimate": 150.0,
        "occupants": 1,
        "commute_minutes": 15.0,
        "safety_score": 8.5,
        "convenience_score": 8.0,
        "management_score": 8.0,
        "quiet_score": 8.0,
        "space_score": 8.0,
        "application_score": 8.0,
        "available_date": date(2026, 8, 20),
        "source_checked_at": date(2026, 6, 10),
        "source_url": "synthetic://listing/L-001",
        "is_synthetic": True,
        "first_month_required": True,
        "last_month_required": True,
        "security_deposit_months": 1.0,
        "broker_fee_months": 0.0,
        "one_time_fees": 300.0,
        "notes": "Synthetic test fixture.",
    }
    payload.update(overrides)
    return Listing(**payload)  # type: ignore[arg-type]


def make_preferences(**overrides: object) -> Preferences:
    weights = {
        "affordability": 0.16,
        "safety": 0.17,
        "commute": 0.15,
        "convenience": 0.09,
        "management": 0.10,
        "quiet": 0.10,
        "space": 0.06,
        "application": 0.07,
        "timing": 0.05,
        "freshness": 0.03,
        "completeness": 0.02,
    }
    payload: dict[str, object] = {
        "profile_name": "Test profile",
        "target_label": "Test campus",
        "target_move_in": date(2026, 8, 20),
        "max_move_in_delay_days": 21,
        "max_all_in_monthly": 3800.0,
        "enforce_budget_cap": False,
        "max_upfront_cash": 12500.0,
        "min_safety_score": 7.5,
        "max_commute_minutes": 35.0,
        "allowed_housing_modes": ("solo", "shared"),
        "max_source_age_days": 90,
        "require_fresh_source": True,
        "home_currency": "CNY",
        "usd_to_home_rate": 6.9,
        "sensitivity_delta": 0.25,
        "weights": weights,
    }
    payload.update(overrides)
    return Preferences(**payload)  # type: ignore[arg-type]
