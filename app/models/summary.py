from __future__ import annotations

from pydantic import BaseModel


class FuelSummary(BaseModel):
    today_spend: float
    yesterday_spend: float
    today_liters: float
    yesterday_liters: float
    mtd_spend: float
    last_month_spend: float
    avg_km_per_liter_mtd: float
    avg_km_per_liter_last_month: float
    mtd_km_covered: float


class AttendanceSummary(BaseModel):
    present_today: int
    total_employees: int
    late_arrivals: int
    geo_violations: int
    missing_checkout: int


class FleetSummary(BaseModel):
    active_vehicles_today: int
    total_vehicles: int
    idle_vehicles_7d: int


class RoutesSummary(BaseModel):
    completed_today: int
    total_today: int


class BreakdownsSummary(BaseModel):
    count_today: int


class TodaySummary(BaseModel):
    fuel: FuelSummary
    attendance: AttendanceSummary
    fleet: FleetSummary
    routes: RoutesSummary
    breakdowns: BreakdownsSummary
