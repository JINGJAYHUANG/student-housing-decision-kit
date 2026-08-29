from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from housing_decision_kit.cli import main


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "synthetic_city"


class CliIntegrationTests(unittest.TestCase):
    def test_evaluate_generates_complete_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            code = main(
                [
                    "evaluate",
                    "--listings",
                    str(EXAMPLE / "listings.csv"),
                    "--preferences",
                    str(EXAMPLE / "preferences.json"),
                    "--as-of",
                    "2026-06-15",
                    "--generated-at",
                    "2026-06-15T12:00:00Z",
                    "--output-dir",
                    str(output),
                ]
            )
            self.assertEqual(code, 0)
            expected = {
                "validation.json",
                "ranking.csv",
                "score_contributions.csv",
                "sensitivity_summary.csv",
                "sensitivity_matrix.csv",
                "budget_scenarios.csv",
                "decision.json",
                "decision_report.html",
                "decision.sqlite",
                "run_manifest.json",
            }
            self.assertEqual({path.name for path in output.iterdir()}, expected)

            payload = json.loads((output / "decision.json").read_text(encoding="utf-8"))
            self.assertTrue(payload["metadata"]["all_data_synthetic"])
            self.assertEqual(payload["rankings"][0]["listing_id"], "SYN-014")

            html = (output / "decision_report.html").read_text(encoding="utf-8")
            self.assertIn("All rows in this demonstration are synthetic", html)
            self.assertIn("Scholars Landing", html)

    def test_sqlite_export_supports_example_query(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            code = main(
                [
                    "evaluate",
                    "--listings",
                    str(EXAMPLE / "listings.csv"),
                    "--preferences",
                    str(EXAMPLE / "preferences.json"),
                    "--as-of",
                    "2026-06-15",
                    "--generated-at",
                    "2026-06-15T12:00:00Z",
                    "--output-dir",
                    str(output),
                ]
            )
            self.assertEqual(code, 0)
            connection = sqlite3.connect(output / "decision.sqlite")
            try:
                row = connection.execute(
                    """
                    SELECT l.name, r.total_score
                    FROM rankings r
                    JOIN listings l USING (listing_id)
                    WHERE r.eligible = 1
                    ORDER BY r.rank
                    LIMIT 1
                    """
                ).fetchone()
            finally:
                connection.close()
            self.assertEqual(row[0], "Scholars Landing")
            self.assertGreater(row[1], 8.0)

    def test_validate_can_write_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "validation.json"
            code = main(
                [
                    "validate",
                    "--listings",
                    str(EXAMPLE / "listings.csv"),
                    "--preferences",
                    str(EXAMPLE / "preferences.json"),
                    "--as-of",
                    "2026-06-15",
                    "--json-output",
                    str(output),
                ]
            )
            self.assertEqual(code, 0)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
