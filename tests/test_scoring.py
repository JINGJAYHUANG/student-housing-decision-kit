from __future__ import annotations

import unittest
from datetime import date

from housing_decision_kit.scoring import (
    affordability_score,
    commute_score,
    constraint_reasons,
    freshness_score,
    rank_listings,
    timing_score,
)

from helpers import make_listing, make_preferences


class ScoreFunctionTests(unittest.TestCase):
    def test_affordability_curve_anchor_points(self) -> None:
        budget = 4000.0
        self.assertAlmostEqual(affordability_score(3000, budget), 10.0)
        self.assertAlmostEqual(affordability_score(4000, budget), 7.0)
        self.assertAlmostEqual(affordability_score(4800, budget), 0.0)

    def test_commute_curve_anchor_points(self) -> None:
        self.assertAlmostEqual(commute_score(10, 35), 10.0)
        self.assertAlmostEqual(commute_score(35, 35), 5.0)
        self.assertEqual(commute_score(60, 35), 0.0)

    def test_timing_score_penalizes_late_move_in(self) -> None:
        target = date(2026, 8, 20)
        self.assertEqual(timing_score(target, target, 20), 10.0)
        self.assertAlmostEqual(timing_score(date(2026, 8, 30), target, 20), 5.0)
        self.assertEqual(timing_score(date(2026, 9, 9), target, 20), 0.0)

    def test_freshness_score_declines_with_age(self) -> None:
        as_of = date(2026, 6, 15)
        recent = freshness_score(date(2026, 6, 10), as_of, 90)
        old = freshness_score(date(2026, 1, 1), as_of, 90)
        self.assertGreater(recent, old)
        self.assertEqual(recent, 10.0)

    def test_constraints_are_explicit_and_cumulative(self) -> None:
        listing = make_listing(
            safety_score=6.0,
            commute_minutes=50.0,
            available_date=date(2026, 10, 1),
            source_checked_at=date(2026, 1, 1),
            monthly_rent_total=5000.0,
        )
        reasons = constraint_reasons(
            listing,
            make_preferences(),
            as_of=date(2026, 6, 15),
        )
        self.assertGreaterEqual(len(reasons), 4)
        self.assertTrue(any("safety" in reason for reason in reasons))
        self.assertTrue(any("commute" in reason for reason in reasons))
        self.assertTrue(any("move-in" in reason for reason in reasons))
        self.assertTrue(any("source age" in reason for reason in reasons))

    def test_eligible_listings_rank_before_filtered_listings(self) -> None:
        eligible = make_listing(listing_id="A", name="Eligible")
        filtered = make_listing(
            listing_id="B",
            name="Filtered",
            safety_score=5.0,
            monthly_rent_total=1000.0,
        )
        records = rank_listings(
            [filtered, eligible],
            make_preferences(),
            as_of=date(2026, 6, 15),
        )
        self.assertEqual(records[0].listing_id, "A")
        self.assertTrue(records[0].eligible)
        self.assertFalse(records[1].eligible)

    def test_pareto_marker_is_computed(self) -> None:
        cheap_far = make_listing(
            listing_id="CHEAP",
            name="Cheap",
            monthly_rent_total=2400,
            commute_minutes=30,
        )
        expensive_near = make_listing(
            listing_id="NEAR",
            name="Near",
            monthly_rent_total=3500,
            commute_minutes=7,
            management_score=9.5,
        )
        dominated = make_listing(
            listing_id="DOM",
            name="Dominated",
            monthly_rent_total=3600,
            commute_minutes=32,
            safety_score=7.6,
            convenience_score=7.0,
            management_score=7.0,
            quiet_score=7.0,
            space_score=7.0,
            application_score=7.0,
        )
        records = rank_listings(
            [cheap_far, expensive_near, dominated],
            make_preferences(),
            as_of=date(2026, 6, 15),
        )
        by_id = {record.listing_id: record for record in records}
        self.assertFalse(by_id["DOM"].pareto_efficient)
        self.assertTrue(by_id["CHEAP"].pareto_efficient or by_id["NEAR"].pareto_efficient)


if __name__ == "__main__":
    unittest.main()
