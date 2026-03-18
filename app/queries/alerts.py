"""
SQL query constants for the Alerts endpoints.

All queries use asyncpg-style parameterized placeholders ($1, $2, ...).
Common rules enforced in all queries:
  - is_deleted = false
  - $1 is always company_id

Each query returns a uniform shape: type, category, message, detail, timestamp, entity_id.
The router combines results from multiple queries via Python-level concatenation.
"""

REPEAT_BREAKDOWN_ALERTS = """
SELECT 'critical' AS type, 'breakdown' AS category,
  b.registration_number || ' — ' || COUNT(*) || ' breakdowns this week (' || MAX(COALESCE(rb.reason_text, 'Unknown')) || ')' AS message,
  b.registration_number AS detail,
  MAX(bb.created_date)::text AS timestamp,
  b.bus_id AS entity_id
FROM bus_breakdown_master bb
JOIN bus_routine_master br ON bb.bus_routine_id = br.bus_routine_id
JOIN bus_master b ON br.bus_id = b.bus_id
LEFT JOIN reason_bucket rb ON bb.reason_id = rb.reason_id
WHERE bb.is_deleted = false AND br.company_id = $1
  AND br.routine_start_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY b.bus_id, b.registration_number HAVING COUNT(*) >= 3
ORDER BY COUNT(*) DESC LIMIT 3
"""

FUEL_WITHOUT_ATTENDANCE_ALERTS = """
SELECT 'warning' AS type, 'fuel_attendance' AS category,
  'Fuel filled without attendance check-in on ' || fe.expense_date::text AS message,
  b.registration_number AS detail,
  fe.created_date::text AS timestamp,
  fe.fuel_expense_id AS entity_id
FROM fuel_expense_master fe
JOIN bus_master b ON fe.bus_id = b.bus_id AND b.is_deleted = false
LEFT JOIN user_attendance_master a
  ON fe.user_id = a.user_id AND a.attendance_type = 1 AND a.is_deleted = false
  AND a.created_date >= fe.expense_date::timestamp
  AND a.created_date < (fe.expense_date + INTERVAL '1 day')::timestamp
WHERE fe.is_deleted = false AND fe.company_id = $1
  AND fe.fuel_expense_id != 12
  AND fe.expense_date >= DATE_TRUNC('month', CURRENT_DATE)
  AND a.user_attendance_id IS NULL
ORDER BY fe.expense_date DESC LIMIT 5
"""

ODOMETER_ANOMALY_ALERTS = """
WITH seq AS (
  SELECT fe.fuel_expense_id, fe.bus_id, fe.expense_date, fe.current_odometer,
    b.registration_number,
    LAG(fe.current_odometer) OVER (PARTITION BY fe.bus_id ORDER BY fe.expense_date, fe.fuel_expense_id) AS prev_odo
  FROM fuel_expense_master fe
  JOIN bus_master b ON fe.bus_id = b.bus_id AND b.is_deleted = false
  WHERE fe.is_deleted = false AND fe.company_id = $1 AND fe.current_odometer > 0
    AND fe.expense_date >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT 'warning' AS type, 'odometer' AS category,
  registration_number || ' — odometer anomaly on ' || expense_date::text
    || ' (prev: ' || prev_odo::text || ', curr: ' || current_odometer::text || ')' AS message,
  registration_number AS detail,
  expense_date::text AS timestamp,
  fuel_expense_id AS entity_id
FROM seq
WHERE prev_odo IS NOT NULL
  AND (current_odometer < prev_odo OR current_odometer - prev_odo > 10000)
ORDER BY expense_date DESC LIMIT 5
"""

IDLE_VEHICLE_ALERTS = """
SELECT 'info' AS type, 'idle_vehicle' AS category,
  b.registration_number || ' — no trip assigned in last 7 days' AS message,
  b.registration_number AS detail,
  NOW()::text AS timestamp,
  b.bus_id AS entity_id
FROM bus_master b
WHERE b.is_deleted = false AND b.is_active = true AND b.company_id = $1
  AND b.bus_id NOT IN (
    SELECT DISTINCT bus_id FROM bus_routine_master
    WHERE is_deleted = false AND company_id = $1
      AND routine_start_date >= CURRENT_DATE - INTERVAL '7 days'
  )
ORDER BY b.registration_number LIMIT 5
"""
