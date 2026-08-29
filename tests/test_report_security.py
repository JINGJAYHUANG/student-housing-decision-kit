from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from helpers import make_listing, make_preferences
from housing_decision_kit.report import render_report
from housing_decision_kit.scoring import rank_listings
from housing_decision_kit.sensitivity import run_sensitivity


class ReportSecurityTests(unittest.TestCase):
    def render(self, *, is_synthetic: bool = True) -> str:
        payload = '<script>globalThis.compromised = true</script>'
        listing = make_listing(
            name=payload,
            notes=payload,
            is_synthetic=is_synthetic,
            source_url=(
                "synthetic://listing/L-001"
                if is_synthetic
                else 'https://example.invalid/\" onmouseover=\"alert(1)'
            ),
        )
        preferences = make_preferences()
        as_of = date(2026, 6, 15)
        records = rank_listings([listing], preferences, as_of=as_of)
        sensitivity, _ = run_sensitivity([listing], preferences, as_of=as_of)
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "report.html"
            render_report(
                output,
                listings=[listing],
                records=records,
                preferences=preferences,
                sensitivity=sensitivity,
                generated_at="2026-06-15T12:00:00Z",
                as_of=as_of.isoformat(),
                input_hash="0" * 64,
            )
            return output.read_text(encoding="utf-8")

    def test_user_text_is_html_escaped(self) -> None:
        html = self.render()
        self.assertNotIn("<script>globalThis.compromised", html)
        self.assertIn("&lt;script&gt;globalThis.compromised", html)

    def test_non_synthetic_run_has_publication_warning(self) -> None:
        html = self.render(is_synthetic=False)
        self.assertIn("includes rows not marked synthetic", html)
        self.assertIn("&quot; onmouseover=&quot;alert(1)", html)


if __name__ == "__main__":
    unittest.main()
