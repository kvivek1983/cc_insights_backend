import asyncio
from datetime import datetime
from fastapi import APIRouter, Query
from app.database import get_pool
from app.models.common import ApiResponse, Meta
from app.models.alerts import DataQualitySnapshot, DataQualityMetric
from app.queries import data_quality as sql

router = APIRouter(tags=["Data Quality"])


def _severity(pct: float) -> str:
    if pct > 15:
        return "red"
    if pct > 5:
        return "amber"
    return "green"


@router.get("/data-quality/snapshot")
async def get_data_quality_snapshot(company_id: int = Query(default=15)):
    pool = get_pool()
    try:
        selfie_row, odo_row, dup_row, fwa_row = await asyncio.gather(
            pool.fetchrow(sql.MISSING_SELFIE, company_id),
            pool.fetchrow(sql.ODOMETER_ANOMALIES, company_id),
            pool.fetchrow(sql.DUPLICATE_FUEL, company_id),
            pool.fetchrow(sql.FUEL_WITHOUT_ATTENDANCE, company_id),
        )

        metrics = []

        selfie_missing = int(selfie_row["missing"] or 0)
        selfie_total = int(selfie_row["total"] or 1)
        selfie_pct = round(selfie_missing / selfie_total * 100, 1) if selfie_total > 0 else 0
        metrics.append(DataQualityMetric(
            key="missing_selfie", label="Missing Driver Selfie",
            value_pct=selfie_pct, count=selfie_missing,
            note=f"{selfie_missing:,} of {selfie_total:,} records",
            severity=_severity(selfie_pct),
        ))

        odo_count = int(odo_row["anomalies"] or 0)
        odo_total = int(odo_row["total"] or 1)
        odo_pct = round(odo_count / odo_total * 100, 1) if odo_total > 0 else 0
        metrics.append(DataQualityMetric(
            key="odometer_anomalies", label="Odometer Anomalies",
            value_pct=odo_pct, count=odo_count,
            note=f"{odo_count:,} anomalies",
            severity=_severity(odo_pct),
        ))

        dup_count = int(dup_row["duplicate_groups"] or 0)
        metrics.append(DataQualityMetric(
            key="duplicate_fuel", label="Duplicate Fuel Entries",
            value_pct=0, count=dup_count,
            note=f"{dup_count} duplicate groups",
            severity="green" if dup_count < 10 else "amber",
        ))

        fwa_count = int(fwa_row["count"] or 0)
        metrics.append(DataQualityMetric(
            key="fuel_without_attendance", label="Fuel Without Attendance",
            value_pct=0, count=fwa_count,
            note=f"{fwa_count} entries (MTD)",
            severity="red" if fwa_count > 50 else "amber" if fwa_count > 10 else "green",
        ))

        return ApiResponse(
            data=DataQualitySnapshot(metrics=metrics),
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
