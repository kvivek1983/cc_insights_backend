"""
SQL query constants for the Division Performance endpoints.

All queries use asyncpg-style parameterized placeholders ($1, $2, ...).
Common rules enforced in all queries:
  - is_deleted = false
  - Fuel quality filters: total_amount < 1000000, volume_in_liter BETWEEN 1 AND 500,
    fuel_price BETWEEN 50 AND 150
  - fuel_expense_id != 12 (excluded pump type)
  - $1 is always company_id
"""

DIVISION_PERFORMANCE = """
WITH att AS (
  SELECT ucm.division_id,
    COUNT(DISTINCT a.user_id) AS present,
    emp.total_employees,
    ROUND(COUNT(DISTINCT a.user_id)::numeric / NULLIF(emp.total_employees, 0) * 100, 1) AS attendance_pct
  FROM user_attendance_master a
  JOIN user_company_master ucm ON a.user_id = ucm.user_id AND ucm.is_deleted = false AND ucm.is_active = true AND ucm.division_id > 0
  LEFT JOIN (
    SELECT division_id, COUNT(DISTINCT user_id) AS total_employees
    FROM user_company_master
    WHERE company_id = $1 AND is_deleted = false AND is_active = true AND division_id > 0
    GROUP BY division_id
  ) emp ON ucm.division_id = emp.division_id
  WHERE a.is_deleted = false AND a.company_id = $1 AND a.attendance_type = 1
    AND a.created_date >= CURRENT_DATE::timestamp AND a.created_date < (CURRENT_DATE + INTERVAL '1 day')::timestamp
  GROUP BY ucm.division_id, emp.total_employees
),
fuel_ranked AS (
  SELECT *, ROW_NUMBER() OVER (
    PARTITION BY bus_id, expense_date, total_amount, volume_in_liter
    ORDER BY fuel_expense_id
  ) AS rn
  FROM fuel_expense_master
  WHERE is_deleted = false AND company_id = $1
    AND fuel_expense_id != 12
    AND total_amount < 1000000 AND volume_in_liter BETWEEN 1 AND 500 AND fuel_price BETWEEN 50 AND 150
),
fuel_dedup AS (SELECT * FROM fuel_ranked WHERE rn = 1),
fuel AS (
  SELECT fe.division_id, ROUND(SUM(fe.total_amount)::numeric / 100000, 2) AS fuel_spend_lakhs
  FROM fuel_dedup fe
  WHERE fe.expense_date >= DATE_TRUNC('month', CURRENT_DATE)
  GROUP BY fe.division_id
),
routes AS (
  SELECT br.division_id,
    ROUND(COUNT(CASE WHEN br.actual_day_end_time IS NOT NULL THEN 1 END)::numeric / NULLIF(COUNT(*), 0) * 100, 1) AS route_completion_pct
  FROM bus_routine_master br
  WHERE br.is_deleted = false AND br.company_id = $1 AND br.routine_start_date = CURRENT_DATE
  GROUP BY br.division_id
),
breakdowns AS (
  SELECT br.division_id, COUNT(*) AS breakdown_count
  FROM bus_breakdown_master bb
  JOIN bus_routine_master br ON bb.bus_routine_id = br.bus_routine_id
  WHERE bb.is_deleted = false AND br.company_id = $1 AND br.routine_start_date >= DATE_TRUNC('month', CURRENT_DATE)
  GROUP BY br.division_id
)
SELECT d.division_id, d.division_name,
  COALESCE(att.attendance_pct, 0) AS attendance_percentage,
  COALESCE(fuel.fuel_spend_lakhs, 0) AS fuel_spend_lakhs,
  COALESCE(routes.route_completion_pct, 0) AS route_completion_pct,
  COALESCE(breakdowns.breakdown_count, 0) AS breakdown_count
FROM divisions_of_company_master d
LEFT JOIN att ON d.division_id = att.division_id
LEFT JOIN fuel ON d.division_id = fuel.division_id
LEFT JOIN routes ON d.division_id = routes.division_id
LEFT JOIN breakdowns ON d.division_id = breakdowns.division_id
WHERE d.is_deleted = false AND d.company_id = $1
ORDER BY attendance_percentage DESC
LIMIT $2
"""
