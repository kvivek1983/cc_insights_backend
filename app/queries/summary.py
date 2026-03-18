"""
SQL query constants for the Today Summary endpoint.

All queries use asyncpg-style parameterized placeholders ($1, $2, ...).
Common rules enforced in all relevant queries:
  - is_deleted = false
  - fuel_expense_id != 12 (excluded pump type)
  - Fuel quality filters: total_amount < 1000000, volume_in_liter BETWEEN 1 AND 500,
    fuel_price BETWEEN 50 AND 150
  - $1 is always company_id
"""

FUEL_TODAY_YESTERDAY = """
SELECT
  ROUND(SUM(CASE WHEN expense_date = CURRENT_DATE THEN total_amount ELSE 0 END)::numeric, 2) AS today_spend,
  ROUND(SUM(CASE WHEN expense_date = CURRENT_DATE - INTERVAL '1 day' THEN total_amount ELSE 0 END)::numeric, 2) AS yesterday_spend,
  ROUND(SUM(CASE WHEN expense_date = CURRENT_DATE THEN volume_in_liter ELSE 0 END)::numeric, 2) AS today_liters,
  ROUND(SUM(CASE WHEN expense_date = CURRENT_DATE - INTERVAL '1 day' THEN volume_in_liter ELSE 0 END)::numeric, 2) AS yesterday_liters
FROM fuel_expense_master
WHERE is_deleted = false AND company_id = $1
  AND fuel_expense_id != 12
  AND total_amount < 1000000 AND volume_in_liter BETWEEN 1 AND 500 AND fuel_price BETWEEN 50 AND 150
  AND expense_date >= CURRENT_DATE - INTERVAL '1 day'
"""

FUEL_MTD = """
SELECT
  ROUND(SUM(CASE WHEN expense_date >= DATE_TRUNC('month', CURRENT_DATE) THEN total_amount ELSE 0 END)::numeric, 2) AS mtd_spend,
  ROUND(SUM(CASE WHEN expense_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
    AND expense_date < DATE_TRUNC('month', CURRENT_DATE) THEN total_amount ELSE 0 END)::numeric, 2) AS last_month_spend
FROM fuel_expense_master
WHERE is_deleted = false AND company_id = $1
  AND fuel_expense_id != 12
  AND total_amount < 1000000 AND volume_in_liter BETWEEN 1 AND 500 AND fuel_price BETWEEN 50 AND 150
  AND expense_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
"""

ATTENDANCE_TODAY = """
SELECT
  COUNT(DISTINCT user_id) AS present_today,
  COUNT(DISTINCT CASE WHEN approval_status IN (5, 7) THEN user_id END) AS late_arrivals,
  COUNT(DISTINCT CASE WHEN approval_status IN (4, 7) THEN user_id END) AS geo_violations
FROM user_attendance_master
WHERE is_deleted = false AND company_id = $1
  AND attendance_type = 1
  AND created_date >= CURRENT_DATE::timestamp
  AND created_date < (CURRENT_DATE + INTERVAL '1 day')::timestamp
"""

TOTAL_EMPLOYEES = """
SELECT COUNT(DISTINCT ucm.user_id) AS total_employees
FROM user_company_master ucm
JOIN user_master u ON ucm.user_id = u.user_id AND u.is_deleted = false AND u.is_active = true
WHERE ucm.company_id = $1 AND ucm.is_deleted = false AND ucm.is_active = true
"""

MISSING_CHECKOUT = """
SELECT COUNT(*) AS missing_checkout FROM (
  SELECT user_id FROM user_attendance_master
  WHERE is_deleted = false AND company_id = $1
    AND attendance_type = 1
    AND created_date >= CURRENT_DATE::timestamp AND created_date < (CURRENT_DATE + INTERVAL '1 day')::timestamp
  EXCEPT
  SELECT user_id FROM user_attendance_master
  WHERE is_deleted = false AND company_id = $1
    AND attendance_type = 2
    AND created_date >= CURRENT_DATE::timestamp AND created_date < (CURRENT_DATE + INTERVAL '1 day')::timestamp
) AS no_checkout
"""

ROUTES_TODAY = """
SELECT
  COUNT(*) AS total_today,
  COUNT(CASE WHEN actual_day_end_time IS NOT NULL THEN 1 END) AS completed_today
FROM bus_routine_master
WHERE is_deleted = false AND company_id = $1 AND routine_start_date = CURRENT_DATE
"""

ACTIVE_VEHICLES = """
SELECT COUNT(DISTINCT bus_id) AS active_vehicles_today
FROM bus_routine_master
WHERE is_deleted = false AND company_id = $1 AND routine_start_date = CURRENT_DATE
"""

TOTAL_VEHICLES = """
SELECT COUNT(*) AS total_vehicles FROM bus_master
WHERE is_deleted = false AND is_active = true AND company_id = $1
"""

IDLE_VEHICLES = """
SELECT COUNT(*) AS idle_vehicles FROM bus_master b
WHERE b.is_deleted = false AND b.is_active = true AND b.company_id = $1
  AND b.bus_id NOT IN (
    SELECT DISTINCT bus_id FROM bus_routine_master
    WHERE is_deleted = false AND company_id = $1 AND routine_start_date >= CURRENT_DATE - INTERVAL '7 days'
  )
"""

BREAKDOWNS_TODAY = """
SELECT COUNT(*) AS breakdowns_today
FROM bus_breakdown_master bb
JOIN bus_routine_master br ON bb.bus_routine_id = br.bus_routine_id
WHERE bb.is_deleted = false AND br.company_id = $1 AND br.routine_start_date = CURRENT_DATE
"""

AVG_KM_PER_LITER = """
SELECT
  ROUND((SUM(CASE WHEN fe.expense_date >= DATE_TRUNC('month', CURRENT_DATE) THEN br.running_kms ELSE 0 END)::numeric /
    NULLIF(SUM(CASE WHEN fe.expense_date >= DATE_TRUNC('month', CURRENT_DATE) THEN fe.volume_in_liter ELSE 0 END)::numeric, 0)), 2) AS mtd_km_per_liter,
  ROUND((SUM(CASE WHEN fe.expense_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
    AND fe.expense_date < DATE_TRUNC('month', CURRENT_DATE) THEN br.running_kms ELSE 0 END)::numeric /
    NULLIF(SUM(CASE WHEN fe.expense_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
    AND fe.expense_date < DATE_TRUNC('month', CURRENT_DATE) THEN fe.volume_in_liter ELSE 0 END)::numeric, 0)), 2) AS last_month_km_per_liter,
  ROUND(SUM(CASE WHEN fe.expense_date >= DATE_TRUNC('month', CURRENT_DATE) THEN br.running_kms ELSE 0 END)::numeric, 0)::numeric AS mtd_km_covered
FROM fuel_expense_master fe
JOIN bus_routine_master br ON fe.bus_id = br.bus_id AND fe.expense_date = br.routine_start_date
WHERE fe.is_deleted = false AND br.is_deleted = false AND fe.company_id = $1
  AND fe.fuel_expense_id != 12
  AND fe.total_amount < 1000000 AND fe.volume_in_liter BETWEEN 1 AND 500 AND fe.fuel_price BETWEEN 50 AND 150
  AND br.running_kms > 0
  AND fe.expense_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
"""
