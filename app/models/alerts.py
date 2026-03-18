from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime


class AlertEntry(BaseModel):
    id: str
    type: str
    category: str
    message: str
    detail: str
    timestamp: datetime
    entity_id: int | None = None


class DashboardAlerts(BaseModel):
    alerts: list[AlertEntry]


class DataQualityMetric(BaseModel):
    key: str
    label: str
    value_pct: float
    count: int
    note: str
    severity: str


class DataQualitySnapshot(BaseModel):
    metrics: list[DataQualityMetric]
