from datetime import datetime
from fastapi import APIRouter, Query
from app.database import get_pool
from app.models.common import ApiResponse, Meta
from app.models.fleet import RouteCompletionByTier, TierEntry, TierTotal
from app.queries import fleet as sql

router = APIRouter(tags=["Routes"])


@router.get("/routes/completion-by-tier")
async def get_route_completion_by_tier(company_id: int = Query(default=15)):
    pool = get_pool()
    try:
        rows = await pool.fetch(sql.ROUTE_COMPLETION_BY_TIER, company_id)
        tiers = [
            TierEntry(
                tier=row["tier"],
                scheduled_trips=int(row["scheduled_trips"] or 0),
                actual_trips=int(row["actual_trips"] or 0),
                scheduled_km=float(row["scheduled_km"] or 0),
                actual_km=float(row["actual_km"] or 0),
                completion_pct=round(
                    int(row["actual_trips"] or 0) / int(row["scheduled_trips"]) * 100, 2
                )
                if int(row["scheduled_trips"] or 0) > 0
                else 0.0,
            )
            for row in rows
        ]
        total_scheduled = sum(t.scheduled_trips for t in tiers)
        total_actual = sum(t.actual_trips for t in tiers)
        total = TierTotal(
            scheduled_trips=total_scheduled,
            actual_trips=total_actual,
            completion_pct=round(total_actual / total_scheduled * 100, 2)
            if total_scheduled > 0
            else 0.0,
        )
        return ApiResponse(
            data=RouteCompletionByTier(tiers=tiers, total=total),
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
