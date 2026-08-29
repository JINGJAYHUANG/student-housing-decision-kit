"""Input/output helpers with deterministic serialization."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .models import CRITERIA, Listing, Preferences


TRUE_VALUES = {"1", "true", "yes", "y"}
FALSE_VALUES = {"0", "false", "no", "n"}


def parse_bool(value: Any, *, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ValueError(f"{field_name} must be a boolean value, got {value!r}.")


def parse_date(value: Any, *, field_name: str) -> date:
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError as exc:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format, got {value!r}.") from exc


def parse_float(value: Any, *, field_name: str, allow_blank: bool = False) -> float | None:
    if value is None or str(value).strip() == "":
        if allow_blank:
            return None
        raise ValueError(f"{field_name} is required.")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric, got {value!r}.") from exc


def parse_int(value: Any, *, field_name: str) -> int:
    if value is None or str(value).strip() == "":
        raise ValueError(f"{field_name} is required.")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer, got {value!r}.") from exc
    return result


def load_preferences(path: str | Path) -> Preferences:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    raw_weights = payload.get("weights", {})
    weights = {criterion: float(raw_weights.get(criterion, 0.0)) for criterion in CRITERIA}

    return Preferences(
        profile_name=str(payload.get("profile_name", "Anonymous student profile")).strip(),
        target_label=str(payload.get("target_label", "Campus center")).strip(),
        target_move_in=parse_date(payload["target_move_in"], field_name="target_move_in"),
        max_move_in_delay_days=parse_int(
            payload.get("max_move_in_delay_days", 21),
            field_name="max_move_in_delay_days",
        ),
        max_all_in_monthly=float(payload["max_all_in_monthly"]),
        enforce_budget_cap=parse_bool(
            payload.get("enforce_budget_cap", False),
            field_name="enforce_budget_cap",
        ),
        max_upfront_cash=float(payload["max_upfront_cash"]),
        min_safety_score=float(payload["min_safety_score"]),
        max_commute_minutes=float(payload["max_commute_minutes"]),
        allowed_housing_modes=tuple(
            str(item).strip().lower() for item in payload.get("allowed_housing_modes", ["solo", "shared"])
        ),
        max_source_age_days=parse_int(
            payload.get("max_source_age_days", 90),
            field_name="max_source_age_days",
        ),
        require_fresh_source=parse_bool(
            payload.get("require_fresh_source", True),
            field_name="require_fresh_source",
        ),
        home_currency=str(payload.get("home_currency", "USD")).strip().upper(),
        usd_to_home_rate=float(payload.get("usd_to_home_rate", 1.0)),
        sensitivity_delta=float(payload.get("sensitivity_delta", 0.25)),
        weights=weights,
    )


def load_listings(path: str | Path) -> list[Listing]:
    source = Path(path)
    listings: list[Listing] = []
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("Listing CSV has no header row.")
        for row_number, row in enumerate(reader, start=2):
            try:
                listings.append(_listing_from_row(row))
            except (KeyError, ValueError) as exc:
                raise ValueError(f"Invalid listing row {row_number}: {exc}") from exc
    return listings


def _listing_from_row(row: Mapping[str, Any]) -> Listing:
    return Listing(
        listing_id=str(row["listing_id"]).strip(),
        name=str(row["name"]).strip(),
        area=str(row["area"]).strip(),
        housing_mode=str(row["housing_mode"]).strip().lower(),
        bedrooms=float(row["bedrooms"]),
        bathrooms=float(row["bathrooms"]),
        sqft=parse_float(row.get("sqft"), field_name="sqft", allow_blank=True),
        monthly_rent_total=float(row["monthly_rent_total"]),
        monthly_required_fees_total=float(row.get("monthly_required_fees_total", 0) or 0),
        monthly_utilities_estimate=float(row.get("monthly_utilities_estimate", 0) or 0),
        occupants=int(row["occupants"]),
        commute_minutes=float(row["commute_minutes"]),
        safety_score=float(row["safety_score"]),
        convenience_score=float(row["convenience_score"]),
        management_score=float(row["management_score"]),
        quiet_score=float(row["quiet_score"]),
        space_score=float(row["space_score"]),
        application_score=float(row["application_score"]),
        available_date=parse_date(row["available_date"], field_name="available_date"),
        source_checked_at=parse_date(row["source_checked_at"], field_name="source_checked_at"),
        source_url=str(row.get("source_url", "")).strip(),
        is_synthetic=parse_bool(row.get("is_synthetic", False), field_name="is_synthetic"),
        first_month_required=parse_bool(
            row.get("first_month_required", True),
            field_name="first_month_required",
        ),
        last_month_required=parse_bool(
            row.get("last_month_required", True),
            field_name="last_month_required",
        ),
        security_deposit_months=float(row.get("security_deposit_months", 1) or 0),
        broker_fee_months=float(row.get("broker_fee_months", 0) or 0),
        one_time_fees=float(row.get("one_time_fees", 0) or 0),
        notes=str(row.get("notes", "")).strip(),
    )


def input_hash(paths: Sequence[str | Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(Path(item) for item in paths):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path: str | Path, payload: Any) -> None:
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_csv(path: str | Path, rows: Iterable[Mapping[str, Any]], fieldnames: Sequence[str]) -> None:
    destination = Path(path)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in fieldnames})


def _csv_value(value: Any) -> Any:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value
