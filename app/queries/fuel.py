"""
SQL query constants for the Fuel Analytics endpoints.

All queries use a dedup CTE to exclude duplicate entries (same bus+date+amount+volume,
keeping only the earliest fuel_expense_id per group).

Common rules:
  - is_deleted = false
  - fuel_expense_id != 12
  - Fuel quality: total_amount < 1000000, volume_in_liter BETWEEN 1 AND 500, fuel_price BETWEEN 50 AND 150
  - $1 is always company_id
"""

# $1 = company_id
_FUEL_DEDUP_1 = """
WITH fuel_ranked AS (
  SELECT *, ROW_NUMBER() OVER (
    PARTITION BY bus_id, expense_date, total_amount, volume_in_liter
    ORDER BY fuel_expense_id
  ) AS rn
  FROM fuel_expense_master
  WHERE is_deleted = false AND company_id = $1
    AND fuel_expense_id != 12
    AND total_amount < 1000000 AND volume_in_liter BETWEEN 1 AND 500 AND fuel_price BETWEEN 50 AND 150
),
fuel AS (SELECT * FROM fuel_ranked WHERE rn = 1)
"""

FUEL_TREND_DAILY = _FUEL_DEDUP_1 + """
SELECT expense_date AS date,
  TO_CHAR(expense_date, 'DD Mon (Dy)') AS display_label,
  ROUND(SUM(total_amount)::numeric, 2) AS total_spend,
  ROUND(SUM(volume_in_liter)::numeric, 2) AS total_liters,
  COUNT(*) AS fill_count
FROM fuel
WHERE expense_date >= CURRENT_DATE - ($2::text || ' days')::interval AND expense_date <= CURRENT_DATE
GROUP BY expense_date ORDER BY expense_date ASC
"""

FUEL_TREND_MONTHLY = _FUEL_DEDUP_1 + """
SELECT TO_CHAR(expense_date, 'YYYY-MM') AS month,
  TO_CHAR(DATE_TRUNC('month', expense_date), 'Mon YYYY') AS display_label,
  ROUND(SUM(total_amount)::numeric, 2) AS total_spend,
  ROUND(SUM(volume_in_liter)::numeric, 2) AS total_liters,
  ROUND(AVG(fuel_price)::numeric, 2) AS avg_price_per_liter
FROM fuel
WHERE expense_date >= DATE_TRUNC('month', CURRENT_DATE) - ($2::text || ' months')::interval
GROUP BY TO_CHAR(expense_date, 'YYYY-MM'), DATE_TRUNC('month', expense_date)
ORDER BY month ASC
"""

FUEL_PAYMENT_MODES = _FUEL_DEDUP_1 + """
SELECT COALESCE(NULLIF(payment_mode, ''), 'Unknown') AS payment_mode,
  COUNT(*) AS transaction_count,
  ROUND(SUM(total_amount)::numeric, 2) AS total_amount,
  ROUND(SUM(volume_in_liter)::numeric, 2) AS total_liters,
  ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 1) AS percentage
FROM fuel
WHERE expense_date >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY payment_mode ORDER BY transaction_count DESC
"""

FUEL_TOP_CONSUMERS = _FUEL_DEDUP_1 + """
SELECT b.bus_id, b.registration_number,
  ROUND(SUM(fe.volume_in_liter)::numeric, 2) AS total_liters,
  ROUND(SUM(fe.total_amount)::numeric, 2) AS total_amount,
  COUNT(*) AS fill_count,
  ROUND(SUM(COALESCE(br_agg.running_kms, 0))::numeric / NULLIF(SUM(fe.volume_in_liter)::numeric, 0), 2) AS km_per_liter
FROM fuel fe
JOIN bus_master b ON fe.bus_id = b.bus_id AND b.is_deleted = false
LEFT JOIN (
  SELECT bus_id, routine_start_date, SUM(running_kms) AS running_kms
  FROM bus_routine_master WHERE is_deleted = false AND company_id = $1
    AND routine_start_date >= DATE_TRUNC('month', CURRENT_DATE)
  GROUP BY bus_id, routine_start_date
) br_agg ON fe.bus_id = br_agg.bus_id AND fe.expense_date = br_agg.routine_start_date
WHERE fe.expense_date >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY b.bus_id, b.registration_number
ORDER BY total_liters DESC LIMIT $2
"""

FUEL_DIVISION_SPEND = _FUEL_DEDUP_1 + """
SELECT d.division_id, d.division_name,
  ROUND(SUM(fe.total_amount)::numeric, 2) AS total_spend,
  ROUND(SUM(fe.volume_in_liter)::numeric, 2) AS total_liters,
  ROUND(SUM(fe.total_amount)::numeric / 100000, 2) AS spend_lakhs,
  COUNT(*) AS fill_count
FROM fuel fe
JOIN divisions_of_company_master d ON fe.division_id = d.division_id AND d.is_deleted = false
WHERE fe.expense_date >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY d.division_id, d.division_name ORDER BY total_spend DESC
"""
