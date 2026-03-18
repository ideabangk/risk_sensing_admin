import json
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from typing import Optional
from app.database import get_db, _DBConn
from app.services import batch as batch_service

router = APIRouter(prefix="/batch", tags=["batch"])


@router.post("/run/all")
async def run_all_companies(
    background_tasks: BackgroundTasks,
    sources: Optional[str] = None,
):
    source_list = [s.strip().upper() for s in sources.split(",")] if sources else None
    background_tasks.add_task(batch_service.run_full_batch, source_list)
    return {"status": "started", "message": "Batch job started in background"}


@router.post("/run/{company_id}")
async def run_single_company(
    company_id: int,
    background_tasks: BackgroundTasks,
    sources: Optional[str] = None,
    db: _DBConn = Depends(get_db),
):
    row = db.execute(
        "SELECT name, search_keywords FROM companies WHERE id = %s", [company_id]
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")

    name = row[0]
    keywords = json.loads(row[1]) if isinstance(row[1], str) else (row[1] or None)
    source_list = [s.strip().upper() for s in sources.split(",")] if sources else None

    background_tasks.add_task(
        batch_service.run_batch_for_company,
        company_id, name, keywords, source_list,
    )
    return {"status": "started", "company": name}


@router.post("/run/{company_id}/sync")
async def run_single_company_sync(
    company_id: int,
    sources: Optional[str] = None,
    db: _DBConn = Depends(get_db),
):
    row = db.execute(
        "SELECT name, search_keywords FROM companies WHERE id = %s", [company_id]
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")

    name = row[0]
    keywords = json.loads(row[1]) if isinstance(row[1], str) else (row[1] or None)
    source_list = [s.strip().upper() for s in sources.split(",")] if sources else None

    result = await batch_service.run_batch_for_company(
        company_id, name, keywords, source_list
    )
    return result


@router.get("/logs")
def get_logs(
    company_id: Optional[int] = None,
    limit: int = 50,
    db: _DBConn = Depends(get_db),
):
    q = """
        SELECT bl.id, bl.company_id, c.name, bl.source_type,
               bl.started_at, bl.completed_at, bl.status,
               bl.articles_collected, bl.error_message
        FROM batch_logs bl
        LEFT JOIN companies c ON c.id = bl.company_id
    """
    params = []
    if company_id is not None:
        q += " WHERE bl.company_id = %s"
        params.append(company_id)

    q += " ORDER BY bl.started_at DESC LIMIT %s"
    params.append(limit)

    rows = db.execute(q, params).fetchall()
    return [
        {
            "id": r[0],
            "company_id": r[1],
            "company_name": r[2],
            "source_type": r[3],
            "started_at": str(r[4]) if r[4] else None,
            "completed_at": str(r[5]) if r[5] else None,
            "status": r[6],
            "articles_collected": r[7],
            "error_message": r[8],
        }
        for r in rows
    ]


@router.get("/status")
def batch_status(db: _DBConn = Depends(get_db)):
    running = db.execute(
        "SELECT COUNT(*) FROM batch_logs WHERE status = 'RUNNING'"
    ).fetchone()[0]

    last_run = db.execute(
        "SELECT MAX(started_at) FROM batch_logs"
    ).fetchone()[0]

    total_collected = db.execute(
        "SELECT SUM(articles_collected) FROM batch_logs WHERE status = 'SUCCESS'"
    ).fetchone()[0]

    return {
        "running_jobs": running,
        "last_run": str(last_run) if last_run else None,
        "total_collected": int(total_collected or 0),
    }
