-- 1. Eligible shortlist with sensitivity diagnostics.
SELECT
    l.name,
    l.area,
    r.rank,
    ROUND(r.total_score, 3) AS total_score,
    ROUND(r.all_in_monthly, 2) AS all_in_monthly,
    ROUND(r.cash_needed_at_signing, 2) AS signing_cash,
    s.best_rank,
    s.worst_rank,
    ROUND(s.robustness_score, 2) AS robustness_score
FROM rankings AS r
JOIN listings AS l USING (listing_id)
JOIN sensitivity_summary AS s USING (listing_id)
WHERE r.eligible = 1
ORDER BY r.rank;

-- 2. Why filtered options failed.
SELECT
    l.name,
    r.total_score,
    r.constraint_reasons
FROM rankings AS r
JOIN listings AS l USING (listing_id)
WHERE r.eligible = 0
ORDER BY r.total_score DESC;

-- 3. Largest weighted contributors for the top-ranked option.
SELECT
    l.name,
    c.criterion,
    ROUND(c.component_score, 3) AS component_score,
    ROUND(c.contribution, 3) AS weighted_contribution
FROM score_contributions AS c
JOIN listings AS l USING (listing_id)
JOIN rankings AS r USING (listing_id)
WHERE r.rank = 1
ORDER BY c.contribution DESC;

-- 4. Pareto-efficient eligible options.
SELECT
    l.name,
    r.total_score,
    r.all_in_monthly,
    l.commute_minutes
FROM rankings AS r
JOIN listings AS l USING (listing_id)
WHERE r.eligible = 1
  AND r.pareto_efficient = 1
ORDER BY r.rank;

-- 5. Scenarios that change the winner.
WITH baseline AS (
    SELECT listing_id
    FROM sensitivity_matrix
    WHERE scenario = 'baseline' AND rank = 1
)
SELECT
    sm.scenario,
    l.name AS scenario_winner,
    ROUND(sm.total_score, 3) AS total_score
FROM sensitivity_matrix AS sm
JOIN listings AS l USING (listing_id)
WHERE sm.rank = 1
  AND sm.eligible = 1
  AND sm.listing_id NOT IN (SELECT listing_id FROM baseline)
ORDER BY sm.scenario;
