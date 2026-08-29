"""Self-contained HTML report generation."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Mapping

from .models import Listing, Preferences, ScoreRecord, SensitivitySummary


def _money(value: float) -> str:
    return f"${value:,.0f}"


def _home_money(value: float, currency: str) -> str:
    return f"{currency} {value:,.0f}"


def _score_bar(score: float) -> str:
    width = max(0.0, min(100.0, score * 10.0))
    return (
        '<div class="score-cell">'
        f'<span>{score:.2f}</span><span class="bar"><span style="width:{width:.1f}%"></span></span>'
        "</div>"
    )


def _status_badge(record: ScoreRecord) -> str:
    if record.eligible:
        return '<span class="badge ok">Eligible</span>'
    return '<span class="badge bad">Filtered</span>'


def render_report(
    path: str | Path,
    *,
    listings: list[Listing],
    records: list[ScoreRecord],
    preferences: Preferences,
    sensitivity: list[SensitivitySummary],
    generated_at: str,
    as_of: str,
    input_hash: str,
) -> None:
    listing_by_id = {listing.listing_id: listing for listing in listings}
    sensitivity_by_id = {row.listing_id: row for row in sensitivity}
    eligible = [record for record in records if record.eligible]
    top = eligible[:3]
    all_synthetic = all(listing.is_synthetic for listing in listings)

    hero_cards = []
    labels = ["Recommended", "Runner-up", "Alternative"]
    for label, record in zip(labels, top, strict=False):
        listing = listing_by_id[record.listing_id]
        robust = sensitivity_by_id[record.listing_id].robustness_score
        hero_cards.append(
            f"""
            <article class="hero-card">
              <div class="eyebrow">{escape(label)}</div>
              <h3>{escape(record.name)}</h3>
              <p class="muted">{escape(record.area)} · {escape(record.housing_mode)}</p>
              <div class="metrics">
                <div><b>{record.total_score:.2f}</b><span>score / 10</span></div>
                <div><b>{_money(record.all_in_monthly)}</b><span>all-in / month</span></div>
                <div><b>{listing.commute_minutes:.0f} min</b><span>commute</span></div>
                <div><b>{robust:.1f}</b><span>robustness / 10</span></div>
              </div>
              <p>{escape(listing.notes)}</p>
            </article>
            """
        )

    ranking_rows = []
    for record in records:
        listing = listing_by_id[record.listing_id]
        robust = sensitivity_by_id[record.listing_id]
        reasons = "; ".join(record.constraint_reasons) or "—"
        pareto = '<span class="badge pareto">Pareto</span>' if record.pareto_efficient else ""
        source = (
            f'<a href="{escape(listing.source_url)}">source</a>'
            if listing.source_url.startswith(("http://", "https://"))
            else "synthetic record"
        )
        ranking_rows.append(
            f"""
            <tr>
              <td>{record.rank}</td>
              <td><b>{escape(record.name)}</b><br><span class="muted small">{escape(record.area)}</span></td>
              <td>{_status_badge(record)} {pareto}</td>
              <td>{_score_bar(record.total_score)}</td>
              <td>{_money(record.all_in_monthly)}</td>
              <td>{_money(record.cash_needed_at_signing)}</td>
              <td>{listing.commute_minutes:.0f}</td>
              <td>{listing.safety_score:.1f}</td>
              <td>{listing.available_date.isoformat()}</td>
              <td>{robust.best_rank}–{robust.worst_rank}</td>
              <td>{robust.robustness_score:.1f}</td>
              <td class="small">{escape(reasons)}</td>
              <td class="small">{source}</td>
            </tr>
            """
        )

    weight_rows = []
    for criterion, weight in preferences.normalized_weights().items():
        weight_rows.append(
            f"<tr><td>{escape(criterion)}</td><td>{weight:.1%}</td></tr>"
        )

    filtered_count = len(records) - len(eligible)
    synthetic_banner = (
        "All rows in this demonstration are synthetic. No real property, price, person or application record is represented."
        if all_synthetic
        else "This run includes rows not marked synthetic. Verify publication rights before sharing."
    )
    top_name = escape(eligible[0].name) if eligible else "No eligible option"
    top_cost = _money(eligible[0].all_in_monthly) if eligible else "—"
    top_home = (
        _home_money(eligible[0].first_year_home_currency, preferences.home_currency)
        if eligible
        else "—"
    )

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Student Housing Decision Report</title>
<style>
:root {{
  --ink:#172033; --muted:#64748b; --line:#d8e0ea; --soft:#f7f9fc;
  --blue:#1d4ed8; --blue-soft:#dbeafe; --green:#047857; --green-soft:#d1fae5;
  --red:#b91c1c; --red-soft:#fee2e2; --amber:#b45309; --amber-soft:#fef3c7;
  --violet:#6d28d9; --shadow:0 12px 32px rgba(15,23,42,.08);
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:var(--ink); background:#eef2f7; line-height:1.5; }}
a {{ color:var(--blue); }}
main {{ max-width:1440px; margin:0 auto; padding:28px; }}
header {{ background:linear-gradient(135deg,#172033,#1e3a8a); color:white; border-radius:22px; padding:34px; box-shadow:var(--shadow); }}
header h1 {{ margin:0 0 8px; font-size:clamp(28px,4vw,48px); letter-spacing:-.03em; }}
header p {{ max-width:900px; margin:0; color:#dbeafe; }}
.notice {{ margin-top:18px; padding:12px 14px; border:1px solid #93c5fd; background:rgba(219,234,254,.13); border-radius:12px; font-size:14px; }}
.kpis {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:14px; margin:22px 0; }}
.kpi {{ background:white; border:1px solid var(--line); border-radius:16px; padding:18px; box-shadow:var(--shadow); }}
.kpi b {{ display:block; font-size:24px; line-height:1.15; }}
.kpi span {{ color:var(--muted); font-size:13px; }}
.section {{ margin-top:22px; background:white; border:1px solid var(--line); border-radius:18px; padding:22px; box-shadow:var(--shadow); }}
.section h2 {{ margin:0 0 4px; font-size:24px; }}
.section-lead {{ margin:0 0 18px; color:var(--muted); }}
.hero-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; }}
.hero-card {{ border:1px solid var(--line); border-radius:16px; padding:18px; background:linear-gradient(180deg,#fff,var(--soft)); }}
.hero-card h3 {{ margin:4px 0 0; font-size:22px; }}
.eyebrow {{ color:var(--blue); text-transform:uppercase; letter-spacing:.12em; font-weight:800; font-size:11px; }}
.metrics {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; margin:16px 0; }}
.metrics div {{ border:1px solid var(--line); background:white; border-radius:12px; padding:10px; }}
.metrics b {{ display:block; }}
.metrics span {{ color:var(--muted); font-size:11px; }}
.table-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:14px; }}
table {{ width:100%; border-collapse:collapse; min-width:1200px; }}
th,td {{ border-bottom:1px solid var(--line); padding:10px 11px; text-align:left; vertical-align:top; }}
th {{ position:sticky; top:0; z-index:1; background:#e9eef6; font-size:12px; text-transform:uppercase; letter-spacing:.05em; }}
tr:hover td {{ background:#fafcff; }}
.badge {{ display:inline-block; padding:3px 7px; border-radius:999px; font-size:11px; font-weight:800; white-space:nowrap; }}
.badge.ok {{ color:var(--green); background:var(--green-soft); }}
.badge.bad {{ color:var(--red); background:var(--red-soft); }}
.badge.pareto {{ color:var(--violet); background:#ede9fe; }}
.score-cell {{ min-width:130px; }}
.bar {{ display:block; width:100%; height:7px; margin-top:5px; background:#e5e7eb; border-radius:99px; overflow:hidden; }}
.bar span {{ display:block; height:100%; background:linear-gradient(90deg,#60a5fa,#1d4ed8); }}
.two-col {{ display:grid; grid-template-columns:1.25fr .75fr; gap:18px; }}
.code {{ padding:14px; background:#111827; color:#e5e7eb; border-radius:12px; overflow:auto; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:13px; }}
.muted {{ color:var(--muted); }} .small {{ font-size:12px; }}
footer {{ color:var(--muted); font-size:12px; padding:22px 4px; }}
@media (max-width:1000px) {{ .kpis {{ grid-template-columns:repeat(2,1fr); }} .hero-grid,.two-col {{ grid-template-columns:1fr; }} }}
@media (max-width:600px) {{ main {{ padding:12px; }} header {{ padding:22px; }} .kpis {{ grid-template-columns:1fr; }} }}
@media print {{ body {{ background:white; }} main {{ max-width:none; padding:0; }} header,.section,.kpi {{ box-shadow:none; break-inside:avoid; }} .table-wrap {{ overflow:visible; }} }}
</style>
</head>
<body>
<main>
<header>
  <div class="eyebrow" style="color:#93c5fd">Explainable decision support</div>
  <h1>Student Housing Decision Report</h1>
  <p>Transparent ranking with hard constraints, all-in cost, move-in timing, source freshness, Pareto trade-offs and sensitivity analysis.</p>
  <div class="notice"><b>Data boundary:</b> {escape(synthetic_banner)} Analysis as of {escape(as_of)}.</div>
</header>

<section class="kpis">
  <div class="kpi"><b>{len(records)}</b><span>options evaluated</span></div>
  <div class="kpi"><b>{len(eligible)}</b><span>eligible after hard constraints</span></div>
  <div class="kpi"><b>{filtered_count}</b><span>filtered with explicit reasons</span></div>
  <div class="kpi"><b>{top_name}</b><span>highest-ranked eligible option</span></div>
  <div class="kpi"><b>{top_cost}</b><span>top option all-in monthly · first year {top_home}</span></div>
</section>

<section class="section">
  <h2>Decision shortlist</h2>
  <p class="section-lead">These are the best eligible options under the current preference profile. A high score is not a substitute for source verification or lease review.</p>
  <div class="hero-grid">{''.join(hero_cards) if hero_cards else '<p>No listing passed all hard constraints.</p>'}</div>
</section>

<section class="section">
  <h2>Full ranking and filter audit</h2>
  <p class="section-lead">Eligible options rank first. Filtered options remain visible so the decision can be audited rather than silently discarding inconvenient evidence.</p>
  <div class="table-wrap">
  <table>
    <thead><tr><th>Rank</th><th>Option</th><th>Status</th><th>Score</th><th>All-in monthly</th><th>Signing cash</th><th>Commute</th><th>Safety</th><th>Available</th><th>Rank range</th><th>Robustness</th><th>Filter reasons</th><th>Source</th></tr></thead>
    <tbody>{''.join(ranking_rows)}</tbody>
  </table>
  </div>
</section>

<section class="section two-col">
  <div>
    <h2>How the model works</h2>
    <p class="section-lead">Every 0–10 component is multiplied by its normalized weight. Hard constraints are evaluated separately and never hidden inside the weighted score.</p>
    <div class="code">total_score = Σ(component_score × normalized_weight)\n\neligible = safety ≥ floor\n       AND commute ≤ cap\n       AND move_in_delay ≤ tolerance\n       AND signing_cash ≤ cap\n       AND source_age ≤ freshness_cap</div>
    <p><b>Pareto</b> marks an eligible option that is not simultaneously beaten on all-in cost, commute and total score.</p>
    <p><b>Robustness</b> combines rank stability and the share of stress scenarios in which the listing remains eligible. It is descriptive, not a probability.</p>
  </div>
  <div>
    <h2>Normalized weights</h2>
    <div class="table-wrap"><table style="min-width:0"><thead><tr><th>Criterion</th><th>Weight</th></tr></thead><tbody>{''.join(weight_rows)}</tbody></table></div>
  </div>
</section>

<section class="section">
  <h2>Reproducibility record</h2>
  <p class="section-lead">The input hash identifies the exact listing CSV and preference JSON used for this run.</p>
  <div class="code">generated_at: {escape(generated_at)}\nas_of: {escape(as_of)}\ninput_hash: {escape(input_hash)}</div>
</section>

<footer>
This report is decision support, not legal, financial, safety or housing advice. Real users must re-check listing availability, costs, neighborhood conditions, lease terms and local law at the time of decision.
</footer>
</main>
</body>
</html>
"""
    Path(path).write_text(html, encoding="utf-8")
