import asyncio
from datetime import datetime
from fastapi import APIRouter, Query
from app.database import get_pool
from app.models.common import ApiResponse, Meta
from app.models.summary import (
    TodaySummary,
    FuelSummary,
    AttendanceSummary,
    FleetSummary,
    RoutesSummary,
    BreakdownsSummary,
)
from app.queries import summary as sql

router = APIRouter(tags=["Summary"])


@router.get("/summary/today")
async def get_today_summary(company_id: int = Query(default=15)):
    pool = get_pool()
    try:
        (
            fuel_row,
            mtd_row,
            att_row,
            emp_row,
            miss_row,
            routes_row,
            active_row,
            total_veh_row,
            idle_row,
            bd_row,
            kml_row,
        ) = await asyncio.gather(
            pool.fetchrow(sql.FUEL_TODAY_YESTERDAY, company_id),
            pool.fetchrow(sql.FUEL_MTD, company_id),
            pool.fetchrow(sql.ATTENDANCE_TODAY, company_id),
            pool.fetchrow(sql.TOTAL_EMPLOYEES, company_id),
            pool.fetchrow(sql.MISSING_CHECKOUT, company_id),
            pool.fetchrow(sql.ROUTES_TODAY, company_id),
            pool.fetchrow(sql.ACTIVE_VEHICLES, company_id),
            pool.fetchrow(sql.TOTAL_VEHICLES, company_id),
            pool.fetchrow(sql.IDLE_VEHICLES, company_id),
            pool.fetchrow(sql.BREAKDOWNS_TODAY, company_id),
            pool.fetchrow(sql.AVG_KM_PER_LITER, company_id),
        )

        data = TodaySummary(
            fuel=FuelSummary(
                today_spend=float(fuel_row["today_spend"] or 0),
                yesterday_spend=float(fuel_row["yesterday_spend"] or 0),
                today_liters=float(fuel_row["today_liters"] or 0),
                yesterday_liters=float(fuel_row["yesterday_liters"] or 0),
                mtd_spend=float(mtd_row["mtd_spend"] or 0),
                last_month_spend=float(mtd_row["last_month_spend"] or 0),
                avg_km_per_liter_mtd=float(kml_row["mtd_km_per_liter"] or 0),
                avg_km_per_liter_last_month=float(kml_row["last_month_km_per_liter"] or 0),
                mtd_km_covered=float(kml_row["mtd_km_covered"] or 0),
            ),
            attendance=AttendanceSummary(
                present_today=int(att_row["present_today"] or 0),
                total_employees=int(emp_row["total_employees"] or 0),
                late_arrivals=int(att_row["late_arrivals"] or 0),
                geo_violations=int(att_row["geo_violations"] or 0),
                missing_checkout=int(miss_row["missing_checkout"] or 0),
            ),
            fleet=FleetSummary(
                active_vehicles_today=int(active_row["active_vehicles_today"] or 0),
                total_vehicles=int(total_veh_row["total_vehicles"] or 0),
                idle_vehicles_7d=int(idle_row["idle_vehicles"] or 0),
            ),
            routes=RoutesSummary(
                completed_today=int(routes_row["completed_today"] or 0),
                total_today=int(routes_row["total_today"] or 0),
            ),
            breakdowns=BreakdownsSummary(
                count_today=int(bd_row["breakdowns_today"] or 0),
            ),
        )
        return ApiResponse(
            data=data,
            meta=Meta(
                generated_at=datetime.utcnow(),
                company_id=company_id,
                filters_applied={"date": "today"},
            ),
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            data=None,
            meta=Meta(
                generated_at=datetime.utcnow(),
                company_id=company_id,
                filters_applied={"date": "today", "error": str(exc)},
            ),
        )
