from __future__ import annotations

from pydantic import BaseModel
from datetime import date


class FuelDayEntry(BaseModel):
    date: date
    display_label: str
    total_spend: float
    total_liters: float
    fill_count: int


class FuelDailyTrend(BaseModel):
    days: list[FuelDayEntry]


class FuelMonthEntry(BaseModel):
    month: str
    display_label: str
    total_spend: float
    total_liters: float
    avg_price_per_liter: float


class FuelMonthlyTrend(BaseModel):
    months: list[FuelMonthEntry]


class PaymentModeEntry(BaseModel):
    payment_mode: str
    transaction_count: int
    total_amount: float
    total_liters: float
    percentage: float


class PaymentModeSplit(BaseModel):
    modes: list[PaymentModeEntry]


class TopFuelVehicle(BaseModel):
    bus_id: int
    registration_number: str
    total_liters: float
    total_amount: float
    fill_count: int
    km_per_liter: float | None


class TopFuelConsumers(BaseModel):
    vehicles: list[TopFuelVehicle]


class DivisionFuelEntry(BaseModel):
    division_id: int
    division_name: str
    total_spend: float
    total_liters: float
    spend_lakhs: float
    fill_count: int


class DivisionFuelSpend(BaseModel):
    divisions: list[DivisionFuelEntry]
