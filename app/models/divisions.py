from __future__ import annotations

from pydantic import BaseModel


class DivisionEntry(BaseModel):
    division_id: int
    division_name: str
    attendance_percentage: float
    fuel_spend_lakhs: float
    route_completion_pct: float
    breakdown_count: int


class DivisionPerformance(BaseModel):
    divisions: list[DivisionEntry]
