from datetime import datetime
from fastapi import APIRouter, Query
from app.database import get_pool
from app.models.common import ApiResponse, Meta
from app.models.divisions import DivisionPerformance, DivisionEntry
from app.queries import divisions as sql

router = APIRouter(tags=["Divisions"])


@router.get("/divisions/performance")
async def get_divisions_performance(
    company_id: int = Query(default=15),
    limit: int = Query(default=10),
):
    pool = get_pool()
    try:
        rows = await pool.fetch(sql.DIVISION_PERFORMANCE, company_id, limit)
        divisions = [
            DivisionEntry(
                division_id=int(row["division_id"]),
                division_name=row["division_name"],
                attendance_percentage=float(row["attendance_percentage"] or 0),
                fuel_spend_lakhs=float(row["fuel_spend_lakhs"] or 0),
                route_completion_pct=float(row["route_completion_pct"] or 0),
                breakdown_count=int(row["breakdown_count"] or 0),
            )
            for row in rows
        ]
        return ApiResponse(
            data=DivisionPerformance(divisions=divisions),
            meta=Meta(
                generated_at=datetime.utcnow(),
                company_id=company_id,
                filters_applied={"limit": limit},
            ),
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            data=None,
            meta=Meta(
                generated_at=datetime.utcnow(),
                company_id=company_id,
                filters_applied={"limit": limit, "error": str(exc)},
            ),
        )
