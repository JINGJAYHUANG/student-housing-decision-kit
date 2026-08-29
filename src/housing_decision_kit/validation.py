"""Dataset and configuration validation."""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Iterable
from urllib.parse import urlparse

from .models import (
    ALLOWED_HOUSING_MODES,
    CRITERIA,
    Listing,
    Preferences,
    ValidationMessage,
)


def validate_dataset(
    listings: Iterable[Listing],
    preferences: Preferences,
    *,
    as_of: date,
) -> list[ValidationMessage]:
    listing_list = list(listings)
    messages = validate_preferences(preferences)

    counts = Counter(listing.listing_id for listing in listing_list)
    for listing_id, count in sorted(counts.items()):
        if count > 1:
            messages.append(
                ValidationMessage(
                    "error",
                    "duplicate_listing_id",
                    f"Listing ID {listing_id!r} occurs {count} times.",
                    listing_id=listing_id,
                )
            )

    if not listing_list:
        messages.append(
            ValidationMessage("error", "empty_dataset", "At least one listing is required.")
        )
        return messages

    for index, listing in enumerate(listing_list, start=2):
        messages.extend(validate_listing(listing, as_of=as_of, row=index))

    if any(not listing.is_synthetic for listing in listing_list):
        messages.append(
            ValidationMessage(
                "warning",
                "contains_non_synthetic_data",
                "Dataset contains rows not marked synthetic. Confirm publication rights and remove personal or confidential details before publishing.",
            )
        )
    else:
        messages.append(
            ValidationMessage(
                "info",
                "all_data_synthetic",
                "Every listing is explicitly marked as synthetic.",
            )
        )

    return messages


def validate_preferences(preferences: Preferences) -> list[ValidationMessage]:
    messages: list[ValidationMessage] = []
    keys = set(preferences.weights)
    expected = set(CRITERIA)
    missing = sorted(expected - keys)
    extra = sorted(keys - expected)
    if missing:
        messages.append(
            ValidationMessage(
                "error",
                "missing_weights",
                f"Missing criteria weights: {', '.join(missing)}.",
            )
        )
    if extra:
        messages.append(
            ValidationMessage(
                "error",
                "unknown_weights",
                f"Unknown criteria weights: {', '.join(extra)}.",
            )
        )

    for criterion, value in preferences.weights.items():
        if value < 0:
            messages.append(
                ValidationMessage(
                    "error",
                    "negative_weight",
                    f"Weight {criterion!r} cannot be negative.",
                )
            )
    if sum(preferences.weights.values()) <= 0:
        messages.append(
            ValidationMessage("error", "zero_weights", "Weight total must be positive.")
        )

    if preferences.max_all_in_monthly <= 0:
        messages.append(
            ValidationMessage("error", "invalid_budget", "max_all_in_monthly must be positive.")
        )
    if preferences.max_upfront_cash <= 0:
        messages.append(
            ValidationMessage("error", "invalid_upfront_cap", "max_upfront_cash must be positive.")
        )
    if not 0 <= preferences.min_safety_score <= 10:
        messages.append(
            ValidationMessage("error", "invalid_safety_floor", "min_safety_score must be between 0 and 10.")
        )
    if preferences.max_commute_minutes <= 0:
        messages.append(
            ValidationMessage("error", "invalid_commute_cap", "max_commute_minutes must be positive.")
        )
    if preferences.max_move_in_delay_days < 0:
        messages.append(
            ValidationMessage("error", "invalid_move_in_delay", "max_move_in_delay_days cannot be negative.")
        )
    if preferences.max_source_age_days <= 0:
        messages.append(
            ValidationMessage("error", "invalid_source_age", "max_source_age_days must be positive.")
        )
    if preferences.usd_to_home_rate <= 0:
        messages.append(
            ValidationMessage("error", "invalid_fx", "usd_to_home_rate must be positive.")
        )
    if not 0 < preferences.sensitivity_delta < 1:
        messages.append(
            ValidationMessage(
                "error",
                "invalid_sensitivity_delta",
                "sensitivity_delta must be between 0 and 1.",
            )
        )

    invalid_modes = sorted(set(preferences.allowed_housing_modes) - set(ALLOWED_HOUSING_MODES))
    if invalid_modes:
        messages.append(
            ValidationMessage(
                "error",
                "invalid_allowed_modes",
                f"Unsupported housing modes: {', '.join(invalid_modes)}.",
            )
        )
    if not preferences.allowed_housing_modes:
        messages.append(
            ValidationMessage("error", "empty_allowed_modes", "At least one housing mode must be allowed.")
        )

    weight_total = sum(preferences.weights.values())
    if weight_total > 0 and abs(weight_total - 1.0) > 1e-9:
        messages.append(
            ValidationMessage(
                "info",
                "weights_normalized",
                f"Weights sum to {weight_total:.6f}; the engine will normalize them to 1.0.",
            )
        )

    return messages


