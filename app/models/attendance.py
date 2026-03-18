from __future__ import annotations

from pydantic import BaseModel
from datetime import date


class AttendanceDailyStats(BaseModel):
    date: date
    total_employees: int
    present: int
    present_no_location: int
    late: int
    late_no_location: int
    total_check_ins: int
    total_check_outs: int
    missing_checkout: int
    fuel_without_attendance: int


class WeeklyDay(BaseModel):
    day_of_week: str
    present: int
    late: int
    geo_violation: int


class WeeklyAttendancePattern(BaseModel):
    days: list[WeeklyDay]


class StatusEntry(BaseModel):
    name: str
    value: int
    color: str


class AttendanceStatusBreakdown(BaseModel):
    statuses: list[StatusEntry]


class DivisionAttendanceEntry(BaseModel):
    division_id: int
    division_name: str
    present: int
    total: int
    pct: float
    late: int
    geo_violations: int


class AttendanceDivisionDetail(BaseModel):
    divisions: list[DivisionAttendanceEntry]


class HourEntry(BaseModel):
    hour: str
    checkins: int


class PeakHourDistribution(BaseModel):
    hours: list[HourEntry]


class WeekdayEntry(BaseModel):
    day: str
    present: int
    pct: float


class WeekdayPattern(BaseModel):
    days: list[WeekdayEntry]


class WorkHoursStats(BaseModel):
    avg: float
    median: float
    min_val: float
    max_val: float
    caveat: str


class FaceMatchRate(BaseModel):
    total: int
    matched: int
    rate: float


class MonthlyAttendanceEntry(BaseModel):
    month: str
    avg_present: float
    avg_late: float
    pct: float


class MonthlyAttendanceTrend(BaseModel):
    months: list[MonthlyAttendanceEntry]


class GhostAttendance(BaseModel):
    drivers_present: int
    drivers_with_trips: int
    ghost_suspect: int
    note: str
