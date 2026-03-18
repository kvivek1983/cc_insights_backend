import asyncio
from datetime import datetime
from fastapi import APIRouter, Query
from app.database import get_pool
from app.models.common import ApiResponse, Meta
from app.models.attendance import (
    AttendanceDailyStats,
    WeeklyAttendancePattern,
    WeeklyDay,
    AttendanceStatusBreakdown,
    StatusEntry,
    AttendanceDivisionDetail,
    DivisionAttendanceEntry,
    PeakHourDistribution,
    HourEntry,
    WeekdayPattern,
    WeekdayEntry,
    WorkHoursStats,
    FaceMatchRate,
    MonthlyAttendanceTrend,
    MonthlyAttendanceEntry,
    GhostAttendance,
)
from app.queries import attendance as sql

router = APIRouter(tags=["Attendance"])

STATUS_MAP = {
    1: ("Present (On-time)", "#10B981"),
    4: ("Present + No Location", "#8B5CF6"),
    5: ("Late", "#F59E0B"),
    7: ("Late + No Location", "#EF4444"),
}


def _fmt_hour(h: int) -> str:
    if h == 0:
        return "12 AM"
    if h < 12:
        return f"{h} AM"
    if h == 12:
        return "12 PM"
    return f"{h - 12} PM"


@router.get("/attendance/daily-stats")
async def get_attendance_daily_stats(company_id: int = Query(default=15)):
    pool = get_pool()
    try:
        row = await pool.fetchrow(sql.ATTENDANCE_DAILY_STATS, company_id)
        data = AttendanceDailyStats(
            date=str(datetime.utcnow().date()),
            total_employees=0,
            present=int(row["present"] or 0),
            present_no_location=int(row["present_no_location"] or 0),
            late=int(row["late"] or 0),
            late_no_location=int(row["late_no_location"] or 0),
            total_check_ins=int(row["total_check_ins"] or 0),
            total_check_outs=int(row["total_check_outs"] or 0),
            missing_checkout=0,
            fuel_without_attendance=0,
        )
        return ApiResponse(
            data=data,
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


@router.get("/attendance/weekly-pattern")
async def get_attendance_weekly_pattern(company_id: int = Query(default=15)):
    pool = get_pool()
    try:
        rows = await pool.fetch(sql.ATTENDANCE_WEEKLY_PATTERN, company_id)
        days = [
            WeeklyDay(
                day_of_week=row["day_of_week"],
                present=int(row["present"] or 0),
                late=int(row["late"] or 0),
                geo_violation=int(row["geo_violation"] or 0),
            )
            for row in rows
        ]
        return ApiResponse(
            data=WeeklyAttendancePattern(days=days),
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


@router.get("/attendance/status-breakdown")
async def get_attendance_status_breakdown(company_id: int = Query(default=15)):
    pool = get_pool()
    try:
        rows = await pool.fetch(sql.ATTENDANCE_STATUS_BREAKDOWN, company_id)
        statuses = []
        for row in rows:
            code = int(row["approval_status"])
            name, color = STATUS_MAP.get(code, (f"Status {code}", "#6B7280"))
            statuses.append(
                StatusEntry(
                    name=name,
                    value=int(row["count"] or 0),
                    color=color,
                )
            )
        return ApiResponse(
            data=AttendanceStatusBreakdown(statuses=statuses),
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


@router.get("/attendance/division-detail")
async def get_attendance_division_detail(company_id: int = Query(default=15)):
    pool = get_pool()
    try:
        rows = await pool.fetch(sql.ATTENDANCE_DIVISION_DETAIL, company_id)
        divisions = [
            DivisionAttendanceEntry(
                division_id=int(row["division_id"]),
                division_name=row["division_name"],
                present=int(row["present"] or 0),
                total=int(row["total"] or 0),
                pct=round(
                    int(row["present"] or 0) / int(row["total"]) * 100, 2
                )
                if int(row["total"] or 0) > 0
                else 0.0,
                late=int(row["late"] or 0),
                geo_violations=int(row["geo_violations"] or 0),
            )
            for row in rows
        ]
        return ApiResponse(
            data=AttendanceDivisionDetail(divisions=divisions),
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


@router.get("/attendance/peak-hours")
async def get_attendance_peak_hours(company_id: int = Query(default=15)):
    pool = get_pool()
    try:
        rows = await pool.fetch(sql.ATTENDANCE_PEAK_HOURS, company_id)
        hours = [
            HourEntry(
                hour=_fmt_hour(int(row["hour_ist"])),
                checkins=int(row["checkins"] or 0),
            )
            for row in rows
        ]
        return ApiResponse(
            data=PeakHourDistribution(hours=hours),
            meta=Meta(
                generated_at=datetime.utcnow(),
                company_id=company_id,
                filters_applied={"hour_format": "e.g. 5 AM, 6 AM"},
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


@router.get("/attendance/weekday-pattern")
async def get_attendance_weekday_pattern(
    company_id: int = Query(default=15),
    weeks: int = Query(default=4),
):
    pool = get_pool()
    try:
        rows, emp_row = await asyncio.gather(
            pool.fetch(sql.ATTENDANCE_WEEKDAY_PATTERN, company_id, str(weeks)),
            pool.fetchrow(sql.TOTAL_EMPLOYEES_COUNT, company_id),
        )
        total_employees = int(emp_row["total_employees"] or 1)
        days = [
            WeekdayEntry(
                day=row["day"],
                present=int(row["present"] or 0),
                pct=round(int(row["present"] or 0) / total_employees * 100, 2),
            )
            for row in rows
        ]
        return ApiResponse(
            data=WeekdayPattern(days=days),
            meta=Meta(
                generated_at=datetime.utcnow(),
                company_id=company_id,
                filters_applied={"weeks": weeks},
            ),
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            data=None,
            meta=Meta(
                generated_at=datetime.utcnow(),
                company_id=company_id,
                filters_applied={"weeks": weeks, "error": str(exc)},
            ),
        )


@router.get("/attendance/work-hours")
async def get_attendance_work_hours(company_id: int = Query(default=15)):
    pool = get_pool()
    try:
        row = await pool.fetchrow(sql.ATTENDANCE_WORK_HOURS, company_id)
        data = WorkHoursStats(
            avg=float(row["avg"] or 0),
            median=float(row["median"] or 0),
            min_val=float(row["min_val"] or 0),
            max_val=float(row["max_val"] or 0),
            caveat="~18-20% miss checkout; night shifts may show negative/inflated values",
        )
        return ApiResponse(
            data=data,
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


@router.get("/attendance/face-match-rate")
async def get_attendance_face_match_rate(company_id: int = Query(default=15)):
    pool = get_pool()
    try:
        row = await pool.fetchrow(sql.ATTENDANCE_FACE_MATCH_RATE, company_id)
        total = int(row["total"] or 0)
        matched = int(row["matched"] or 0)
        data = FaceMatchRate(
            total=total,
            matched=matched,
            rate=round(matched / total * 100, 2) if total > 0 else 0.0,
        )
        return ApiResponse(
            data=data,
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


@router.get("/attendance/monthly-trend")
async def get_attendance_monthly_trend(
    company_id: int = Query(default=15),
    months: int = Query(default=6),
):
    pool = get_pool()
    try:
        rows, emp_row = await asyncio.gather(
            pool.fetch(sql.ATTENDANCE_MONTHLY_TREND, company_id, str(months)),
            pool.fetchrow(sql.TOTAL_EMPLOYEES_COUNT, company_id),
        )
        total_employees = int(emp_row["total_employees"] or 1)
        entries = [
            MonthlyAttendanceEntry(
                month=row["month"],
                avg_present=float(row["avg_present"] or 0),
                avg_late=float(row["avg_late"] or 0),
                pct=round(float(row["avg_present"] or 0) / total_employees * 100, 2),
            )
            for row in rows
        ]
        return ApiResponse(
            data=MonthlyAttendanceTrend(months=entries),
            meta=Meta(
                generated_at=datetime.utcnow(),
                company_id=company_id,
                filters_applied={"months": months},
            ),
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            data=None,
            meta=Meta(
                generated_at=datetime.utcnow(),
                company_id=company_id,
                filters_applied={"months": months, "error": str(exc)},
            ),
        )


@router.get("/attendance/ghost-detection")
async def get_attendance_ghost_detection(company_id: int = Query(default=15)):
    pool = get_pool()
    try:
        row = await pool.fetchrow(sql.ATTENDANCE_GHOST_DETECTION, company_id)
        drivers_present = int(row["drivers_present"] or 0)
        drivers_with_trips = int(row["drivers_with_trips"] or 0)
        ghost_suspect = max(0, drivers_present - drivers_with_trips)
        data = GhostAttendance(
            drivers_present=drivers_present,
            drivers_with_trips=drivers_with_trips,
            ghost_suspect=ghost_suspect,
            note="Filter by DRIVER role only — non-drivers excluded.",
        )
        return ApiResponse(
            data=data,
            meta=Meta(
                generated_at=datetime.utcnow(),
                company_id=company_id,
                filters_applied={"role": "DRIVER"},
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
