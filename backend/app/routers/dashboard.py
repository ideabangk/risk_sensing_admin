from fastapi import APIRouter, Depends
from app.database import get_db, _DBConn

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_stats(db: _DBConn = Depends(get_db)):
    total = db.execute("SELECT COUNT(*) FROM articles").fetchone()[0]

    today_count = db.execute(
        "SELECT COUNT(*) FROM articles WHERE collected_at >= CURRENT_DATE"
    ).fetchone()[0]

    risk_counts = db.execute(
        "SELECT risk_level, COUNT(*) as cnt FROM articles GROUP BY risk_level"
    ).fetchall()
    risk_map = {r[0]: r[1] for r in risk_counts}

    neg_count = db.execute(
        "SELECT COUNT(*) FROM articles WHERE sentiment = 'NEGATIVE'"
    ).fetchone()[0]
    neg_ratio = round(neg_count / total * 100, 1) if total > 0 else 0

    top_risk_companies = db.execute(
        """
        SELECT c.name, COUNT(*) as total,
               SUM(CASE WHEN a.risk_level IN ('CRITICAL','HIGH') THEN 1 ELSE 0 END) as high_risk
        FROM articles a
        JOIN companies c ON c.id = a.company_id
        GROUP BY c.id, c.name
        ORDER BY high_risk DESC, total DESC
        LIMIT 10
        """
    ).fetchall()

    recent_critical = db.execute(
        """
        SELECT a.id, a.title, a.source_type, a.risk_level,
               a.collected_at, c.name as company_name
        FROM articles a
        JOIN companies c ON c.id = a.company_id
        WHERE a.risk_level IN ('CRITICAL', 'HIGH')
        ORDER BY a.collected_at DESC
        LIMIT 10
        """
    ).fetchall()

    source_dist = db.execute(
        "SELECT source_type, COUNT(*) as cnt FROM articles GROUP BY source_type"
    ).fetchall()

    daily_trend = db.execute(
        """
        SELECT DATE_TRUNC('day', collected_at) as day,
               COUNT(*) as total,
               SUM(CASE WHEN risk_level IN ('CRITICAL','HIGH') THEN 1 ELSE 0 END) as high_risk,
               SUM(CASE WHEN sentiment = 'NEGATIVE' THEN 1 ELSE 0 END) as negative
        FROM articles
        WHERE collected_at >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY 1 ORDER BY 1
        """
    ).fetchall()

    return {
        "total_articles": total,
        "articles_today": today_count,
        "critical_count": risk_map.get("CRITICAL", 0),
        "high_count": risk_map.get("HIGH", 0),
        "middle_count": risk_map.get("MIDDLE", 0),
        "low_count": risk_map.get("LOW", 0),
        "none_count": risk_map.get("NONE", 0),
        "negative_ratio": neg_ratio,
        "top_risk_companies": [
            {"name": r[0], "total": r[1], "high_risk": r[2]}
            for r in top_risk_companies
        ],
        "recent_critical": [
            {
                "id": r[0],
                "title": r[1],
                "source_type": r[2],
                "risk_level": r[3],
                "collected_at": str(r[4]) if r[4] else None,
                "company_name": r[5],
            }
            for r in recent_critical
        ],
        "source_distribution": [
            {"source_type": r[0], "count": r[1]} for r in source_dist
        ],
        "daily_trend": [
            {
                "date": str(r[0])[:10],
                "total": r[1],
                "high_risk": r[2],
                "negative": r[3],
            }
            for r in daily_trend
        ],
    }


@router.get("/risk-heatmap")
def risk_heatmap(db: _DBConn = Depends(get_db)):
    rows = db.execute(
        """
        SELECT c.name,
               SUM(CASE WHEN a.risk_level = 'CRITICAL' THEN 1 ELSE 0 END) as critical,
               SUM(CASE WHEN a.risk_level = 'HIGH' THEN 1 ELSE 0 END) as high,
               SUM(CASE WHEN a.risk_level = 'MIDDLE' THEN 1 ELSE 0 END) as middle,
               SUM(CASE WHEN a.risk_level = 'LOW' THEN 1 ELSE 0 END) as low,
               COUNT(*) as total
        FROM articles a
        JOIN companies c ON c.id = a.company_id
        GROUP BY c.id, c.name
        ORDER BY critical DESC, high DESC
        """
    ).fetchall()

    return [
        {
            "company": r[0],
            "critical": r[1],
            "high": r[2],
            "middle": r[3],
            "low": r[4],
            "total": r[5],
        }
        for r in rows
    ]
