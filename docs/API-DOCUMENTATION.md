# OneCheck Dashboard API — Frontend Integration Guide

> **Base URL:** `{NEXT_PUBLIC_API_BASE_URL}/api/v1/dashboard`
>
> Set `NEXT_PUBLIC_API_BASE_URL` as an environment variable in your Next.js project (e.g. `https://api.onecheck.example.com`).

---

## Table of Contents

1. [Common Response Envelope](#common-response-envelope)
2. [Common Query Parameters](#common-query-parameters)
3. [Error Response](#error-response)
4. [CEO View Endpoints](#ceo-view-endpoints)
5. [Operations View Endpoints](#operations-view-endpoints)
6. [Attendance Tab Endpoints](#attendance-tab-endpoints)
7. [Notes](#notes)

---

## Common Response Envelope

Every endpoint returns the same top-level wrapper:

```typescript
interface ApiResponse<T> {
  success: boolean;       // Always true on 2xx
  data: T;                // Payload — shape varies per endpoint (documented below)
  meta: {
    generated_at: string; // ISO 8601 UTC timestamp — convert to IST (+5:30) for display
    company_id: number;
    filters_applied: Record<string, unknown>; // Echoes back active query params
  };
}
```

**Example envelope (abbreviated):**

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "generated_at": "2026-03-18T10:18:16.219542",
    "company_id": 15,
    "filters_applied": { "date": "today" }
  }
}
```

---

## Common Query Parameters

These parameters are accepted by most endpoints. Refer to each endpoint's own parameter table for what is actually supported.

| Parameter     | Type    | Default    | Description                                                  |
|---------------|---------|------------|--------------------------------------------------------------|
| `company_id`  | integer | `15`       | Tenant identifier. Always pass this explicitly.              |
| `date`        | string  | today      | ISO date string `YYYY-MM-DD` for single-day filters.        |
| `start_date`  | string  | —          | Start of date range, `YYYY-MM-DD`.                          |
| `end_date`    | string  | —          | End of date range (inclusive), `YYYY-MM-DD`.                |
| `division_id` | integer | —          | Filter to a single division. Omit for company-wide results. |

---

## Error Response

When `success` is `false`, the shape is:

```json
{
  "success": false,
  "detail": "Human-readable error message"
}
```

HTTP status codes follow standard conventions: `400` for bad input, `404` for not found, `500` for server errors.

---

## CEO View Endpoints

---

### 1. GET /summary/today

**Purpose:** Returns a single-call snapshot of all key KPIs for today — fuel, attendance, fleet, routes, and breakdowns.

**Used in:** CEO View — top KPI cards

**Query Parameters:**

| Parameter    | Type    | Default | Description          |
|--------------|---------|---------|----------------------|
| `company_id` | integer | `15`    | Tenant identifier.   |

**Response Schema:**

```typescript
interface TodaySummaryData {
  fuel: {
    today_spend: number;               // INR
    yesterday_spend: number;           // INR
    today_liters: number;
    yesterday_liters: number;
    mtd_spend: number;                 // Month-to-date INR
    last_month_spend: number;          // INR
    avg_km_per_liter_mtd: number;
    avg_km_per_liter_last_month: number;
    mtd_km_covered: number;
  };
  attendance: {
    present_today: number;
    total_employees: number;
    late_arrivals: number;
    geo_violations: number;
    missing_checkout: number;
  };
  fleet: {
    active_vehicles_today: number;
    total_vehicles: number;
    idle_vehicles_7d: number;          // Idle for last 7 days
  };
  routes: {
    completed_today: number;
    total_today: number;
  };
  breakdowns: {
    count_today: number;
  };
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "fuel": {
      "today_spend": 934546.21,
      "yesterday_spend": 2773555.04,
      "today_liters": 9977.93,
      "yesterday_liters": 29629.7,
      "mtd_spend": 44916429.09,
      "last_month_spend": 67527950.09,
      "avg_km_per_liter_mtd": 2.13,
      "avg_km_per_liter_last_month": 4.85,
      "mtd_km_covered": 718151.0
    },
    "attendance": {
      "present_today": 782,
      "total_employees": 1857,
      "late_arrivals": 779,
      "geo_violations": 331,
      "missing_checkout": 370
    },
    "fleet": {
      "active_vehicles_today": 706,
      "total_vehicles": 975,
      "idle_vehicles_7d": 161
    },
    "routes": {
      "completed_today": 2,
      "total_today": 715
    },
    "breakdowns": {
      "count_today": 1
    }
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:16.219542",
    "company_id": 15,
    "filters_applied": { "date": "today" }
  }
}
```

---

### 2. GET /fuel/trend-daily

**Purpose:** Returns daily fuel spend and volume for the last N days (including today), used to render a bar/line chart.

**Used in:** CEO View — Fuel Trend (Daily) chart

**Query Parameters:**

| Parameter    | Type    | Default | Description                                     |
|--------------|---------|---------|-------------------------------------------------|
| `company_id` | integer | `15`    | Tenant identifier.                              |
| `days`       | integer | `3`     | Number of past days to include (plus today).    |

**Response Schema:**

```typescript
interface FuelDailyTrendData {
  days: Array<{
    date: string;           // YYYY-MM-DD
    display_label: string;  // e.g. "18 Mar (Wed)" — ready for chart axis labels
    total_spend: number;    // INR
    total_liters: number;
    fill_count: number;     // Number of fuel fill transactions
  }>;
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "days": [
      {
        "date": "2026-03-15",
        "display_label": "15 Mar (Sun)",
        "total_spend": 2585809.16,
        "total_liters": 27622.5,
        "fill_count": 295
      },
      {
        "date": "2026-03-16",
        "display_label": "16 Mar (Mon)",
        "total_spend": 2977708.96,
        "total_liters": 31810.11,
        "fill_count": 328
      },
      {
        "date": "2026-03-17",
        "display_label": "17 Mar (Tue)",
        "total_spend": 2773555.04,
        "total_liters": 29629.7,
        "fill_count": 297
      },
      {
        "date": "2026-03-18",
        "display_label": "18 Mar (Wed)",
        "total_spend": 934546.21,
        "total_liters": 9977.93,
        "fill_count": 105
      }
    ]
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:16.314708",
    "company_id": 15,
    "filters_applied": { "days": 3 }
  }
}
```

---

### 3. GET /fuel/trend-monthly

**Purpose:** Returns monthly fuel spend, volume, and average price-per-liter for the last N months, used to render a monthly comparison chart.

**Used in:** CEO View — Fuel Trend (Monthly) chart

**Query Parameters:**

| Parameter    | Type    | Default | Description                               |
|--------------|---------|---------|-------------------------------------------|
| `company_id` | integer | `15`    | Tenant identifier.                        |
| `months`     | integer | `2`     | Number of previous months to include.     |

**Response Schema:**

```typescript
interface FuelMonthlyTrendData {
  months: Array<{
    month: string;               // YYYY-MM
    display_label: string;       // e.g. "Jan 2026" — ready for chart axis labels
    total_spend: number;         // INR
    total_liters: number;
    avg_price_per_liter: number; // INR/litre
  }>;
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "months": [
      {
        "month": "2026-01",
        "display_label": "Jan 2026",
        "total_spend": 63753578.01,
        "total_liters": 681779.6,
        "avg_price_per_liter": 93.56
      },
      {
        "month": "2026-02",
        "display_label": "Feb 2026",
        "total_spend": 67527950.09,
        "total_liters": 721363.94,
        "avg_price_per_liter": 93.65
      },
      {
        "month": "2026-03",
        "display_label": "Mar 2026",
        "total_spend": 44916429.09,
        "total_liters": 479795.99,
        "avg_price_per_liter": 93.65
      }
    ]
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:16.439052",
    "company_id": 15,
    "filters_applied": { "months": 2 }
  }
}
```

---

### 4. GET /fuel/payment-modes

**Purpose:** Breaks down MTD fuel spend by payment mode (Bowser, OTP, NEFT), suitable for a pie or donut chart.

**Used in:** CEO View — Payment Mode split chart

**Query Parameters:**

| Parameter    | Type    | Default | Description        |
|--------------|---------|---------|--------------------|
| `company_id` | integer | `15`    | Tenant identifier. |

**Response Schema:**

```typescript
interface PaymentModeSplitData {
  modes: Array<{
    payment_mode: string;      // e.g. "Bowser", "OTP", "NEFT"
    transaction_count: number;
    total_amount: number;      // INR
    total_liters: number;
    percentage: number;        // % of total liters
  }>;
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "modes": [
      {
        "payment_mode": "Bowser",
        "transaction_count": 2664,
        "total_amount": 21170868.67,
        "total_liters": 225947.1,
        "percentage": 47.13
      },
      {
        "payment_mode": "OTP",
        "transaction_count": 2108,
        "total_amount": 21785828.23,
        "total_liters": 232890.58,
        "percentage": 48.5
      },
      {
        "payment_mode": "NEFT",
        "transaction_count": 199,
        "total_amount": 1959732.2,
        "total_liters": 20958.31,
        "percentage": 4.36
      }
    ]
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:16.529444",
    "company_id": 15,
    "filters_applied": {}
  }
}
```

---

### 5. GET /divisions/performance

**Purpose:** Returns a ranked list of divisions with key performance metrics: attendance %, fuel spend, route completion, and breakdown count.

**Used in:** CEO View — Division Performance table/heatmap

**Query Parameters:**

| Parameter    | Type    | Default | Description                                       |
|--------------|---------|---------|---------------------------------------------------|
| `company_id` | integer | `15`    | Tenant identifier.                                |
| `limit`      | integer | `10`    | Maximum number of divisions to return.            |

**Response Schema:**

```typescript
interface DivisionPerformanceData {
  divisions: Array<{
    division_id: number;
    division_name: string;
    attendance_percentage: number;   // 0–100
    fuel_spend_lakhs: number;        // INR in lakhs (1 lakh = 100,000)
    route_completion_pct: number;    // 0–100
    breakdown_count: number;
  }>;
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "divisions": [
      {
        "division_id": 45,
        "division_name": "Bhadrak",
        "attendance_percentage": 68.6,
        "fuel_spend_lakhs": 10.86,
        "route_completion_pct": 0.0,
        "breakdown_count": 0
      },
      {
        "division_id": 55,
        "division_name": "Jharsuguda",
        "attendance_percentage": 66.7,
        "fuel_spend_lakhs": 8.78,
        "route_completion_pct": 0.0,
        "breakdown_count": 2
      },
      {
        "division_id": 41,
        "division_name": "Malkangiri",
        "attendance_percentage": 58.7,
        "fuel_spend_lakhs": 21.05,
        "route_completion_pct": 0.0,
        "breakdown_count": 27
      }
    ]
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:17.037244",
    "company_id": 15,
    "filters_applied": { "limit": 3 }
  }
}
```

---

### 6. GET /alerts

**Purpose:** Returns a list of recent actionable alerts (e.g. repeat breakdowns, anomalies), sorted by severity.

**Used in:** CEO View — Alerts panel

**Query Parameters:**

| Parameter    | Type    | Default | Description                              |
|--------------|---------|---------|------------------------------------------|
| `company_id` | integer | `15`    | Tenant identifier.                       |
| `limit`      | integer | `10`    | Maximum number of alerts to return.      |

**Response Schema:**

```typescript
interface DashboardAlertsData {
  alerts: Array<{
    id: string;            // Unique alert ID, e.g. "alert-breakdown-0"
    type: string;          // Severity: "critical" | "warning" | "info"
    category: string;      // Domain: "breakdown" | "fuel" | "attendance" | etc.
    message: string;       // Human-readable alert text — display directly
    detail: string;        // Entity identifier, e.g. vehicle registration number
    timestamp: string;     // ISO 8601 UTC datetime
    entity_id: number | null; // Related entity ID (bus_id, employee_id, etc.)
  }>;
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "alerts": [
      {
        "id": "alert-breakdown-0",
        "type": "critical",
        "category": "breakdown",
        "message": "OD18M3373 — 5 breakdowns this week (Maintenance)",
        "detail": "OD18M3373",
        "timestamp": "2026-03-17T08:25:06.998207",
        "entity_id": 443
      },
      {
        "id": "alert-breakdown-1",
        "type": "critical",
        "category": "breakdown",
        "message": "OD30F1907 — 4 breakdowns this week (Maintenance)",
        "detail": "OD30F1907",
        "timestamp": "2026-03-15T03:15:15.684797",
        "entity_id": 328
      },
      {
        "id": "alert-breakdown-2",
        "type": "critical",
        "category": "breakdown",
        "message": "OD08V3208 — 3 breakdowns this week (Other)",
        "detail": "OD08V3208",
        "timestamp": "2026-03-18T01:58:30.934591",
        "entity_id": 211
      }
    ]
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:17.676127",
    "company_id": 15,
    "filters_applied": { "limit": 3 }
  }
}
```

---

## Operations View Endpoints

---

### 7. GET /attendance/daily-stats

**Purpose:** Returns a detailed attendance count for a specific date — check-ins, check-outs, late, geo-violations, and anomalies.

**Used in:** Operations View — Daily Attendance stats row

**Query Parameters:**

| Parameter    | Type    | Default | Description                              |
|--------------|---------|---------|------------------------------------------|
| `company_id` | integer | `15`    | Tenant identifier.                       |
| `date`       | string  | today   | Date to query, `YYYY-MM-DD`.             |
| `division_id`| integer | —       | Filter to a single division (optional).  |

**Response Schema:**

```typescript
interface AttendanceDailyStatsData {
  date: string;                  // YYYY-MM-DD
  total_employees: number;
  present: number;
  present_no_location: number;   // Checked in but no GPS location recorded
  late: number;
  late_no_location: number;      // Late AND missing location
  total_check_ins: number;
  total_check_outs: number;
  missing_checkout: number;      // Checked in but no corresponding check-out
  fuel_without_attendance: number; // Fuel entries with no attendance record
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "date": "2026-03-18",
    "total_employees": 0,
    "present": 782,
    "present_no_location": 2,
    "late": 448,
    "late_no_location": 331,
    "total_check_ins": 801,
    "total_check_outs": 592,
    "missing_checkout": 0,
    "fuel_without_attendance": 0
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:17.768060",
    "company_id": 15,
    "filters_applied": {}
  }
}
```

---

### 8. GET /attendance/weekly-pattern

**Purpose:** Returns aggregated attendance counts (present, late, geo-violations) grouped by day of week for the current week.

**Used in:** Operations View — Weekly Attendance pattern chart

**Query Parameters:**

| Parameter    | Type    | Default | Description        |
|--------------|---------|---------|--------------------|
| `company_id` | integer | `15`    | Tenant identifier. |

**Response Schema:**

```typescript
interface WeeklyAttendancePatternData {
  days: Array<{
    day_of_week: string;   // "Mon" | "Tue" | "Wed" | "Thu" | "Fri" | "Sat" | "Sun"
    present: number;
    late: number;
    geo_violation: number;
  }>;
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "days": [
      { "day_of_week": "Mon", "present": 244, "late": 886, "geo_violation": 475 },
      { "day_of_week": "Tue", "present": 285, "late": 906, "geo_violation": 450 },
      { "day_of_week": "Wed", "present": 4,   "late": 779, "geo_violation": 331 }
    ]
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:17.923970",
    "company_id": 15,
    "filters_applied": {}
  }
}
```

---

### 9. GET /routes/completion-by-tier

**Purpose:** Returns route completion statistics broken down by route tier, including scheduled vs. actual trips and kilometres.

**Used in:** Operations View — Route Completion by Tier table

**Query Parameters:**

| Parameter    | Type    | Default | Description        |
|--------------|---------|---------|--------------------|
| `company_id` | integer | `15`    | Tenant identifier. |
| `date`       | string  | today   | Date to query, `YYYY-MM-DD`. |

**Response Schema:**

```typescript
interface RouteCompletionByTierData {
  tiers: Array<{
    tier: string;              // Route tier identifier, e.g. "1"
    scheduled_trips: number;
    actual_trips: number;
    scheduled_km: number;
    actual_km: number;         // Note: can be negative due to odometer anomalies
    completion_pct: number;    // actual_trips / scheduled_trips * 100
  }>;
  total: {
    scheduled_trips: number;
    actual_trips: number;
    completion_pct: number;
  };
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "tiers": [
      {
        "tier": "1",
        "scheduled_trips": 4984,
        "actual_trips": 2,
        "scheduled_km": 259878.0,
        "actual_km": -329210.0,
        "completion_pct": 0.04
      }
    ],
    "total": {
      "scheduled_trips": 4984,
      "actual_trips": 2,
      "completion_pct": 0.04
    }
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:20.672169",
    "company_id": 15,
    "filters_applied": {}
  }
}
```

> **Note:** `actual_km` can be negative when odometer readings are anomalous. Do not render negative values as-is; show a warning indicator instead.

---

### 10. GET /fuel/top-consumers

**Purpose:** Returns the top N vehicles ranked by total fuel consumption (litres) within the current MTD period.

**Used in:** Operations View — Top Fuel Consumers table

**Query Parameters:**

| Parameter    | Type    | Default | Description                              |
|--------------|---------|---------|------------------------------------------|
| `company_id` | integer | `15`    | Tenant identifier.                       |
| `limit`      | integer | `10`    | Number of top vehicles to return.        |
| `start_date` | string  | MTD     | Override start date, `YYYY-MM-DD`.       |
| `end_date`   | string  | today   | Override end date, `YYYY-MM-DD`.         |

**Response Schema:**

```typescript
interface TopFuelConsumersData {
  vehicles: Array<{
    bus_id: number;
    registration_number: string;
    total_liters: number;
    total_amount: number;        // INR
    fill_count: number;
    km_per_liter: number | null; // null or 0.0 when odometer data unavailable
  }>;
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "vehicles": [
      {
        "bus_id": 410,
        "registration_number": "OD18M8085",
        "total_liters": 2156.54,
        "total_amount": 203232.33,
        "fill_count": 9,
        "km_per_liter": 0.0
      },
      {
        "bus_id": 1071,
        "registration_number": "OD10AA3952",
        "total_liters": 2012.78,
        "total_amount": 189684.39,
        "fill_count": 9,
        "km_per_liter": 0.0
      },
      {
        "bus_id": 1065,
        "registration_number": "OD08X4547",
        "total_liters": 1911.52,
        "total_amount": 180141.64,
        "fill_count": 8,
        "km_per_liter": 0.0
      }
    ]
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:16.746504",
    "company_id": 15,
    "filters_applied": { "limit": 3 }
  }
}
```

---

### 11. GET /breakdowns/repeat-vehicles

**Purpose:** Returns vehicles with the highest number of breakdowns within the selected period, helping identify chronic maintenance problems.

**Used in:** Operations View — Repeat Breakdown Vehicles table

**Query Parameters:**

| Parameter    | Type    | Default | Description                              |
|--------------|---------|---------|------------------------------------------|
| `company_id` | integer | `15`    | Tenant identifier.                       |
| `limit`      | integer | `10`    | Number of top vehicles to return.        |
| `start_date` | string  | MTD     | Override start date, `YYYY-MM-DD`.       |
| `end_date`   | string  | today   | Override end date, `YYYY-MM-DD`.         |

**Response Schema:**

```typescript
interface RepeatBreakdownVehiclesData {
  vehicles: Array<{
    bus_id: number;
    registration_number: string;
    breakdown_count: number;
    last_breakdown_date: string;  // YYYY-MM-DD
    last_reason: string;          // e.g. "Maintenance", "Accident"
  }>;
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "vehicles": [
      {
        "bus_id": 328,
        "registration_number": "OD30F1907",
        "breakdown_count": 27,
        "last_breakdown_date": "2026-03-14",
        "last_reason": "Maintenance"
      },
      {
        "bus_id": 352,
        "registration_number": "OD30F2058",
        "breakdown_count": 24,
        "last_breakdown_date": "2026-03-14",
        "last_reason": "Maintenance"
      },
      {
        "bus_id": 333,
        "registration_number": "OD30F1934",
        "breakdown_count": 22,
        "last_breakdown_date": "2026-02-02",
        "last_reason": "Maintenance"
      }
    ]
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:21.007341",
    "company_id": 15,
    "filters_applied": { "limit": 3 }
  }
}
```

---

### 12. GET /breakdowns/reasons

**Purpose:** Returns a breakdown of all reported breakdown events grouped and ranked by reason, suitable for a pie chart or ranked list.

**Used in:** Operations View — Breakdown Reasons chart

**Query Parameters:**

| Parameter    | Type    | Default | Description        |
|--------------|---------|---------|--------------------|
| `company_id` | integer | `15`    | Tenant identifier. |
| `start_date` | string  | MTD     | Override start date, `YYYY-MM-DD`. |
| `end_date`   | string  | today   | Override end date, `YYYY-MM-DD`.   |

**Response Schema:**

```typescript
interface BreakdownReasonsData {
  reasons: Array<{
    reason_id: number;
    reason_text: string;   // e.g. "Maintenance", "Accident", "Other"
    count: number;
    percentage: number;    // % of total breakdowns
  }>;
  total: number;           // Total breakdown events in the period
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "reasons": [
      { "reason_id": 6,    "reason_text": "Maintenance",    "count": 50, "percentage": 62.5 },
      { "reason_id": 1,    "reason_text": "Accident",       "count": 3,  "percentage": 3.75 },
      { "reason_id": 1111, "reason_text": "Other",          "count": 2,  "percentage": 2.5  },
      { "reason_id": 8,    "reason_text": "Wrong Survey",   "count": 1,  "percentage": 1.25 },
      { "reason_id": 3,    "reason_text": "Driver",         "count": 1,  "percentage": 1.25 },
      { "reason_id": 4,    "reason_text": "Incident",       "count": 1,  "percentage": 1.25 },
      { "reason_id": 5,    "reason_text": "For Diesel Pump","count": 1,  "percentage": 1.25 }
    ],
    "total": 80
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:20.758324",
    "company_id": 15,
    "filters_applied": {}
  }
}
```

> **Note:** `reason_id: 1111` is a catch-all "Other" bucket. Multiple entries with the same `reason_text` may appear; aggregate them on the frontend if displaying a unique list.

---

### 13. GET /fuel/division-spend

**Purpose:** Returns MTD fuel spend, volume, and fill count for every division, ranked by total spend — useful for a horizontal bar chart or sortable table.

**Used in:** Operations View — Division Fuel Spend breakdown

**Query Parameters:**

| Parameter    | Type    | Default | Description        |
|--------------|---------|---------|--------------------|
| `company_id` | integer | `15`    | Tenant identifier. |
| `start_date` | string  | MTD     | Override start date, `YYYY-MM-DD`. |
| `end_date`   | string  | today   | Override end date, `YYYY-MM-DD`.   |

**Response Schema:**

```typescript
interface DivisionFuelSpendData {
  divisions: Array<{
    division_id: number;
    division_name: string;
    total_spend: number;    // INR
    total_liters: number;
    spend_lakhs: number;    // total_spend / 100,000 — use for display
    fill_count: number;
  }>;
}
```

**Sample Response (first 3 of 24 divisions shown):**

```json
{
  "success": true,
  "data": {
    "divisions": [
      {
        "division_id": 51,
        "division_name": "Mayurbhanj",
        "total_spend": 5912816.38,
        "total_liters": 63346.26,
        "spend_lakhs": 59.13,
        "fill_count": 642
      },
      {
        "division_id": 52,
        "division_name": "Bargarh",
        "total_spend": 4006106.47,
        "total_liters": 42623.54,
        "spend_lakhs": 40.06,
        "fill_count": 512
      },
      {
        "division_id": 44,
        "division_name": "Balasore",
        "total_spend": 2718073.13,
        "total_liters": 29286.5,
        "spend_lakhs": 27.18,
        "fill_count": 270
      }
      // ... 21 more divisions
    ]
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:16.845022",
    "company_id": 15,
    "filters_applied": {}
  }
}
```

---

### 14. GET /data-quality/snapshot

**Purpose:** Returns a set of data quality health metrics (missing selfies, odometer anomalies, duplicate entries, etc.) with severity ratings to highlight data integrity issues.

**Used in:** Operations View — Data Quality panel

**Query Parameters:**

| Parameter    | Type    | Default | Description        |
|--------------|---------|---------|--------------------|
| `company_id` | integer | `15`    | Tenant identifier. |

**Response Schema:**

```typescript
interface DataQualitySnapshotData {
  metrics: Array<{
    key: string;         // Stable machine key, e.g. "missing_selfie"
    label: string;       // Human-readable label for display
    value_pct: number;   // Percentage value (may be 0.0 when count-only)
    count: number;       // Raw count of affected records
    note: string;        // Contextual note string — display as subtitle
    severity: "red" | "amber" | "green"; // Use for colour coding
  }>;
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "metrics": [
      {
        "key": "missing_selfie",
        "label": "Missing Driver Selfie",
        "value_pct": 31.6,
        "count": 19717,
        "note": "19,717 of 62,458 records",
        "severity": "red"
      },
      {
        "key": "odometer_anomalies",
        "label": "Odometer Anomalies",
        "value_pct": 3.3,
        "count": 1995,
        "note": "1,995 anomalies",
        "severity": "green"
      },
      {
        "key": "duplicate_fuel",
        "label": "Duplicate Fuel Entries",
        "value_pct": 0.0,
        "count": 171,
        "note": "171 duplicate groups",
        "severity": "amber"
      },
      {
        "key": "fuel_without_attendance",
        "label": "Fuel Without Attendance",
        "value_pct": 0.0,
        "count": 1056,
        "note": "1056 entries (MTD)",
        "severity": "red"
      }
    ]
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:21.946321",
    "company_id": 15,
    "filters_applied": {}
  }
}
```

---

## Attendance Tab Endpoints

---

### 15. GET /attendance/status-breakdown

**Purpose:** Returns a categorised count of today's attendance statuses (on-time, late, geo-violation combinations) with suggested chart colours.

**Used in:** Attendance Tab — Status Donut chart

**Query Parameters:**

| Parameter    | Type    | Default | Description                             |
|--------------|---------|---------|------------------------------------------|
| `company_id` | integer | `15`    | Tenant identifier.                       |
| `date`       | string  | today   | Date to query, `YYYY-MM-DD`.             |
| `division_id`| integer | —       | Filter to a single division (optional).  |

**Response Schema:**

```typescript
interface AttendanceStatusBreakdownData {
  statuses: Array<{
    name: string;    // Label, e.g. "Present (On-time)", "Late + No Location"
    value: number;   // Count of employees in this status
    color: string;   // Hex color string — use directly in chart config
  }>;
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "statuses": [
      { "name": "Present (On-time)",    "value": 4,   "color": "#10B981" },
      { "name": "Present + No Location","value": 2,   "color": "#8B5CF6" },
      { "name": "Late",                 "value": 448, "color": "#F59E0B" },
      { "name": "Late + No Location",   "value": 331, "color": "#EF4444" }
    ]
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:18.168267",
    "company_id": 15,
    "filters_applied": {}
  }
}
```

---

### 16. GET /attendance/division-detail

**Purpose:** Returns per-division attendance statistics for today — present count, total headcount, attendance %, late count, and geo-violations.

**Used in:** Attendance Tab — Division Attendance table

**Query Parameters:**

| Parameter    | Type    | Default | Description                             |
|--------------|---------|---------|------------------------------------------|
| `company_id` | integer | `15`    | Tenant identifier.                       |
| `date`       | string  | today   | Date to query, `YYYY-MM-DD`.             |

**Response Schema:**

```typescript
interface AttendanceDivisionDetailData {
  divisions: Array<{
    division_id: number;
    division_name: string;
    present: number;
    total: number;
    pct: number;          // present / total * 100
    late: number;
    geo_violations: number;
  }>;
}
```

**Sample Response (first 3 of 25 divisions shown):**

```json
{
  "success": true,
  "data": {
    "divisions": [
      {
        "division_id": 45,
        "division_name": "Bhadrak",
        "present": 35,
        "total": 51,
        "pct": 68.63,
        "late": 35,
        "geo_violations": 11
      },
      {
        "division_id": 55,
        "division_name": "Jharsuguda",
        "present": 18,
        "total": 27,
        "pct": 66.67,
        "late": 18,
        "geo_violations": 4
      },
      {
        "division_id": 41,
        "division_name": "Malkangiri",
        "present": 44,
        "total": 75,
        "pct": 58.67,
        "late": 44,
        "geo_violations": 26
      }
      // ... 22 more divisions
    ]
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:18.251346",
    "company_id": 15,
    "filters_applied": {}
  }
}
```

---

### 17. GET /attendance/peak-hours

**Purpose:** Returns the distribution of check-in events by hour of day for today, used to render a histogram showing peak arrival times.

**Used in:** Attendance Tab — Peak Hours bar chart

**Query Parameters:**

| Parameter    | Type    | Default | Description                             |
|--------------|---------|---------|------------------------------------------|
| `company_id` | integer | `15`    | Tenant identifier.                       |
| `date`       | string  | today   | Date to query, `YYYY-MM-DD`.             |
| `division_id`| integer | —       | Filter to a single division (optional).  |

**Response Schema:**

```typescript
interface PeakHourDistributionData {
  hours: Array<{
    hour: string;      // Human-readable label, e.g. "5 AM", "12 PM" — use as axis label
    checkins: number;
  }>;
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "hours": [
      { "hour": "5 AM",  "checkins": 417 },
      { "hour": "6 AM",  "checkins": 108 },
      { "hour": "7 AM",  "checkins": 42  },
      { "hour": "8 AM",  "checkins": 43  },
      { "hour": "9 AM",  "checkins": 61  },
      { "hour": "10 AM", "checkins": 32  },
      { "hour": "11 AM", "checkins": 24  },
      { "hour": "12 PM", "checkins": 35  },
      { "hour": "1 PM",  "checkins": 24  },
      { "hour": "2 PM",  "checkins": 12  },
      { "hour": "3 PM",  "checkins": 3   }
    ]
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:18.334594",
    "company_id": 15,
    "filters_applied": { "hour_format": "e.g. 5 AM, 6 AM" }
  }
}
```

---

### 18. GET /attendance/weekday-pattern

**Purpose:** Returns average attendance presence count and percentage for each weekday over the last N weeks, to identify day-of-week trends.

**Used in:** Attendance Tab — Weekday Pattern chart

**Query Parameters:**

| Parameter    | Type    | Default | Description                           |
|--------------|---------|---------|---------------------------------------|
| `company_id` | integer | `15`    | Tenant identifier.                    |
| `weeks`      | integer | `4`     | Number of past weeks to average over. |

**Response Schema:**

```typescript
interface WeekdayPatternData {
  days: Array<{
    day: string;     // "Sun" | "Mon" | "Tue" | "Wed" | "Thu" | "Fri" | "Sat"
    present: number; // Rounded average present count across weeks
    pct: number;     // Average attendance percentage
  }>;
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "days": [
      { "day": "Sun", "present": 1135, "pct": 61.12 },
      { "day": "Mon", "present": 1168, "pct": 62.9  },
      { "day": "Tue", "present": 1156, "pct": 62.25 },
      { "day": "Wed", "present": 1075, "pct": 57.89 },
      { "day": "Thu", "present": 1143, "pct": 61.55 },
      { "day": "Fri", "present": 1158, "pct": 62.36 },
      { "day": "Sat", "present": 1166, "pct": 62.79 }
    ]
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:18.902051",
    "company_id": 15,
    "filters_applied": { "weeks": 4 }
  }
}
```

---

### 19. GET /attendance/work-hours

**Purpose:** Returns statistical summary of work-hours (duration between check-in and check-out) for today — average, median, min, and max.

**Used in:** Attendance Tab — Work Hours summary card

**Query Parameters:**

| Parameter    | Type    | Default | Description                             |
|--------------|---------|---------|------------------------------------------|
| `company_id` | integer | `15`    | Tenant identifier.                       |
| `date`       | string  | today   | Date to query, `YYYY-MM-DD`.             |
| `division_id`| integer | —       | Filter to a single division (optional).  |

**Response Schema:**

```typescript
interface WorkHoursStatsData {
  avg: number;      // Average hours worked
  median: number;   // Median hours worked
  min_val: number;  // Minimum (may be 0.0 for employees who only checked in)
  max_val: number;  // Maximum
  caveat: string;   // Important data quality note — display near the stats
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "avg": 3.9,
    "median": 4.9,
    "min_val": 0.0,
    "max_val": 9.8,
    "caveat": "~18-20% miss checkout; night shifts may show negative/inflated values"
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:19.001609",
    "company_id": 15,
    "filters_applied": {}
  }
}
```

> **Note:** Always display the `caveat` string alongside these numbers. Night-shift employees crossing midnight can produce anomalous durations.

---

### 20. GET /attendance/face-match-rate

**Purpose:** Returns the overall face-recognition match rate across all attendance check-ins for the current month.

**Used in:** Attendance Tab — Face Match Rate KPI card

**Query Parameters:**

| Parameter    | Type    | Default | Description        |
|--------------|---------|---------|--------------------|
| `company_id` | integer | `15`    | Tenant identifier. |

**Response Schema:**

```typescript
interface FaceMatchRateData {
  total: number;    // Total check-in attempts processed
  matched: number;  // Successfully face-matched
  rate: number;     // matched / total * 100
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "total": 547045,
    "matched": 539046,
    "rate": 98.54
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:19.516417",
    "company_id": 15,
    "filters_applied": {}
  }
}
```

---

### 21. GET /attendance/monthly-trend

**Purpose:** Returns average daily attendance (present count and percentage) for each of the last N months, used to visualise attendance trends over time.

**Used in:** Attendance Tab — Monthly Attendance Trend chart

**Query Parameters:**

| Parameter    | Type    | Default | Description                                |
|--------------|---------|---------|---------------------------------------------|
| `company_id` | integer | `15`    | Tenant identifier.                          |
| `months`     | integer | `3`     | Number of previous months to include.       |

**Response Schema:**

```typescript
interface MonthlyAttendanceTrendData {
  months: Array<{
    month: string;       // Abbreviated month name, e.g. "Dec", "Jan" — use as axis label
    avg_present: number; // Average daily present headcount
    avg_late: number;    // Average daily late headcount
    pct: number;         // Average attendance percentage
  }>;
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "months": [
      { "month": "Dec", "avg_present": 1343.0, "avg_late": 976.0, "pct": 72.32 },
      { "month": "Jan", "avg_present": 1310.0, "avg_late": 994.0, "pct": 70.54 },
      { "month": "Feb", "avg_present": 1128.0, "avg_late": 848.0, "pct": 60.74 },
      { "month": "Mar", "avg_present": 1143.0, "avg_late": 873.0, "pct": 61.55 }
    ]
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:20.079725",
    "company_id": 15,
    "filters_applied": { "months": 3 }
  }
}
```

---

### 22. GET /attendance/ghost-detection

**Purpose:** Returns a count of drivers who marked attendance today but have no associated trip records — potential ghost attendance suspects. Filters to DRIVER role only.

**Used in:** Attendance Tab — Ghost Detection alert card

**Query Parameters:**

| Parameter    | Type    | Default | Description                             |
|--------------|---------|---------|------------------------------------------|
| `company_id` | integer | `15`    | Tenant identifier.                       |
| `date`       | string  | today   | Date to query, `YYYY-MM-DD`.             |

**Response Schema:**

```typescript
interface GhostAttendanceData {
  drivers_present: number;     // Drivers who checked in today
  drivers_with_trips: number;  // Drivers who also have at least one trip record
  ghost_suspect: number;       // drivers_present - drivers_with_trips
  note: string;                // Scope note — display near the count
}
```

**Sample Response:**

```json
{
  "success": true,
  "data": {
    "drivers_present": 6,
    "drivers_with_trips": 0,
    "ghost_suspect": 6,
    "note": "Filter by DRIVER role only — non-drivers excluded."
  },
  "meta": {
    "generated_at": "2026-03-18T10:18:20.216758",
    "company_id": 15,
    "filters_applied": { "role": "DRIVER" }
  }
}
```

---

## Notes

### Timestamps

- All `generated_at` and `timestamp` fields are in **UTC**.
- Convert to **IST (UTC +5:30)** for user-facing display.
- Example (JavaScript):
  ```js
  const ist = new Date(generated_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });
  ```

### CORS

- CORS is configured server-side. Contact the backend team if your frontend origin needs to be whitelisted.

### Interactive API Explorer (Swagger UI)

- Available at: `{NEXT_PUBLIC_API_BASE_URL}/docs`
- Use this to inspect full request/response schemas and try live calls.

### Health Check

- `GET {NEXT_PUBLIC_API_BASE_URL}/health`
- Returns `200 OK` when the service is running. Useful for readiness probes.

### MTD Convention

- When no date range is supplied, fuel and breakdown endpoints default to **Month-to-Date** (1st of current month through today).

### `spend_lakhs` vs raw INR

- Several endpoints return both `total_spend` (raw INR) and `spend_lakhs` (divided by 100,000).
- Prefer `spend_lakhs` for chart labels and summary cards to keep numbers human-readable (e.g. "₹59.13L").
