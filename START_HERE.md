# Compare homes beyond the advertised rent
## 月租之外，还要看总成本、签约现金和实际取舍

[Full documentation](README.md) · [Public tool collection](https://github.com/JINGJAYHUANG/JINGJAYHUANG)

**For:** students and other renters who want a transparent way to compare options.  
**Input:** a listing CSV, preference JSON and explicit analysis date.  
**Output:** rankings, exclusion reasons, cost comparisons, sensitivity analysis and an HTML report.

The student-housing fixture is a starting point, not proof that the model fits every city's rental rules or every household.

## Try the fictional city

Requires Python 3.11 or newer. Create an isolated environment:

```bash
git clone https://github.com/JINGJAYHUANG/student-housing-decision-kit.git
cd student-housing-decision-kit
python -m venv .venv
```

Activate with `source .venv/bin/activate` on macOS/Linux, or `.venv\Scripts\Activate.ps1` in Windows PowerShell. Then:

```bash
python -m pip install -e .
housing-decision validate --listings examples/synthetic_city/listings.csv --preferences examples/synthetic_city/preferences.json --as-of 2026-06-15
housing-decision evaluate --listings examples/synthetic_city/listings.csv --preferences examples/synthetic_city/preferences.json --as-of 2026-06-15 --generated-at 2026-06-15T12:00:00Z --output-dir build/housing-demo
```

Open `build/housing-demo/decision_report.html` in a browser. Inspect `ranking.csv` to see why options passed or failed. The fixed 2026-06-15 date belongs to the synthetic demonstration; it is not a claim about current listings.

## Read the result in this order

First check the hard constraints. Then compare all-in monthly cost and signing cash. Finally inspect how the ordering changes when reasonable preferences change. A high score should never silently compensate for a non-negotiable constraint.

房源便宜，不代表签约时需要的钱少；分数高，也不代表换一套权重后仍然第一。这个工具把这些取舍显式列出来，而不是替你作决定。

## Before using real records

Keep real inputs outside the public checkout. Define fees, units, currency and analysis dates consistently. Replace fictional source records with evidence you are entitled to use, and document subjective ratings. Do not publish personal applications, landlord contacts, addresses, lease documents or private preference files.

## Boundaries

This is a decision-support model, not a property search service, legal advisor or safety guarantee. It does not retrieve current listings, apply for housing or inspect a building. Synthetic scores and prices do not describe any real property.

See the [README](README.md) for the data dictionary, formulas, SQL examples and verification instructions. This onboarding guide follows documentation reviewed on 2026-09-05; it does not establish fresh execution of the full test suite.
