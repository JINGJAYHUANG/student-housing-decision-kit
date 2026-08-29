#!/usr/bin/env python3
"""Apply the portable reproducibility contract to an extracted source tree."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def replace_required(text: str, old: str, new: str, *, label: str) -> str:
    if old not in text:
        raise SystemExit(f"expected text not found while patching {label}")
    return text.replace(old, new)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: normalize_source.py SOURCE_ROOT")

    source_root = Path(sys.argv[1]).resolve()
    bootstrap_root = Path(__file__).resolve().parent
    compare_target = source_root / "scripts" / "compare_demo.py"
    shutil.copyfile(bootstrap_root / "portable_compare.py", compare_target)

    test_path = source_root / "tests" / "test_publication_guards.py"
    test_text = test_path.read_text(encoding="utf-8")
    test_text = replace_required(
        test_text,
        'self.assertIn("byte-identical", result.stdout)',
        'self.assertIn("Portable deterministic comparison passed", result.stdout)',
        label=str(test_path),
    )
    test_path.write_text(test_text, encoding="utf-8")

    verification_path = source_root / "docs" / "release-verification.md"
    verification_text = verification_path.read_text(encoding="utf-8")
    verification_text = replace_required(
        verification_text,
        "| Deterministic regeneration | 10 output files byte-identical |",
        "| Portable deterministic regeneration | 8 text/JSON/CSV/HTML artifacts byte-identical; SQLite schema/data and normalized manifest equivalent across runtime versions |",
        label=str(verification_path),
    )
    verification_text = verification_text.replace(
        "The GitHub-hosted workflow has not run because the new repository has not yet been created. The workflow is configured for Python 3.11, 3.12 and 3.13 with read-only repository permissions and pinned action revisions.",
        "GitHub-hosted verification is required on Python 3.11, 3.12 and 3.13 with read-only repository permissions and pinned action revisions before merge.",
    )
    verification_path.write_text(verification_text, encoding="utf-8")

    readme_path = source_root / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8")
    marker = "These numbers demonstrate the model only; they are not real market information.\n"
    note = (
        "\nPortable reproducibility is verified byte-for-byte for CSV, JSON and HTML "
        "artifacts. SQLite is compared by schema and ordered row content because its "
        "physical file layout can vary across SQLite runtime versions; the manifest is "
        "normalized only for that SQLite file digest.\n"
    )
    if note.strip() not in readme_text:
        readme_text = replace_required(
            readme_text,
            marker,
            marker + note,
            label=str(readme_path),
        )
    readme_path.write_text(readme_text, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
