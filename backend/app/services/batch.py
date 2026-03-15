"""
Batch collection service: runs crawlers per company and stores to DuckDB.
"""
import json
from datetime import datetime
from typing import Optional, List
import duckdb
from app.config import settings
from app.services.sentiment import analyze, generate_summary
from app.services.crawler import naver, consumer_agency, dart
from pathlib import Path


def _get_conn():
    Path(settings.duckdb_path).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(settings.duckdb_path)


def _upsert_article(conn: duckdb.DuckDBPyConnection, article: dict, company_id: int):
    """Insert article if URL not already present. Returns True if inserted."""
    url = article.get("url") or ""
    if url:
        existing = conn.execute(
            "SELECT id FROM articles WHERE url = ?", [url]
        ).fetchone()
        if existing:
            return False

    sentiment, risk_level, risk_keywords = analyze(
        article.get("title", ""),
        article.get("content", ""),
        article.get("source_type", "NEWS"),
    )
    summary = generate_summary(
        article.get("title", ""),
        article.get("content", ""),
    )

    conn.execute(
        """
        INSERT INTO articles
            (company_id, source_type, title, content, url, author,
             published_at, sentiment, risk_level, risk_keywords, summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            company_id,
            article.get("source_type", "NEWS"),
            article.get("title", ""),
            article.get("content", ""),
            url or None,
            article.get("author", ""),
            article.get("published_at"),
            sentiment,
            risk_level,
            json.dumps(risk_keywords, ensure_ascii=False),
            summary,
        ],
    )
    return True


async def run_batch_for_company(
    company_id: int,
    company_name: str,
    keywords: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
) -> dict:
    """
    Run full collection for one company.
    sources: subset of ['NEWS', 'BLOG', 'CAFE', 'CONSUMER_AGENCY', 'DART']
    Returns summary dict.
    """
    if sources is None:
        sources = ["NEWS", "BLOG", "CAFE", "CONSUMER_AGENCY", "DART"]

    search_term = company_name
    if keywords:
        search_term = keywords[0]

    conn = _get_conn()
    log_id = conn.execute(
        """
        INSERT INTO batch_logs (company_id, source_type, started_at, status)
        VALUES (?, ?, ?, 'RUNNING') RETURNING id
        """,
        [company_id, ",".join(sources)],
    ).fetchone()[0]
    conn.commit()

    collected = 0
    error_msg = None

    try:
        articles = []

        if any(s in sources for s in ["NEWS", "BLOG", "CAFE"]):
            naver_sources = [s.lower() for s in sources if s in ("NEWS", "BLOG", "CAFE")]
            import asyncio
            naver_tasks = [naver.search(search_term, src, display=20) for src in naver_sources]
            naver_results = await asyncio.gather(*naver_tasks)
            for result_list in naver_results:
                articles.extend(result_list)

        if "CONSUMER_AGENCY" in sources:
            kca_articles = await consumer_agency.fetch_press_releases(
                keyword=company_name, pages=2
            )
            articles.extend(kca_articles)

        if "DART" in sources:
            dart_articles = await dart.search_disclosures(
                company_name=company_name, days_back=90
            )
            articles.extend(dart_articles)

        for article in articles:
            try:
                inserted = _upsert_article(conn, article, company_id)
                if inserted:
                    collected += 1
            except Exception as e:
                print(f"[Batch] Failed to insert article: {e}")

        conn.commit()

    except Exception as e:
        error_msg = str(e)
        print(f"[Batch] Error for company {company_name}: {e}")

    conn.execute(
        """
        UPDATE batch_logs
        SET status = ?, completed_at = ?, articles_collected = ?, error_message = ?
        WHERE id = ?
        """,
        [
            "FAILED" if error_msg else "SUCCESS",
            datetime.now(),
            collected,
            error_msg,
            log_id,
        ],
    )
    conn.commit()
    conn.close()

    return {
        "company_id": company_id,
        "company_name": company_name,
        "articles_collected": collected,
        "status": "FAILED" if error_msg else "SUCCESS",
        "error": error_msg,
    }


async def run_full_batch(source_filter: Optional[List[str]] = None):
    """Run batch for all active companies."""
    conn = _get_conn()
    companies = conn.execute(
        "SELECT id, name, search_keywords FROM companies WHERE is_active = TRUE"
    ).fetchall()
    conn.close()

    results = []
    for company_id, name, kw_json in companies:
        keywords = json.loads(kw_json) if kw_json else None
        result = await run_batch_for_company(
            company_id, name, keywords, source_filter
        )
        results.append(result)

    return results
