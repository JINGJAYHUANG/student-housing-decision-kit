"""Budget and stress-scenario calculations."""

from __future__ import annotations

from .models import Listing, Preferences


def build_budget_scenarios(
    listings: list[Listing],
    preferences: Preferences,
) -> list[dict[str, float | str]]:
    scenarios = (
        ("base", 1.0, 1.0, 1.0),
        ("fees_and_utilities_plus_20pct", 1.0, 1.2, 1.0),
        ("rent_plus_5pct", 1.05, 1.0, 1.0),
        ("home_currency_weakens_5pct", 1.0, 1.0, 1.05),
    )
    rows: list[dict[str, float | str]] = []
    for listing in listings:
        for scenario_name, rent_factor, operating_factor, fx_factor in scenarios:
            rent_share = listing.rent_share * rent_factor
            recurring_share = (
                listing.required_fees_share + listing.utilities_share
            ) * operating_factor
            monthly = rent_share + recurring_share
            signing = (
                rent_share
                * (
                    int(listing.first_month_required)
                    + int(listing.last_month_required)
                    + listing.security_deposit_months
                    + listing.broker_fee_months
                )
                + listing.one_time_fees / listing.occupants
            )
            first_year = (
                monthly * 12
                + rent_share * listing.broker_fee_months
                + listing.one_time_fees / listing.occupants
            )
            rows.append(
                {
                    "scenario": scenario_name,
                    "listing_id": listing.listing_id,
                    "name": listing.name,
                    "monthly_usd": round(monthly, 2),
                    "signing_cash_usd": round(signing, 2),
                    "first_year_usd": round(first_year, 2),
                    "first_year_home_currency": round(
                        first_year * preferences.usd_to_home_rate * fx_factor,
                        2,
                    ),
                    "home_currency": preferences.home_currency,
                }
            )
    return rows
