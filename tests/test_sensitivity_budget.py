from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path

from housing_decision_kit.budget import build_budget_scenarios
from housing_decision_kit.io import load_listings, load_preferences
from housing_decision_kit.sensitivity import build_scenarios, run_sensitivity


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "synthetic_city"


class SensitivityAndBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.listings = load_listings(EXAMPLE / "listings.csv")
        cls.preferences = load_preferences(EXAMPLE / "preferences.json")

    def test_expected_scenario_count(self) -> None:
        scenarios = build_scenarios(self.preferences)
        self.assertEqual(len(scenarios), 28)
        self.assertEqual(scenarios[0][0], "baseline")

    def test_sensitivity_covers_every_listing_and_scenario(self) -> None:
        summaries, matrix = run_sensitivity(
            self.listings,
            self.preferences,
            as_of=date(2026, 6, 15),
        )
        self.assertEqual(len(summaries), len(self.listings))
        self.assertEqual(len(matrix), len(self.listings) * 28)
        self.assertTrue(all(0 <= row.robustness_score <= 10 for row in summaries))

    def test_budget_scenarios_cover_four_stresses(self) -> None:
        rows = build_budget_scenarios(self.listings, self.preferences)
        self.assertEqual(len(rows), len(self.listings) * 4)
        scenarios = {str(row["scenario"]) for row in rows}
        self.assertEqual(
            scenarios,
            {
                "base",
                "fees_and_utilities_plus_20pct",
                "rent_plus_5pct",
                "home_currency_weakens_5pct",
            },
        )

    def test_home_currency_stress_changes_only_currency_conversion(self) -> None:
        rows = build_budget_scenarios([self.listings[0]], self.preferences)
        base = next(row for row in rows if row["scenario"] == "base")
        fx = next(row for row in rows if row["scenario"] == "home_currency_weakens_5pct")
        self.assertEqual(base["first_year_usd"], fx["first_year_usd"])
        self.assertGreater(float(fx["first_year_home_currency"]), float(base["first_year_home_currency"]))


if __name__ == "__main__":
    unittest.main()
