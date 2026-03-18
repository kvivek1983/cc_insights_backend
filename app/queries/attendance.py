"""
SQL query constants for the Attendance Analytics endpoints.

All queries use asyncpg-style parameterized placeholders ($1, $2, ...).
Common rules enforced in all queries:
  - is_deleted = false
  - attendance_type = 1 means Check-In, attendance_type = 2 means Check-Out
  - $1 is always company_id

approval_status reference:
  1 = On time / normal
  4 = No location (geo violation, on time)
  5 = Late (with location)
  7 = Late + no location (geo violation)
"""

DAILY_STATS = """
SELECT
  COUNT(DISTINCT CASE WHEN attendance_type = 1 THEN user_id END) AS present,
  COUNT(DISTINCT CASE WHEN approval_status = 4 AND attendance_type = 1 THEN user_id END) AS present_no_location,
  COUNT(DISTINCT CASE WHEN approval_status = 5 AND attendance_type = 1 THEN user_id END) AS late,
  COUNT(DISTINCT CASE WHEN approval_status = 7 AND attendance_type = 1 THEN user_id END) AS late_no_location,
  COUNT(CASE WHEN attendance_type = 1 THEN 1 END) AS total_check_ins,
  COUNT(CASE WHEN attendance_type = 2 THEN 1 END) AS total_check_outs
FROM user_attendance_master
WHERE is_deleted = false AND company_id = $1
  AND created_date >= CURRENT_DATE::timestamp AND created_date < (CURRENT_DATE + INTERVAL '1 day')::timestamp
"""

WEEKLY_PATTERN = """
SELECT TO_CHAR(created_date, 'Dy') AS day_of_week,
  EXTRACT(DOW FROM created_date) AS dow_num,
  COUNT(DISTINCT CASE WHEN approval_status = 1 THEN user_id END) AS present,
  COUNT(DISTINCT CASE WHEN approval_status IN (5, 7) THEN user_id END) AS late,
  COUNT(DISTINCT CASE WHEN approval_status IN (4, 7) THEN user_id END) AS geo_violation
FROM user_attendance_master
WHERE is_deleted = false AND company_id = $1
  AND attendance_type = 1
  AND created_date >= DATE_TRUNC('week', CURRENT_DATE)
  AND created_date < DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '7 days'
GROUP BY TO_CHAR(created_date, 'Dy'), EXTRACT(DOW FROM created_date)
ORDER BY dow_num
"""

STATUS_BREAKDOWN = """
SELECT approval_status, COUNT(DISTINCT user_id) AS count
FROM user_attendance_master
WHERE is_deleted = false AND company_id = $1
  AND attendance_type = 1
  AND created_date >= CURRENT_DATE::timestamp AND created_date < (CURRENT_DATE + INTERVAL '1 day')::timestamp
GROUP BY approval_status ORDER BY approval_status
"""

DIVISION_DETAIL = """
SELECT d.division_id, d.division_name,
  COUNT(DISTINCT a.user_id) AS present,
  COALESCE(emp.total_employees, 0) AS total,
  ROUND(COUNT(DISTINCT a.user_id)::numeric / NULLIF(emp.total_employees, 0) * 100, 1) AS pct,
  COUNT(DISTINCT CASE WHEN a.approval_status IN (5, 7) THEN a.user_id END) AS late,
  COUNT(DISTINCT CASE WHEN a.approval_status IN (4, 7) THEN a.user_id END) AS geo_violations
FROM user_attendance_master a
JOIN user_company_master ucm ON a.user_id = ucm.user_id AND ucm.is_deleted = false AND ucm.is_active = true AND ucm.division_id > 0
JOIN divisions_of_company_master d ON ucm.division_id = d.division_id AND d.is_deleted = false
LEFT JOIN (
  SELECT ucm2.division_id, COUNT(DISTINCT ucm2.user_id) AS total_employees
  FROM user_company_master ucm2
  JOIN user_master u ON ucm2.user_id = u.user_id AND u.is_deleted = false AND u.is_active = true
  WHERE ucm2.company_id = $1 AND ucm2.is_deleted = false AND ucm2.is_active = true AND ucm2.division_id > 0
  GROUP BY ucm2.division_id
) emp ON d.division_id = emp.division_id
WHERE a.is_deleted = false AND a.company_id = $1
  AND a.attendance_type = 1
  AND a.created_date >= CURRENT_DATE::timestamp AND a.created_date < (CURRENT_DATE + INTERVAL '1 day')::timestamp
GROUP BY d.division_id, d.division_name, emp.total_employees
ORDER BY pct DESC
"""

PEAK_HOURS = """
SELECT EXTRACT(HOUR FROM created_date + INTERVAL '5 hours 30 minutes')::int AS hour_ist,
  COUNT(*) AS checkins
FROM user_attendance_master
WHERE is_deleted = false AND company_id = $1
  AND attendance_type = 1
  AND created_date >= CURRENT_DATE::timestamp AND created_date < (CURRENT_DATE + INTERVAL '1 day')::timestamp
GROUP BY hour_ist ORDER BY hour_ist
"""

WEEKDAY_PATTERN = """
WITH daily AS (
  SELECT created_date::date AS att_date,
    EXTRACT(DOW FROM created_date) AS dow_num,
    TO_CHAR(created_date, 'Dy') AS day_name,
    COUNT(DISTINCT user_id) AS present
  FROM user_attendance_master
  WHERE is_deleted = false AND company_id = $1 AND attendance_type = 1
    AND created_date >= CURRENT_DATE - ($2::text || ' weeks')::interval
    AND created_date < CURRENT_DATE + INTERVAL '1 day'
  GROUP BY att_date, dow_num, day_name
)
SELECT day_name AS day, dow_num, ROUND(AVG(present))::int AS present
FROM daily GROUP BY day_name, dow_num ORDER BY dow_num
"""

