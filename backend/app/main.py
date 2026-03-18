from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

from app.config import settings
from app.seed_data import seed
from app.routers import companies, articles, dashboard, batch
from app.services import batch as batch_service

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    seed()

    # Schedule periodic batch
    scheduler.add_job(
        batch_service.run_full_batch,
        "interval",
        hours=settings.batch_interval_hours,
        id="full_batch",
        replace_existing=True,
    )
    scheduler.start()

    yield

    # Shutdown
    scheduler.shutdown()


app = FastAPI(
    title="Risk Sensing Admin API",
    description="외부정보 센싱 어드민 - 가맹기업 리스크 모니터링",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router)
app.include_router(articles.router)
app.include_router(dashboard.router)
app.include_router(batch.router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
