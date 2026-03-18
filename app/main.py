from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_pool, close_pool
from app.routers import summary, fuel, attendance, routes, breakdowns, divisions, alerts, data_quality


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_pool()
    yield
    await close_pool()


app = FastAPI(
    title="OneCheck Dashboard API",
    description="Backend API for the OneCheck Sr. Management Dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

PREFIX = "/api/v1/dashboard"

app.include_router(summary.router, prefix=PREFIX)
app.include_router(fuel.router, prefix=PREFIX)
app.include_router(attendance.router, prefix=PREFIX)
app.include_router(routes.router, prefix=PREFIX)
app.include_router(breakdowns.router, prefix=PREFIX)
app.include_router(divisions.router, prefix=PREFIX)
app.include_router(alerts.router, prefix=PREFIX)
app.include_router(data_quality.router, prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok"}
