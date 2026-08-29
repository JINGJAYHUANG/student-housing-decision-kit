"""Command-line interface for validation and evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .budget import build_budget_scenarios
from .io import file_sha256, input_hash, load_listings, load_preferences, write_csv, write_json
from .models import CRITERIA, RunMetadata
from .report import render_report
from .scoring import rank_listings
from .sensitivity import run_sensitivity
from .sqlite_export import export_sqlite
from .validation import has_errors, validate_dataset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="housing-decision",
        description="Explainable, privacy-conscious student housing decision support.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate inputs without ranking listings.")
    _add_common_inputs(validate_parser)
    validate_parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional path for machine-readable validation messages.",
    )

    evaluate_parser = subparsers.add_parser("evaluate", help="Rank listings and generate an auditable report bundle.")
    _add_common_inputs(evaluate_parser)
    evaluate_parser.add_argument("--output-dir", type=Path, required=True)
    evaluate_parser.add_argument(
        "--generated-at",
        help="Optional fixed ISO-8601 timestamp for reproducible examples.",
    )
    evaluate_parser.add_argument(
        "--no-sqlite",
        action="store_true",
        help="Skip creation of decision.sqlite.",
    )
    return parser


def _add_common_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--listings", type=Path, required=True, help="Listing CSV path.")
    parser.add_argument("--preferences", type=Path, required=True, help="Preference JSON path.")
    parser.add_argument(
        "--as-of",
        required=True,
        help="Analysis date in YYYY-MM-DD format. Required to make freshness explicit.",
    )


def parse_as_of(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"--as-of must use YYYY-MM-DD format, got {value!r}.") from exc


def parse_generated_at(value: str | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    normalized = value.strip()
    try:
        datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SystemExit(f"--generated-at must be an ISO-8601 timestamp, got {value!r}.") from exc
    return normalized


def run_validate(args: argparse.Namespace) -> int:
    as_of = parse_as_of(args.as_of)
    listings = load_listings(args.listings)
    preferences = load_preferences(args.preferences)
    messages = validate_dataset(listings, preferences, as_of=as_of)
    _print_validation(messages)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        write_json(args.json_output, [message.public_dict() for message in messages])
    return 2 if has_errors(messages) else 0


def run_evaluate(args: argparse.Namespace) -> int:
    as_of = parse_as_of(args.as_of)
    generated_at = parse_generated_at(args.generated_at)
    listings = load_listings(args.listings)
    preferences = load_preferences(args.preferences)
    messages = validate_dataset(listings, preferences, as_of=as_of)

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "validation.json", [message.public_dict() for message in messages])
    _print_validation(messages)
    if has_errors(messages):
        print("Evaluation stopped because validation errors were found.", file=sys.stderr)
        return 2

    source_hash = input_hash([args.listings, args.preferences])
    records = rank_listings(listings, preferences, as_of=as_of)
    sensitivity, sensitivity_matrix = run_sensitivity(
        listings,
        preferences,
        as_of=as_of,
    )
    budget_rows = build_budget_scenarios(listings, preferences)

    ranking_rows = [_ranking_csv_row(record) for record in records]
    ranking_fields = [
        "rank",
        "listing_id",
        "name",
        "area",
        "housing_mode",
        "eligible",
        "pareto_efficient",
        "total_score",
        "all_in_monthly",
        "rent_share",
        "cash_needed_at_signing",
        "refundable_deposit",
        "first_year_nonrefundable_cost",
        "first_year_home_currency",
        "source_age_days",
        "constraint_reasons",
        *[f"score_{criterion}" for criterion in CRITERIA],
    ]
    write_csv(output_dir / "ranking.csv", ranking_rows, ranking_fields)

    contribution_rows = []
    for record in records:
        for criterion in CRITERIA:
            contribution_rows.append(
                {
                    "listing_id": record.listing_id,
                    "name": record.name,
                    "criterion": criterion,
                    "component_score": record.component_scores[criterion],
                    "normalized_weight": preferences.normalized_weights()[criterion],
                    "weighted_contribution": record.contributions[criterion],
                }
            )
    write_csv(
        output_dir / "score_contributions.csv",
        contribution_rows,
        [
            "listing_id",
            "name",
            "criterion",
            "component_score",
            "normalized_weight",
            "weighted_contribution",
        ],
    )

    write_csv(
        output_dir / "sensitivity_summary.csv",
        [row.public_dict() for row in sensitivity],
        [
            "listing_id",
            "name",
            "baseline_rank",
            "best_rank",
            "worst_rank",
            "average_rank",
            "top_one_count",
            "eligible_scenarios",
            "scenario_count",
            "robustness_score",
        ],
    )
    write_csv(
        output_dir / "sensitivity_matrix.csv",
        [row.public_dict() for row in sensitivity_matrix],
        ["scenario", "listing_id", "rank", "eligible", "total_score"],
    )
    write_csv(
        output_dir / "budget_scenarios.csv",
        budget_rows,
        [
            "scenario",
            "listing_id",
            "name",
            "monthly_usd",
            "signing_cash_usd",
            "first_year_usd",
            "first_year_home_currency",
            "home_currency",
        ],
    )

    eligible_count = sum(record.eligible for record in records)
    all_synthetic = all(listing.is_synthetic for listing in listings)
    base_metadata: dict[str, Any] = {
        "generated_at": generated_at,
        "as_of": as_of.isoformat(),
        "input_hash": source_hash,
        "package_version": __version__,
        "listing_count": len(listings),
        "eligible_count": eligible_count,
        "all_data_synthetic": all_synthetic,
    }

    decision_payload = {
        "metadata": base_metadata,
        "preferences": preferences.public_dict(),
        "rankings": [record.public_dict() for record in records],
        "sensitivity": [row.public_dict() for row in sensitivity],
    }
    write_json(output_dir / "decision.json", decision_payload)

    render_report(
        output_dir / "decision_report.html",
        listings=listings,
        records=records,
        preferences=preferences,
        sensitivity=sensitivity,
        generated_at=generated_at,
        as_of=as_of.isoformat(),
        input_hash=source_hash,
    )

    if not args.no_sqlite:
        export_sqlite(
            output_dir / "decision.sqlite",
            listings=listings,
            records=records,
            sensitivity=sensitivity,
            sensitivity_matrix=sensitivity_matrix,
            metadata=base_metadata,
        )

    output_hashes = {
        path.name: file_sha256(path)
        for path in sorted(output_dir.iterdir())
        if path.is_file() and path.name != "run_manifest.json"
    }
    metadata = RunMetadata(
        generated_at=generated_at,
        as_of=as_of.isoformat(),
        input_hash=source_hash,
        package_version=__version__,
        listing_count=len(listings),
        eligible_count=eligible_count,
        all_data_synthetic=all_synthetic,
        output_files=output_hashes,
    )
    write_json(output_dir / "run_manifest.json", metadata.public_dict())

    top = next((record for record in records if record.eligible), None)
    print(f"Generated {len(output_hashes) + 1} files in {output_dir}")
    if top:
        print(
            f"Top eligible option: {top.name} | score {top.total_score:.2f} | "
            f"all-in ${top.all_in_monthly:,.0f}/month"
        )
    else:
        print("No listing passed all hard constraints.")
    return 0


def _ranking_csv_row(record: Any) -> dict[str, Any]:
    row = {
        "rank": record.rank,
        "listing_id": record.listing_id,
        "name": record.name,
        "area": record.area,
        "housing_mode": record.housing_mode,
        "eligible": record.eligible,
        "pareto_efficient": record.pareto_efficient,
        "total_score": record.total_score,
        "all_in_monthly": record.all_in_monthly,
        "rent_share": record.rent_share,
        "cash_needed_at_signing": record.cash_needed_at_signing,
        "refundable_deposit": record.refundable_deposit,
        "first_year_nonrefundable_cost": record.first_year_nonrefundable_cost,
        "first_year_home_currency": record.first_year_home_currency,
        "source_age_days": record.source_age_days,
        "constraint_reasons": list(record.constraint_reasons),
    }
    for criterion in CRITERIA:
        row[f"score_{criterion}"] = record.component_scores[criterion]
    return row


def _print_validation(messages: list[Any]) -> None:
    counts = {"error": 0, "warning": 0, "info": 0}
    for message in messages:
        counts[message.severity] = counts.get(message.severity, 0) + 1
        location = f" row={message.row}" if message.row is not None else ""
        listing = f" listing={message.listing_id}" if message.listing_id else ""
        print(
            f"[{message.severity.upper()}] {message.code}:{location}{listing} {message.message}"
        )
    print(
        "Validation summary: "
        f"{counts.get('error', 0)} error(s), "
        f"{counts.get('warning', 0)} warning(s), "
        f"{counts.get('info', 0)} info message(s)."
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            return run_validate(args)
        if args.command == "evaluate":
            return run_evaluate(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Input or processing error: {exc}", file=sys.stderr)
        return 2
    parser.error(f"Unknown command {args.command!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
