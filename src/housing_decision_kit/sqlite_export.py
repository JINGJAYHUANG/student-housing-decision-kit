"""SQLite export for downstream analysis and portfolio SQL examples."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable, Mapping

from .models import Listing, ScoreRecord, SensitivityMatrixRow, SensitivitySummary


def export_sqlite(
    path: str | Path,
    *,
    listings: list[Listing],
    records: list[ScoreRecord],
    sensitivity: list[SensitivitySummary],
    sensitivity_matrix: list[SensitivityMatrixRow],
    metadata: Mapping[str, object],
) -> None:
    destination = Path(path)
    if destination.exists():
        destination.unlink()

    connection = sqlite3.connect(destination)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        _create_schema(connection)
        _insert_listings(connection, listings)
        _insert_rankings(connection, records)
        _insert_contributions(connection, records)
        _insert_sensitivity(connection, sensitivity)
        _insert_sensitivity_matrix(connection, sensitivity_matrix)
        connection.executemany(
            "INSERT INTO run_metadata(key, value) VALUES (?, ?)",
            [
                (str(key), json.dumps(value, ensure_ascii=False, sort_keys=True))
                for key, value in sorted(metadata.items())
            ],
        )
        connection.commit()
    finally:
        connection.close()


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE listings (
            listing_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            area TEXT NOT NULL,
            housing_mode TEXT NOT NULL,
            bedrooms REAL NOT NULL,
            bathrooms REAL NOT NULL,
            sqft REAL,
            monthly_rent_total REAL NOT NULL,
            monthly_required_fees_total REAL NOT NULL,
            monthly_utilities_estimate REAL NOT NULL,
            occupants INTEGER NOT NULL,
            commute_minutes REAL NOT NULL,
            safety_score REAL NOT NULL,
            convenience_score REAL NOT NULL,
            management_score REAL NOT NULL,
            quiet_score REAL NOT NULL,
            space_score REAL NOT NULL,
            application_score REAL NOT NULL,
            available_date TEXT NOT NULL,
            source_checked_at TEXT NOT NULL,
            source_url TEXT NOT NULL,
            is_synthetic INTEGER NOT NULL,
            notes TEXT NOT NULL
        );

        CREATE TABLE rankings (
            listing_id TEXT PRIMARY KEY REFERENCES listings(listing_id),
            rank INTEGER NOT NULL,
            eligible INTEGER NOT NULL,
            constraint_reasons TEXT NOT NULL,
            total_score REAL NOT NULL,
            all_in_monthly REAL NOT NULL,
            rent_share REAL NOT NULL,
            cash_needed_at_signing REAL NOT NULL,
            refundable_deposit REAL NOT NULL,
            first_year_nonrefundable_cost REAL NOT NULL,
            first_year_home_currency REAL NOT NULL,
            source_age_days INTEGER NOT NULL,
            pareto_efficient INTEGER NOT NULL
        );

        CREATE TABLE score_contributions (
            listing_id TEXT NOT NULL REFERENCES listings(listing_id),
            criterion TEXT NOT NULL,
            component_score REAL NOT NULL,
            contribution REAL NOT NULL,
            PRIMARY KEY (listing_id, criterion)
        );

        CREATE TABLE sensitivity_summary (
            listing_id TEXT PRIMARY KEY REFERENCES listings(listing_id),
            baseline_rank INTEGER NOT NULL,
            best_rank INTEGER NOT NULL,
            worst_rank INTEGER NOT NULL,
            average_rank REAL NOT NULL,
            top_one_count INTEGER NOT NULL,
            eligible_scenarios INTEGER NOT NULL,
            scenario_count INTEGER NOT NULL,
            robustness_score REAL NOT NULL
        );

        CREATE TABLE sensitivity_matrix (
            scenario TEXT NOT NULL,
            listing_id TEXT NOT NULL REFERENCES listings(listing_id),
            rank INTEGER NOT NULL,
            eligible INTEGER NOT NULL,
            total_score REAL NOT NULL,
            PRIMARY KEY (scenario, listing_id)
        );

        CREATE TABLE run_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE INDEX idx_rankings_rank ON rankings(rank);
        CREATE INDEX idx_rankings_eligible ON rankings(eligible);
        CREATE INDEX idx_sensitivity_robustness ON sensitivity_summary(robustness_score DESC);
        """
    )


def _insert_listings(connection: sqlite3.Connection, listings: Iterable[Listing]) -> None:
    connection.executemany(
        """
        INSERT INTO listings VALUES (
            :listing_id, :name, :area, :housing_mode, :bedrooms, :bathrooms,
            :sqft, :monthly_rent_total, :monthly_required_fees_total,
            :monthly_utilities_estimate, :occupants, :commute_minutes,
            :safety_score, :convenience_score, :management_score, :quiet_score,
            :space_score, :application_score, :available_date,
            :source_checked_at, :source_url, :is_synthetic, :notes
        )
        """,
        [
            {
                **listing.public_dict(),
                "is_synthetic": int(listing.is_synthetic),
            }
            for listing in listings
        ],
    )


def _insert_rankings(connection: sqlite3.Connection, records: Iterable[ScoreRecord]) -> None:
    connection.executemany(
        """
        INSERT INTO rankings VALUES (
            :listing_id, :rank, :eligible, :constraint_reasons, :total_score,
            :all_in_monthly, :rent_share, :cash_needed_at_signing,
            :refundable_deposit, :first_year_nonrefundable_cost,
            :first_year_home_currency, :source_age_days, :pareto_efficient
        )
        """,
        [
            {
                **record.public_dict(),
                "eligible": int(record.eligible),
                "constraint_reasons": json.dumps(
                    record.constraint_reasons,
                    ensure_ascii=False,
                ),
                "pareto_efficient": int(record.pareto_efficient),
            }
            for record in records
        ],
    )


def _insert_contributions(connection: sqlite3.Connection, records: Iterable[ScoreRecord]) -> None:
    rows = []
    for record in records:
        for criterion, contribution in record.contributions.items():
            rows.append(
                (
                    record.listing_id,
                    criterion,
                    record.component_scores[criterion],
                    contribution,
                )
            )
    connection.executemany(
        "INSERT INTO score_contributions VALUES (?, ?, ?, ?)",
        rows,
    )


def _insert_sensitivity(
    connection: sqlite3.Connection,
    summaries: Iterable[SensitivitySummary],
) -> None:
    connection.executemany(
        """
        INSERT INTO sensitivity_summary VALUES (
            :listing_id, :baseline_rank, :best_rank, :worst_rank,
            :average_rank, :top_one_count, :eligible_scenarios,
            :scenario_count, :robustness_score
        )
        """,
        [summary.public_dict() for summary in summaries],
    )


def _insert_sensitivity_matrix(
    connection: sqlite3.Connection,
    rows: Iterable[SensitivityMatrixRow],
) -> None:
    connection.executemany(
        """
        INSERT INTO sensitivity_matrix VALUES (
            :scenario, :listing_id, :rank, :eligible, :total_score
        )
        """,
        [
            {
                **row.public_dict(),
                "eligible": int(row.eligible),
            }
            for row in rows
        ],
    )
