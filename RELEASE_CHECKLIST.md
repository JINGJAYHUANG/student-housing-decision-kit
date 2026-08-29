# Release Checklist

- [ ] Version matches in `pyproject.toml`, `src/housing_decision_kit/__init__.py`, `CHANGELOG.md` and `CITATION.cff`.
- [ ] `python -m unittest discover -s tests -v` passes.
- [ ] `python scripts/privacy_scan.py` passes.
- [ ] Fixed synthetic demo regenerates successfully.
- [ ] `python scripts/verify_demo.py` passes.
- [ ] Regenerated output is byte-identical to the committed fixture.
- [ ] HTML report is visually inspected at desktop and narrow widths.
- [ ] Wheel installs in a clean virtual environment without network access.
- [ ] Source archive contains no build cache, `.git`, private data or credentials.
- [ ] GitHub Actions uses read-only permissions and pinned action SHAs.
- [ ] Repository description, topics and release notes do not imply current housing advice.
