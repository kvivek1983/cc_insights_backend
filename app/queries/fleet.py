"""
SQL query constants for the Fleet Analytics endpoints.

All queries use asyncpg-style parameterized placeholders ($1, $2, ...).
Common rules enforced in all queries:
  - is_deleted = false
  - $1 is always company_id
"""

ROUTE_COMPLETION_BY_TIER = """
SELECT COALESCE(rc.tier, 'Unassigned') AS tier,
  COALESCE(SUM(rc.scheduled_count_of_trips), 0)::int AS scheduled_trips,
  COUNT(CASE WHEN br.actual_day_end_time IS NOT NULL THEN 1 END) AS actual_trips,
  ROUND(COALESCE(SUM(rc.scheduled_km), 0)::numeric, 0) AS scheduled_km,
  ROUND(COALESCE(SUM(br.running_kms), 0)::numeric, 0) AS actual_km,
  ROUND(COUNT(CASE WHEN br.actual_day_end_time IS NOT NULL THEN 1 END)::numeric /
    NULLIF(COALESCE(SUM(rc.scheduled_count_of_trips), 0), 0) * 100, 1) AS completion_pct
FROM bus_routine_master br
LEFT JOIN route_code_master rc ON br.route_id = rc.route_code_id AND rc.is_deleted = false
WHERE br.is_deleted = false AND br.company_id = $1 AND br.routine_start_date = CURRENT_DATE
GROUP BY rc.tier ORDER BY rc.tier
"""

BREAKDOWN_REASONS = """
SELECT COALESCE(rb.reason_id, 0) AS reason_id,
  COALESCE(rb.reason_text, bb.reason_bucket, 'Unknown') AS reason_text,
  COUNT(*) AS count,
  ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 1) AS percentage
FROM bus_breakdown_master bb
JOIN bus_routine_master br ON bb.bus_routine_id = br.bus_routine_id AND br.is_deleted = false
LEFT JOIN reason_bucket rb ON bb.reason_id = rb.reason_id AND rb.is_deleted = false
WHERE bb.is_deleted = false AND br.company_id = $1
  AND br.routine_start_date >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY rb.reason_id, rb.reason_text, bb.reason_bucket ORDER BY count DESC
"""

REPEAT_BREAKDOWN_VEHICLES = """
SELECT b.bus_id, b.registration_number, COUNT(*) AS breakdown_count,
  MAX(br.routine_start_date)::text AS last_breakdown_date,
  (SELECT rb.reason_text FROM reason_bucket rb WHERE rb.reason_id = (
    SELECT bb2.reason_id FROM bus_breakdown_master bb2
    JOIN bus_routine_master br2 ON bb2.bus_routine_id = br2.bus_routine_id
    WHERE br2.bus_id = b.bus_id AND bb2.is_deleted = false
    ORDER BY bb2.created_date DESC LIMIT 1
  )) AS last_reason
FROM bus_breakdown_master bb
JOIN bus_routine_master br ON bb.bus_routine_id = br.bus_routine_id AND br.is_deleted = false
JOIN bus_master b ON br.bus_id = b.bus_id AND b.is_deleted = false
WHERE bb.is_deleted = false AND br.company_id = $1
  AND br.routine_start_date >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY b.bus_id, b.registration_number HAVING COUNT(*) >= 3
ORDER BY breakdown_count DESC LIMIT $2
"""
