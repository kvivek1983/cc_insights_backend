import asyncio
from datetime import datetime
from fastapi import APIRouter, Query
from app.database import get_pool
from app.models.common import ApiResponse, Meta
from app.models.alerts import DashboardAlerts, AlertEntry
from app.queries import alerts as sql

router = APIRouter(tags=["Alerts"])

_TYPE_ORDER = {"critical": 0, "warning": 1, "info": 2}


@router.get("/alerts")
async def get_alerts(
    company_id: int = Query(default=15),
    limit: int = Query(default=10),
):
    pool = get_pool()
    try:
        bd_rows, fuel_rows, odo_rows, idle_rows = await asyncio.gather(
            pool.fetch(sql.REPEAT_BREAKDOWN_ALERTS, company_id),
            pool.fetch(sql.FUEL_WITHOUT_ATTENDANCE_ALERTS, company_id),
            pool.fetch(sql.ODOMETER_ANOMALY_ALERTS, company_id),
            pool.fetch(sql.IDLE_VEHICLE_ALERTS, company_id),
        )

        all_rows = list(bd_rows) + list(fuel_rows) + list(odo_rows) + list(idle_rows)
        all_rows.sort(key=lambda r: _TYPE_ORDER.get(r["type"], 99))
        all_rows = all_rows[:limit]

        alerts = [
            AlertEntry(
                id=f"alert-{row['category']}-{i}",
                type=row["type"],
                category=row["category"],
                message=row["message"],
                detail=row["detail"],
                timestamp=str(row["timestamp"]),
                entity_id=int(row["entity_id"]) if row["entity_id"] else None,
            )
            for i, row in enumerate(all_rows)
        ]

        return ApiResponse(
            data=DashboardAlerts(alerts=alerts),
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