def validate_listing(listing: Listing, *, as_of: date, row: int) -> list[ValidationMessage]:
    messages: list[ValidationMessage] = []
    prefix = {"row": row, "listing_id": listing.listing_id}

    if not listing.listing_id:
        messages.append(ValidationMessage("error", "missing_listing_id", "listing_id is required.", **prefix))
    if not listing.name:
        messages.append(ValidationMessage("error", "missing_name", "name is required.", **prefix))
    if listing.housing_mode not in ALLOWED_HOUSING_MODES:
        messages.append(
            ValidationMessage(
                "error",
                "invalid_housing_mode",
                f"housing_mode must be one of {ALLOWED_HOUSING_MODES}.",
                **prefix,
            )
        )
    if listing.occupants <= 0:
        messages.append(ValidationMessage("error", "invalid_occupants", "occupants must be positive.", **prefix))
    if listing.monthly_rent_total <= 0:
        messages.append(ValidationMessage("error", "invalid_rent", "monthly_rent_total must be positive.", **prefix))
    for field_name, value in (
        ("monthly_required_fees_total", listing.monthly_required_fees_total),
        ("monthly_utilities_estimate", listing.monthly_utilities_estimate),
        ("security_deposit_months", listing.security_deposit_months),
        ("broker_fee_months", listing.broker_fee_months),
        ("one_time_fees", listing.one_time_fees),
    ):
        if value < 0:
            messages.append(
                ValidationMessage("error", "negative_cost", f"{field_name} cannot be negative.", **prefix)
            )

    for field_name, score in (
        ("safety_score", listing.safety_score),
        ("convenience_score", listing.convenience_score),
        ("management_score", listing.management_score),
        ("quiet_score", listing.quiet_score),
        ("space_score", listing.space_score),
        ("application_score", listing.application_score),
    ):
        if not 0 <= score <= 10:
            messages.append(
                ValidationMessage(
                    "error",
                    "score_out_of_range",
                    f"{field_name} must be between 0 and 10.",
                    **prefix,
                )
            )

    if listing.commute_minutes < 0:
        messages.append(ValidationMessage("error", "negative_commute", "commute_minutes cannot be negative.", **prefix))
    if listing.bedrooms < 0 or listing.bathrooms <= 0:
        messages.append(
            ValidationMessage("error", "invalid_layout", "bedrooms must be nonnegative and bathrooms positive.", **prefix)
        )
    if listing.sqft is not None and listing.sqft <= 0:
        messages.append(ValidationMessage("error", "invalid_sqft", "sqft must be positive when supplied.", **prefix))

    if listing.source_checked_at > as_of:
        messages.append(
            ValidationMessage(
                "error",
                "future_source_date",
                "source_checked_at cannot be after the analysis as-of date.",
                **prefix,
            )
        )

    if listing.available_date < as_of:
        messages.append(
            ValidationMessage(
                "warning",
                "availability_before_as_of",
                "available_date is before the analysis as-of date; confirm that the record represents a still-open listing.",
                **prefix,
            )
        )

    if not listing.source_url:
        messages.append(
            ValidationMessage("warning", "missing_source", "source_url is blank.", **prefix)
        )
    else:
        parsed = urlparse(listing.source_url)
        if parsed.scheme not in {"http", "https", "synthetic"}:
            messages.append(
                ValidationMessage(
                    "warning",
                    "unusual_source_scheme",
                    f"source_url uses unsupported or unusual scheme {parsed.scheme!r}.",
                    **prefix,
                )
            )
        if listing.is_synthetic and parsed.scheme != "synthetic":
            messages.append(
                ValidationMessage(
                    "warning",
                    "synthetic_row_with_external_url",
                    "Synthetic rows should normally use a synthetic:// source URI to avoid implying a real listing.",
                    **prefix,
                )
            )

    return messages


def has_errors(messages: Iterable[ValidationMessage]) -> bool:
    return any(message.severity == "error" for message in messages)
