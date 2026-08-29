#!/usr/bin/env python3
"""Compare deterministic demo outputs across Python and SQLite versions."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_map(directory: Path) -> dict[str, Path]:
    return {
        str(path.relative_to(directory)): path
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def sqlite_payload(path: Path) -> dict[str, object]:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        table_names = [
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
        ]
        payload: dict[str, object] = {}
        for table_name in table_names:
            escaped_name = table_name.replace('"', '""')
            columns = [
                list(row)
                for row in connection.execute(
                    f'PRAGMA table_info("{escaped_name}")'
                ).fetchall()
            ]
            rows = [
                list(row)
                for row in connection.execute(
                    f'SELECT * FROM "{escaped_name}"'
                ).fetchall()
            ]
            rows.sort(
                key=lambda row: json.dumps(
                    row,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    default=str,
                )
            )
            payload[table_name] = {"columns": columns, "rows": rows}
        return payload
    finally:
        connection.close()


def normalized_manifest(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    output_files = payload.get("output_files")
    if isinstance(output_files, dict) and "decision.sqlite" in output_files:
        output_files["decision.sqlite"] = "<semantic-sqlite-comparison>"
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("expected", type=Path)
    parser.add_argument("actual", type=Path)
    args = parser.parse_args(argv)

    expected = args.expected.resolve()
    actual = args.actual.resolve()
    if not expected.is_dir() or not actual.is_dir():
        print("Both arguments must be output directories.", file=sys.stderr)
        return 2

    expected_files = file_map(expected)
    actual_files = file_map(actual)
    errors: list[str] = []

    missing = sorted(set(expected_files) - set(actual_files))
    extra = sorted(set(actual_files) - set(expected_files))
    if missing:
        errors.append(f"missing files: {', '.join(missing)}")
    if extra:
        errors.append(f"unexpected files: {', '.join(extra)}")

    byte_count = 0
    common = sorted(set(expected_files) & set(actual_files))
    for name in common:
        if name == "decision.sqlite":
            if sqlite_payload(expected_files[name]) != sqlite_payload(actual_files[name]):
                errors.append("semantic mismatch: decision.sqlite")
        elif name == "run_manifest.json":
            if normalized_manifest(expected_files[name]) != normalized_manifest(
                actual_files[name]
            ):
                errors.append("normalized content mismatch: run_manifest.json")
        else:
            expected_hash = digest(expected_files[name])
            actual_hash = digest(actual_files[name])
            if expected_hash != actual_hash:
                errors.append(
                    f"content mismatch: {name} ({expected_hash} != {actual_hash})"
                )
            else:
                byte_count += 1

    if errors:
        print(
            f"Portable deterministic comparison failed with {len(errors)} difference(s):",
            file=sys.stderr,
        )
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        "Portable deterministic comparison passed: "
        f"{byte_count} file(s) byte-identical; SQLite schema/data and "
        "the normalized manifest match."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
