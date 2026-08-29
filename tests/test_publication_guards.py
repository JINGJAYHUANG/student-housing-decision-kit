from __future__ import annotations

import csv
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PublicationGuardTests(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_repository_privacy_scan_passes(self) -> None:
        result = self.run_script("scripts/privacy_scan.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Privacy scan passed", result.stdout)

    def test_committed_demo_verifies(self) -> None:
        result = self.run_script("scripts/verify_demo.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Demo verification passed", result.stdout)

    def test_demo_compares_to_itself(self) -> None:
        output = "examples/synthetic_city/output"
        result = self.run_script("scripts/compare_demo.py", output, output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Portable deterministic comparison passed", result.stdout)

    def test_privacy_scan_rejects_email(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fixture = root / "examples" / "synthetic_city"
            fixture.mkdir(parents=True)
            shutil.copy(ROOT / "examples/synthetic_city/listings.csv", fixture / "listings.csv")
            shutil.copy(
                ROOT / "examples/synthetic_city/preferences.json",
                fixture / "preferences.json",
            )
            (root / "README.md").write_text(
                "Contact person: private.person" + "@" + "example.org\n",
                encoding="utf-8",
            )
            result = self.run_script("scripts/privacy_scan.py", "--root", str(root))
            self.assertEqual(result.returncode, 1)
            self.assertIn("possible email_address", result.stderr)

    def test_privacy_scan_rejects_non_synthetic_public_row(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fixture = root / "examples" / "synthetic_city"
            fixture.mkdir(parents=True)
            source = ROOT / "examples/synthetic_city/listings.csv"
            with source.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
                fieldnames = list(rows[0])
            rows[0]["is_synthetic"] = "false"
            with (fixture / "listings.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            shutil.copy(
                ROOT / "examples/synthetic_city/preferences.json",
                fixture / "preferences.json",
            )
            result = self.run_script("scripts/privacy_scan.py", "--root", str(root))
            self.assertEqual(result.returncode, 1)
            self.assertIn("not explicitly synthetic", result.stderr)


if __name__ == "__main__":
    unittest.main()
