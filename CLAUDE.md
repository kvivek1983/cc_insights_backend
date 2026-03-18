# OneCheck Dashboard Backend

## Quick Reference
- **Stack**: Python 3.11+ / FastAPI / asyncpg / Pydantic v2
- **Database**: PostgreSQL 16.13, schema `cleancheck`, company_id=15 (OSRTC)
- **DB Connection**: SSH tunnel to `localhost:15432` (read-only user)
- **Run**: `uvicorn app.main:app --reload`
- **API Docs**: http://localhost:8000/docs
- **Endpoints**: 22 endpoints under `/api/v1/dashboard`

## Critical Rules
- `is_deleted = false` (PostgreSQL boolean, NOT 0/1)
- `attendance_type = 1` = Check-In, `2` = Check-Out (changed post-migration Aug 2025)
- Always exclude `fuel_expense_id != 12` (test entry worth ~250M)
- Fuel quality filters: `total_amount < 1000000`, `volume_in_liter BETWEEN 1 AND 500`, `fuel_price BETWEEN 50 AND 150`
- Timestamps are UTC — frontend converts to IST (+5:30)
- `company_id = 15` for OSRTC

## Pre-Deploy Checklist
- [ ] SSH tunnel active (`localhost:15432`)
- [ ] `.env` file populated with DB credentials
- [ ] All 22 endpoints return valid JSON on `/docs`
- [ ] No SQL injection risks (all queries use asyncpg parameterized $1, $2)

## Backlog
- Live API deployment (currently local only)
- Authentication (Phase 2)
- Rate limiting
- Response caching for heavy queries
