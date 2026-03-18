"""
SQL query constants for the Data Quality endpoints.

All queries use asyncpg-style parameterized placeholders ($1, $2, ...).
Common rules enforced in all queries:
  - is_deleted = false
  - fuel_expense_id != 12 (excluded pump type) where applicable
  - $1 is always company_id

These queries surface data integrity issues such as missing selfies,
odometer anomalies, duplicate fuel entries, and fuel fills without
a corresponding attendance check-in.
"""

MISSING_SELFIE = """
SELECT COUNT(CASE WHEN driver_selfie IS NULL OR driver_selfie = '' THEN 1 END) AS missing,
  COUNT(*) AS total
FROM fuel_expense_master
WHERE is_deleted = false AND company_id = $1 AND fuel_expense_id != 12
"""

ODOMETER_ANOMALIES = """
WITH seq AS (
  SELECT fuel_expense_id, bus_id, expense_date, current_odometer,
    LAG(current_odometer) OVER (PARTITION BY bus_id ORDER BY expense_date, fuel_expense_id) AS prev_odo
  FROM fuel_expense_master
  WHERE is_deleted = false AND company_id = $1 AND current_odometer > 0
)
SELECT COUNT(CASE WHEN current_odometer < prev_odo OR current_odometer - prev_odo > 10000 THEN 1 END) AS anomalies,
  COUNT(*) AS total
FROM seq WHERE prev_odo IS NOT NULL
"""

DUPLICATE_FUEL = """
SELECT COUNT(*) AS duplicate_groups FROM (
  SELECT bus_id, expense_date, total_amount
  FROM fuel_expense_master WHERE is_deleted = false AND company_id = $1
  GROUP BY bus_id, expense_date, total_amount HAVING COUNT(*) > 1
) dupes
"""

FUEL_WITHOUT_ATTENDANCE = """
SELECT COUNT(DISTINCT fe.fuel_expense_id) AS count
FROM fuel_expense_master fe
LEFT JOIN user_attendance_master a
  ON fe.user_id = a.user_id AND a.attendance_type = 1 AND a.is_deleted = false
  AND a.created_date >= fe.expense_date::timestamp
  AND a.created_date < (fe.expense_date + INTERVAL '1 day')::timestamp
WHERE fe.is_deleted = false AND fe.company_id = $1
  AND fe.fuel_expense_id != 12
  AND fe.expense_date >= DATE_TRUNC('month', CURRENT_DATE)
  AND a.user_attendance_id IS NULL
"""
