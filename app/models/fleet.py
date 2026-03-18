from __future__ import annotations

from pydantic import BaseModel
from datetime import date


class TierEntry(BaseModel):
    tier: str
    scheduled_trips: int
    actual_trips: int
    scheduled_km: float
    actual_km: float
    completion_pct: float


class TierTotal(BaseModel):
    scheduled_trips: int
    actual_trips: int
    completion_pct: float


class RouteCompletionByTier(BaseModel):
    tiers: list[TierEntry]
    total: TierTotal


class BreakdownReasonEntry(BaseModel):
    reason_id: int
    reason_text: str
    count: int
    percentage: float


class BreakdownReasons(BaseModel):
    reasons: list[BreakdownReasonEntry]
    total: int


class RepeatBreakdownVehicle(BaseModel):
    bus_id: int
    registration_number: str
    breakdown_count: int
    last_breakdown_date: date
    last_reason: str


class RepeatBreakdownVehicles(BaseModel):
    vehicles: list[RepeatBreakdownVehicle]
