from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from housing_decision_kit.io import input_hash, load_listings, load_preferences
from housing_decision_kit.validation import has_errors, validate_dataset

from helpers import make_listing, make_preferences


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "synthetic_city"


class InputAndValidationTests(unittest.TestCase):
    def test_loads_example_inputs(self) -> None:
        listings = load_listings(EXAMPLE / "listings.csv")
        preferences = load_preferences(EXAMPLE / "preferences.json")
        self.assertEqual(len(listings), 14)
        self.assertEqual(preferences.home_currency, "CNY")
        self.assertTrue(all(listing.is_synthetic for listing in listings))

    def test_example_dataset_has_no_validation_errors(self) -> None:
        messages = validate_dataset(
            load_listings(EXAMPLE / "listings.csv"),
            load_preferences(EXAMPLE / "preferences.json"),
            as_of=date(2026, 6, 15),
        )
        self.assertFalse(has_errors(messages))
        self.assertTrue(any(message.code == "all_data_synthetic" for message in messages))

    def test_duplicate_ids_are_rejected(self) -> None:
        listing = make_listing()
        messages = validate_dataset(
            [listing, listing],
            make_preferences(),
            as_of=date(2026, 6, 15),
        )
        self.assertTrue(has_errors(messages))
        self.assertTrue(any(message.code == "duplicate_listing_id" for message in messages))

    def test_future_source_date_is_rejected(self) -> None:
        messages = validate_dataset(
            [make_listing(source_checked_at=date(2026, 7, 1))],
            make_preferences(),
            as_of=date(2026, 6, 15),
        )
        self.assertTrue(any(message.code == "future_source_date" for message in messages))

    def test_input_hash_changes_when_input_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "a.json"
            second = Path(temporary) / "b.json"
            first.write_text(json.dumps({"a": 1}), encoding="utf-8")
            second.write_text(json.dumps({"b": 2}), encoding="utf-8")
            before = input_hash([first, second])
            second.write_text(json.dumps({"b": 3}), encoding="utf-8")
            after = input_hash([first, second])
            self.assertNotEqual(before, after)


if __name__ == "__main__":
    unittest.main()
