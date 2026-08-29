#!/usr/bin/env python3
"""Conservative repository privacy and secret scanner.

This is intentionally small and dependency-free. It catches common accidental
publication problems, then performs stronger invariants on the committed public
fixture. It does not replace human review.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

TEXT_EXTENSIONS = {
    ".csv",
    ".html",
    ".json",
    ".md",
    ".py",
    ".sql",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
SKIP_PARTS = {".git", "__pycache__", ".venv", "venv", "build", "dist"}

# Concatenation prevents the scanner from triggering on its own source.
LEGACY_PRIVATE_TERMS = (
    "north" + "eastern",
    "jing" + "jie",
    "huang" + "jing" + "jie",
    "ly" + "ra",
    "aval" + "on exeter",
    "pierce " + "boston",
    "longwood " + "towers",
)

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "email_address",
        re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![A-Za-z0-9])"),
    ),
    (
        "phone_number",
        re.compile(r"(?<!\d)(?:\+?1[ .-]?)?(?:\(?\d{3}\)?[ .-])\d{3}[ .-]\d{4}(?!\d)"),
    ),
    (
        "unix_user_path",
        re.compile(re.escape("/" + "Users" + "/") + r"[^/\s]+/"),
    ),
    (
        "windows_user_path",
        re.compile(re.escape("C:" + "\\" + "Users" + "\\"), re.IGNORECASE),
    ),
    (
        "linux_home_path",
        re.compile(re.escape("/" + "home" + "/") + r"(?!oai(?:/|\b))[^/\s]+/"),
    ),
    (
        "github_token",
        re.compile(r"\b(?:gh" + r"[pousr]_[A-Za-z0-9]{20,})\b"),
    ),
    (
        "openai_style_secret",
        re.compile(r"\b(?:s" + r"k-[A-Za-z0-9_-]{16,})\b"),
    ),
    (
        "aws_access_key",
        re.compile(r"\b(?:AK" + r"IA|ASIA)[A-Z0-9]{16}\b"),
    ),
    (
        "private_key_block",
        re.compile(r"-{5}BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-{5}"),
    ),
)

ALLOWED_EMAIL_CONTEXTS: tuple[str, ...] = ()


def iter_text_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in SKIP_PARTS for part in relative.parts):
            continue
        if path.suffix.lower() in TEXT_EXTENSIONS or path.name in {
            "LICENSE",
            "Makefile",
            ".gitignore",
            ".env.example",
        }:
            yield path


def scan_text(root: Path) -> list[str]:
    findings: list[str] = []
    for path in iter_text_files(root):
        relative = path.relative_to(root)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(f"{relative}: text-like file is not valid UTF-8")
            continue

        lower_text = text.lower()
        for term in LEGACY_PRIVATE_TERMS:
            if term in lower_text:
                findings.append(f"{relative}: contains legacy/private term {term!r}")

        for label, pattern in PATTERNS:
            for match in pattern.finditer(text):
                value = match.group(0)
                if label == "email_address" and any(
                    allowed in value for allowed in ALLOWED_EMAIL_CONTEXTS
                ):
                    continue
                line = text.count("\n", 0, match.start()) + 1
                findings.append(
                    f"{relative}:{line}: possible {label}: {redact(value)}"
                )
    return findings


def redact(value: str) -> str:
    if len(value) <= 8:
        return "<redacted>"
    return f"{value[:3]}…{value[-3:]}"


def check_public_fixture(root: Path) -> list[str]:
    findings: list[str] = []
    listings_path = root / "examples" / "synthetic_city" / "listings.csv"
    preferences_path = root / "examples" / "synthetic_city" / "preferences.json"
    if not listings_path.exists():
        return [f"missing public fixture: {listings_path.relative_to(root)}"]
    if not preferences_path.exists():
        findings.append(f"missing public fixture: {preferences_path.relative_to(root)}")

    with listings_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        findings.append("public fixture contains no listing rows")
        return findings

    ids: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        listing_id = (row.get("listing_id") or "").strip()
        if listing_id in ids:
            findings.append(f"listings.csv:{line_number}: duplicate listing_id {listing_id!r}")
        ids.add(listing_id)
        if (row.get("is_synthetic") or "").strip().lower() != "true":
            findings.append(
                f"listings.csv:{line_number}: public row is not explicitly synthetic"
            )
        if not (row.get("source_url") or "").startswith("synthetic://"):
            findings.append(
                f"listings.csv:{line_number}: public source must use synthetic://"
            )
        if not listing_id.startswith("SYN-"):
            findings.append(
                f"listings.csv:{line_number}: public listing_id must start with SYN-"
            )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root to scan.",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()

    findings = scan_text(root)
    findings.extend(check_public_fixture(root))
    if findings:
        print(f"Privacy scan failed with {len(findings)} finding(s):", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1

    scanned = sum(1 for _ in iter_text_files(root))
    print(f"Privacy scan passed: {scanned} text file(s) checked; public fixture is synthetic.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
