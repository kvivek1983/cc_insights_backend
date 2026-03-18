from __future__ import annotations

from pydantic import BaseModel
from typing import Generic, TypeVar, Any
from datetime import datetime

T = TypeVar("T")


class Meta(BaseModel):
    generated_at: datetime
    company_id: int
    filters_applied: dict[str, Any] = {}


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    meta: Meta
