from datetime import datetime
from fastapi import APIRouter, Query
from app.database import get_pool
from app.models.common import ApiResponse, Meta
from app.models.fuel import (
    FuelDailyTrend,
    FuelDayEntry,
    FuelMonthlyTrend,
    FuelMonthEntry,
    PaymentModeSplit,
    PaymentModeEntry,
    TopFuelConsumers,
    TopFuelVehicle,
    DivisionFuelSpend,
    DivisionFuelEntry,
)
from app.queries import fuel as sql

router = APIRouter(tags=["Fuel"])


@router.get("/fuel/trend-daily")
async def get_fuel_trend_daily(
    company_id: int = Query(default=15),
    days: int = Query(default=15),
):
    pool = get_pool()
    try:
        rows = await pool.fetch(sql.FUEL_TREND_DAILY, company_id, str(days))
        entries = [
            FuelDayEntry(
                date=str(row["date"]),
                display_label=row["display_label"],
                total_spend=float(row["total_spend"] or 0),
                total_liters=float(row["total_liters"] or 0),
                fill_count=int(row["fill_count"] or 0),
            )
            for row in rows
        ]
        return ApiResponse(
            data=FuelDailyTrend(days=entries),
            meta=Meta(
                generated_at=datetime.utcnow(),
                company_id=company_id,
                filters_applied={"days": days},
            ),
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            data=None,
            meta=Meta(
                generated_at=datetime.utcnow(),
                company_id=company_id,
                filters_applied={"days": days, "error": str(exc)},
            ),
        )


@router.get("/fuel/trend-monthly")
async def get_fuel_trend_monthly(
    company_id: int = Query(default=15),
    months: int = Query(default=6),
):
    pool = get_pool()
    try:
        rows = await pool.fetch(sql.FUEL_TREND_MONTHLY, company_id, str(months))
        entries = [
            FuelMonthEntry(
                month=row["month"],
                display_label=row["display_label"],
                total_spend=float(row["total_spend"] or 0),
                total_liters=float(row["total_liters"] or 0),
                avg_price_per_liter=float(row["avg_price_per_liter"] or 0),
            )
            for row in rows
        ]
        return ApiResponse(
            data=FuelMonthlyTrend(months=entries),
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


@router.get("/fuel/payment-modes")
async def get_fuel_payment_modes(company_id: int = Query(default=15)):
    pool = get_pool()
    try:
        rows = await pool.fetch(sql.FUEL_PAYMENT_MODES, company_id)
        total_amount = sum(float(r["total_amount"] or 0) for r in rows)
        entries = [
            PaymentModeEntry(
                payment_mode=row["payment_mode"],
                transaction_count=int(row["transaction_count"] or 0),
                total_amount=float(row["total_amount"] or 0),
                total_liters=float(row["total_liters"] or 0),
                percentage=round(
                    float(row["total_amount"] or 0) / total_amount * 100, 2
                )
                if total_amount > 0
                else 0.0,
            )
            for row in rows
        ]
        return ApiResponse(
            data=PaymentModeSplit(modes=entries),
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


@router.get("/fuel/top-consumers")
async def get_fuel_top_consumers(
    company_id: int = Query(default=15),
    limit: int = Query(default=10),
):
    pool = get_pool()
    try:
        rows = await pool.fetch(sql.FUEL_TOP_CONSUMERS, company_id, limit)
        vehicles = [
            TopFuelVehicle(
                bus_id=int(row["bus_id"]),
                registration_number=row["registration_number"],
                total_liters=float(row["total_liters"] or 0),
                total_amount=float(row["total_amount"] or 0),
                fill_count=int(row["fill_count"] or 0),
                km_per_liter=float(row["km_per_liter"]) if row["km_per_liter"] is not None else None,
            )
            for row in rows
        ]
        return ApiResponse(
            data=TopFuelConsumers(vehicles=vehicles),
            meta=Meta(
                generated_at=datetime.utcnow(),
                company_id=company_id,
                filters_applied={"limit": limit},
            ),
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            data=None,
            meta=Meta(
                generated_at=datetime.utcnow(),
                company_id=company_id,
                filters_applied={"limit": limit, "error": str(exc)},
            ),
        )


@router.get("/fuel/division-spend")
async def get_fuel_division_spend(company_id: int = Query(default=15)):
    pool = get_pool()
    try:
        rows = await pool.fetch(sql.FUEL_DIVISION_SPEND, company_id)
        divisions = [
            DivisionFuelEntry(
                division_id=int(row["division_id"]),
                division_name=row["division_name"],
                total_spend=float(row["total_spend"] or 0),
                total_liters=float(row["total_liters"] or 0),
                spend_lakhs=round(float(row["total_spend"] or 0) / 100000, 2),
                fill_count=int(row["fill_count"] or 0),
            )
            for row in rows
        ]
        return ApiResponse(
            data=DivisionFuelSpend(divisions=divisions),
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
