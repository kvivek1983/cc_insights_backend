from datetime import datetime
from fastapi import APIRouter, Query
from app.database import get_pool
from app.models.common import ApiResponse, Meta
from app.models.fleet import (
    BreakdownReasons,
    BreakdownReasonEntry,
    RepeatBreakdownVehicles,
    RepeatBreakdownVehicle,
)
from app.queries import fleet as sql

router = APIRouter(tags=["Breakdowns"])


@router.get("/breakdowns/reasons")
async def get_breakdown_reasons(company_id: int = Query(default=15)):
    pool = get_pool()
    try:
        rows = await pool.fetch(sql.BREAKDOWN_REASONS, company_id)
        total = sum(int(r["count"] or 0) for r in rows)
        reasons = [
            BreakdownReasonEntry(
                reason_id=int(row["reason_id"]),
                reason_text=row["reason_text"],
                count=int(row["count"] or 0),
                percentage=round(int(row["count"] or 0) / total * 100, 2)
                if total > 0
                else 0.0,
            )
            for row in rows
        ]
        return ApiResponse(
            data=BreakdownReasons(reasons=reasons, total=total),
            meta=Meta(
                generated_at=datetime.utcnow(),
                company_id=company_id,
                filters_applied={},
            ),
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            data=None,
            meta=Meta(
                generated_at=datetime.utcnow(),
                company_id=company_id,
                filters_applied={"error": str(exc)},
            ),
        )


@router.get("/breakdowns/repeat-vehicles")
async def get_breakdown_repeat_vehicles(
    company_id: int = Query(default=15),
    limit: int = Query(default=10),
):
    pool = get_pool()
    try:
        rows = await pool.fetch(sql.REPEAT_BREAKDOWN_VEHICLES, company_id, limit)
        vehicles = [
            RepeatBreakdownVehicle(
                bus_id=int(row["bus_id"]),
                registration_number=row["registration_number"],
                breakdown_count=int(row["breakdown_count"] or 0),
                last_breakdown_date=row["last_breakdown_date"],
                last_reason=row["last_reason"],
            )
            for row in rows
        ]
        return ApiResponse(
            data=RepeatBreakdownVehicles(vehicles=vehicles),
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
