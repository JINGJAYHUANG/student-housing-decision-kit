#!/usr/bin/env python3
"""Verify a generated synthetic demonstration bundle."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

REQUIRED_OUTPUTS = {
    "budget_scenarios.csv",
    "decision.json",
    "decision.sqlite",
    "decision_report.html",
    "ranking.csv",
    "run_manifest.json",
    "score_contributions.csv",
    "sensitivity_matrix.csv",
    "sensitivity_summary.csv",
    "validation.json",
}
EXPECTED_TABLES = {
    "listings",
    "rankings",
    "run_metadata",
    "score_contributions",
    "sensitivity_matrix",
    "sensitivity_summary",
}
EXPECTED_SCENARIOS = 28
EXPECTED_BUDGET_SCENARIOS = 4
EXPECTED_TOP_LISTING = "Scholars Landing"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def verify(output_dir: Path) -> list[str]:
    errors: list[str] = []
    present = {path.name for path in output_dir.iterdir() if path.is_file()}
    missing = sorted(REQUIRED_OUTPUTS - present)
    if missing:
        errors.append(f"missing output files: {', '.join(missing)}")
        return errors

    manifest = json.loads((output_dir / "run_manifest.json").read_text(encoding="utf-8"))
    decision = json.loads((output_dir / "decision.json").read_text(encoding="utf-8"))
    validation = json.loads((output_dir / "validation.json").read_text(encoding="utf-8"))

    if manifest.get("all_data_synthetic") is not True:
        errors.append("manifest does not confirm all_data_synthetic=true")
    if decision.get("metadata", {}).get("all_data_synthetic") is not True:
        errors.append("decision metadata does not confirm all_data_synthetic=true")
    if any(message.get("severity") == "error" for message in validation):
        errors.append("validation.json contains an error")

    listing_count = int(manifest.get("listing_count", 0))
    rankings = decision.get("rankings", [])
    if len(rankings) != listing_count:
        errors.append(
            f"ranking count {len(rankings)} does not match manifest listing_count {listing_count}"
        )

    eligible = [row for row in rankings if row.get("eligible")]
    if not eligible:
        errors.append("demo has no eligible listing")
    elif eligible[0].get("name") != EXPECTED_TOP_LISTING:
        errors.append(
            f"unexpected top listing: {eligible[0].get('name')!r}; expected {EXPECTED_TOP_LISTING!r}"
        )

    output_hashes = manifest.get("output_files", {})
    for filename, expected_hash in output_hashes.items():
        path = output_dir / filename
        if not path.exists():
            errors.append(f"manifest references missing file: {filename}")
            continue
        actual = sha256(path)
        if actual != expected_hash:
            errors.append(f"hash mismatch for {filename}: {actual} != {expected_hash}")

    sensitivity_rows = csv_rows(output_dir / "sensitivity_matrix.csv")
    scenario_names = {row["scenario"] for row in sensitivity_rows}
    if len(scenario_names) != EXPECTED_SCENARIOS:
        errors.append(
            f"expected {EXPECTED_SCENARIOS} sensitivity scenarios, found {len(scenario_names)}"
        )
    if len(sensitivity_rows) != listing_count * EXPECTED_SCENARIOS:
        errors.append(
            "sensitivity matrix row count does not equal listings × scenarios"
        )

    budget_rows = csv_rows(output_dir / "budget_scenarios.csv")
    budget_scenarios = {row["scenario"] for row in budget_rows}
    if len(budget_scenarios) != EXPECTED_BUDGET_SCENARIOS:
        errors.append(
            f"expected {EXPECTED_BUDGET_SCENARIOS} budget scenarios, found {len(budget_scenarios)}"
        )
    if len(budget_rows) != listing_count * EXPECTED_BUDGET_SCENARIOS:
        errors.append("budget scenario row count does not equal listings × scenarios")

    report = (output_dir / "decision_report.html").read_text(encoding="utf-8")
    if "All rows in this demonstration are synthetic" not in report:
        errors.append("HTML report is missing the synthetic-data boundary")
    if manifest.get("input_hash") not in report:
        errors.append("HTML report is missing the input hash")

    connection = sqlite3.connect(output_dir / "decision.sqlite")
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        missing_tables = sorted(EXPECTED_TABLES - tables)
        if missing_tables:
            errors.append(f"SQLite missing tables: {', '.join(missing_tables)}")
        top = connection.execute(
            """
            SELECT l.name
            FROM rankings AS r
            JOIN listings AS l USING (listing_id)
            WHERE r.eligible = 1
            ORDER BY r.rank
            LIMIT 1
            """
        ).fetchone()
        if not top or top[0] != EXPECTED_TOP_LISTING:
            errors.append(f"SQLite top listing is unexpected: {top!r}")
        non_synthetic = connection.execute(
            "SELECT COUNT(*) FROM listings WHERE is_synthetic != 1"
        ).fetchone()[0]
        if non_synthetic:
            errors.append(f"SQLite contains {non_synthetic} non-synthetic row(s)")
    finally:
        connection.close()

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "examples"
        / "synthetic_city"
        / "output",
    )
    args = parser.parse_args(argv)
    output_dir = args.output_dir.resolve()

    if not output_dir.is_dir():
        print(f"Demo output directory not found: {output_dir}", file=sys.stderr)
        return 1

    errors = verify(output_dir)
    if errors:
        print(f"Demo verification failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        "Demo verification passed: files, hashes, synthetic boundary, scenario counts, HTML and SQLite are consistent."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
