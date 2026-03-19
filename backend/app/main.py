from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
from pathlib import Path

from app.config import settings
from app.seed_data import seed
from app.routers import companies, articles, dashboard, batch
from app.services import batch as batch_service

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed()
    scheduler.add_job(
        batch_service.run_full_batch,
        "interval",
        hours=settings.batch_interval_hours,
        id="full_batch",
        replace_existing=True,
    )
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Risk Sensing Admin API",
    description="외부정보 센싱 어드민 - 가맹기업 리스크 모니터링",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router, prefix="/api")
app.include_router(articles.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(batch.router, prefix="/api")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "static_exists": static_path.exists(),
        "index_exists": (static_path / "index.html").exists(),
        "static_path": str(static_path),
    }


# 프론트엔드 정적 파일 서빙 (빌드된 경우)
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")
