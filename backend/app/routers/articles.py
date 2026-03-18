import json
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.database import get_db, _DBConn, _j
from app.models import Article, RiskLevel, Sentiment, SourceType

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=dict)
def list_articles(
    company_id: Optional[int] = None,
    source_type: Optional[str] = None,
    sentiment: Optional[str] = None,
    risk_level: Optional[str] = None,
    keyword: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: _DBConn = Depends(get_db),
):
    base = """
        SELECT a.id, a.company_id, a.source_type, a.title, a.content,
               a.url, a.author, a.published_at, a.collected_at,
               a.sentiment, a.risk_level, a.risk_keywords, a.summary,
               c.name as company_name
        FROM articles a
        LEFT JOIN companies c ON c.id = a.company_id
    """
    conditions = []
    params = []

    if company_id is not None:
        conditions.append("a.company_id = %s")
        params.append(company_id)
    if source_type:
        conditions.append("a.source_type = %s")
        params.append(source_type.upper())
    if sentiment:
        conditions.append("a.sentiment = %s")
        params.append(sentiment.upper())
    if risk_level:
        conditions.append("a.risk_level = %s")
        params.append(risk_level.upper())
    if keyword:
        conditions.append("(a.title ILIKE %s OR a.content ILIKE %s)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    if date_from:
        conditions.append("a.published_at >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("a.published_at <= %s")
        params.append(date_to)

    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""

    count_row = db.execute(
        f"SELECT COUNT(*) FROM articles a{where}", params
    ).fetchone()
    total = count_row[0] if count_row else 0

    offset = (page - 1) * size
    rows = db.execute(
        f"{base}{where} ORDER BY a.collected_at DESC LIMIT %s OFFSET %s",
        params + [size, offset],
    ).fetchall()

    articles = []
    for row in rows:
        articles.append({
            "id": row[0],
            "company_id": row[1],
            "company_name": row[13],
            "source_type": row[2],
            "title": row[3],
            "content": row[4],
            "url": row[5],
            "author": row[6],
            "published_at": str(row[7]) if row[7] else None,
            "collected_at": str(row[8]) if row[8] else None,
            "sentiment": row[9],
            "risk_level": row[10],
            "risk_keywords": _j(row[11]),
            "summary": row[12],
        })

    return {
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
        "items": articles,
    }


@router.get("/{article_id}")
def get_article(
    article_id: int,
    db: _DBConn = Depends(get_db),
):
    row = db.execute(
        """
        SELECT a.id, a.company_id, a.source_type, a.title, a.content,
               a.url, a.author, a.published_at, a.collected_at,
               a.sentiment, a.risk_level, a.risk_keywords, a.summary,
               c.name as company_name
        FROM articles a
        LEFT JOIN companies c ON c.id = a.company_id
        WHERE a.id = %s
        """,
        [article_id],
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Article not found")

    return {
        "id": row[0],
        "company_id": row[1],
        "company_name": row[13],
        "source_type": row[2],
        "title": row[3],
        "content": row[4],
        "url": row[5],
        "author": row[6],
        "published_at": str(row[7]) if row[7] else None,
        "collected_at": str(row[8]) if row[8] else None,
        "sentiment": row[9],
        "risk_level": row[10],
        "risk_keywords": _j(row[11]),
        "summary": row[12],
    }


@router.patch("/{article_id}/label")
def update_label(
    article_id: int,
    risk_level: Optional[str] = None,
    sentiment: Optional[str] = None,
    db: _DBConn = Depends(get_db),
):
    updates = []
    params = []
    if risk_level:
        updates.append("risk_level = %s")
        params.append(risk_level.upper())
    if sentiment:
        updates.append("sentiment = %s")
        params.append(sentiment.upper())
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")

    params.append(article_id)
    db.execute(f"UPDATE articles SET {', '.join(updates)} WHERE id = %s", params)
    db.commit()
    return {"ok": True}


@router.delete("/{article_id}")
def delete_article(
    article_id: int,
    db: _DBConn = Depends(get_db),
):
    db.execute("DELETE FROM articles WHERE id = %s", [article_id])
    db.commit()
    return {"ok": True}
