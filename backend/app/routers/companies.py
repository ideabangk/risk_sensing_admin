import json
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from app.database import get_db, _DBConn, _j
from app.models import Company, CompanyCreate

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=List[Company])
def list_companies(
    is_active: Optional[bool] = None,
    db: _DBConn = Depends(get_db),
):
    q = "SELECT id, name, search_keywords, is_active, created_at FROM companies"
    params = []
    if is_active is not None:
        q += " WHERE is_active = %s"
        params.append(is_active)
    q += " ORDER BY name"

    rows = db.execute(q, params).fetchall()
    return [
        Company(
            id=r[0],
            name=r[1],
            search_keywords=_j(r[2]),
            is_active=r[3],
            created_at=r[4],
        )
        for r in rows
    ]


@router.post("", response_model=Company)
def create_company(
    body: CompanyCreate,
    db: _DBConn = Depends(get_db),
):
    existing = db.execute(
        "SELECT id FROM companies WHERE name = %s", [body.name]
    ).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail="Company already exists")

    kw_json = json.dumps(body.search_keywords or [], ensure_ascii=False)
    row = db.execute(
        """
        INSERT INTO companies (name, search_keywords, is_active)
        VALUES (%s, %s, %s) RETURNING id, name, search_keywords, is_active, created_at
        """,
        [body.name, kw_json, body.is_active],
    ).fetchone()
    db.commit()

    return Company(
        id=row[0],
        name=row[1],
        search_keywords=_j(row[2]),
        is_active=row[3],
        created_at=row[4],
    )


@router.patch("/{company_id}", response_model=Company)
def update_company(
    company_id: int,
    body: CompanyCreate,
    db: _DBConn = Depends(get_db),
):
    kw_json = json.dumps(body.search_keywords or [], ensure_ascii=False)
    db.execute(
        "UPDATE companies SET name=%s, search_keywords=%s, is_active=%s WHERE id=%s",
        [body.name, kw_json, body.is_active, company_id],
    )
    db.commit()

    row = db.execute(
        "SELECT id, name, search_keywords, is_active, created_at FROM companies WHERE id=%s",
        [company_id],
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")

    return Company(
        id=row[0],
        name=row[1],
        search_keywords=_j(row[2]),
        is_active=row[3],
        created_at=row[4],
    )


@router.delete("/{company_id}")
def delete_company(
    company_id: int,
    db: _DBConn = Depends(get_db),
):
    db.execute("DELETE FROM companies WHERE id = %s", [company_id])
    db.commit()
    return {"ok": True}


@router.get("/{company_id}/stats")
def company_stats(
    company_id: int,
    db: _DBConn = Depends(get_db),
):
    total = db.execute(
        "SELECT COUNT(*) FROM articles WHERE company_id = %s", [company_id]
    ).fetchone()[0]

    risk_dist = db.execute(
        """
        SELECT risk_level, COUNT(*) as cnt
        FROM articles WHERE company_id = %s
        GROUP BY risk_level ORDER BY cnt DESC
        """,
        [company_id],
    ).fetchall()

    sentiment_dist = db.execute(
        """
        SELECT sentiment, COUNT(*) as cnt
        FROM articles WHERE company_id = %s
        GROUP BY sentiment
        """,
        [company_id],
    ).fetchall()

    trend = db.execute(
        """
        SELECT DATE_TRUNC('day', collected_at) as day, COUNT(*) as cnt
        FROM articles WHERE company_id = %s
        GROUP BY 1 ORDER BY 1 DESC LIMIT 30
        """,
        [company_id],
    ).fetchall()

    return {
        "total": total,
        "risk_distribution": [{"risk_level": r[0], "count": r[1]} for r in risk_dist],
        "sentiment_distribution": [{"sentiment": r[0], "count": r[1]} for r in sentiment_dist],
        "daily_trend": [
            {"date": str(r[0])[:10], "count": r[1]} for r in trend
        ],
    }