WORK_HOURS = """
WITH hours AS (
  SELECT ci.user_id,
    EXTRACT(EPOCH FROM MIN(co.created_date) - MIN(ci.created_date)) / 3600.0 AS work_hours
  FROM user_attendance_master ci
  JOIN user_attendance_master co ON ci.user_id = co.user_id
    AND co.attendance_type = 2 AND co.is_deleted = false AND co.company_id = $1
    AND co.created_date >= CURRENT_DATE::timestamp AND co.created_date < (CURRENT_DATE + INTERVAL '1 day')::timestamp
  WHERE ci.is_deleted = false AND ci.company_id = $1 AND ci.attendance_type = 1
    AND ci.created_date >= CURRENT_DATE::timestamp AND ci.created_date < (CURRENT_DATE + INTERVAL '1 day')::timestamp
  GROUP BY ci.user_id
  HAVING EXTRACT(EPOCH FROM MIN(co.created_date) - MIN(ci.created_date)) / 3600.0 BETWEEN 0 AND 24
)
SELECT ROUND(AVG(work_hours)::numeric, 1) AS avg,
  ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY work_hours)::numeric, 1) AS median,
  ROUND(MIN(work_hours)::numeric, 1) AS min_val,
  ROUND(MAX(work_hours)::numeric, 1) AS max_val
FROM hours
"""

FACE_MATCH_RATE = """
SELECT COUNT(*) AS total,
  COUNT(CASE WHEN ual.is_image_compare = true THEN 1 END) AS matched,
  ROUND(COUNT(CASE WHEN ual.is_image_compare = true THEN 1 END)::numeric / NULLIF(COUNT(*), 0) * 100, 1) AS rate
FROM user_attendance_log ual
JOIN user_company_master ucm ON ual.user_id = ucm.user_id AND ucm.is_deleted = false AND ucm.is_active = true
WHERE ucm.company_id = $1
"""

MONTHLY_TREND = """
WITH daily AS (
  SELECT created_date::date AS att_date,
    COUNT(DISTINCT user_id) AS daily_present,
    COUNT(DISTINCT CASE WHEN approval_status IN (5, 7) THEN user_id END) AS daily_late
  FROM user_attendance_master
  WHERE is_deleted = false AND company_id = $1 AND attendance_type = 1
    AND created_date >= DATE_TRUNC('month', CURRENT_DATE) - ($2::text || ' months')::interval
  GROUP BY att_date
)
SELECT TO_CHAR(DATE_TRUNC('month', att_date), 'Mon') AS month,
  DATE_TRUNC('month', att_date) AS month_date,
  ROUND(AVG(daily_present))::int AS avg_present,
  ROUND(AVG(daily_late))::int AS avg_late
FROM daily
GROUP BY DATE_TRUNC('month', att_date), TO_CHAR(DATE_TRUNC('month', att_date), 'Mon')
ORDER BY month_date
"""

GHOST_DETECTION = """
WITH drivers AS (
  SELECT DISTINCT curm.user_id
  FROM company_user_role_master curm
  JOIN role_master r ON curm.role_id = r.role_id AND r.is_deleted = false
  WHERE curm.company_id = $1 AND curm.is_deleted = false AND curm.is_active = true
    AND UPPER(r.role) LIKE '%DRIVER%'
),
present_drivers AS (
  SELECT DISTINCT a.user_id
  FROM user_attendance_master a
  JOIN drivers d ON a.user_id = d.user_id
  WHERE a.is_deleted = false AND a.company_id = $1 AND a.attendance_type = 1
    AND a.created_date >= CURRENT_DATE::timestamp AND a.created_date < (CURRENT_DATE + INTERVAL '1 day')::timestamp
),
drivers_with_trips AS (
  SELECT DISTINCT br.driver_id AS user_id
  FROM bus_routine_master br
  WHERE br.is_deleted = false AND br.company_id = $1
    AND br.routine_start_date = CURRENT_DATE
    AND br.driver_id IN (SELECT user_id FROM present_drivers)
)
SELECT
  (SELECT COUNT(*) FROM present_drivers) AS drivers_present,
  (SELECT COUNT(*) FROM drivers_with_trips) AS drivers_with_trips,
  (SELECT COUNT(*) FROM present_drivers) - (SELECT COUNT(*) FROM drivers_with_trips) AS ghost_suspect
"""

# Aliases used by routers
ATTENDANCE_DAILY_STATS = DAILY_STATS
ATTENDANCE_WEEKLY_PATTERN = WEEKLY_PATTERN
ATTENDANCE_STATUS_BREAKDOWN = STATUS_BREAKDOWN
ATTENDANCE_DIVISION_DETAIL = DIVISION_DETAIL
ATTENDANCE_PEAK_HOURS = PEAK_HOURS
ATTENDANCE_WEEKDAY_PATTERN = WEEKDAY_PATTERN
ATTENDANCE_WORK_HOURS = WORK_HOURS
ATTENDANCE_FACE_MATCH_RATE = FACE_MATCH_RATE
ATTENDANCE_MONTHLY_TREND = MONTHLY_TREND
ATTENDANCE_GHOST_DETECTION = GHOST_DETECTION

# Total employees query (reused by weekday/monthly trend for pct calculation)
TOTAL_EMPLOYEES_COUNT = """
SELECT COUNT(DISTINCT ucm.user_id) AS total_employees
FROM user_company_master ucm
JOIN user_master u ON ucm.user_id = u.user_id AND u.is_deleted = false AND u.is_active = true
WHERE ucm.company_id = $1 AND ucm.is_deleted = false AND ucm.is_active = true
"""
