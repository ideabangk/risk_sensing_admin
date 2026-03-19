"""
Batch collection service: runs crawlers per company and stores to Supabase.
"""
import json
from datetime import datetime
from typing import Optional, List
from app.config import settings
from app.database import new_conn, _j
from app.services.sentiment import analyze, generate_summary
from app.services.crawler import naver, consumer_agency, dart


def _upsert_article(conn, article: dict, company_id: int) -> bool:
    """Insert article only if not already present. Returns True if inserted.
    Sentiment analysis is intentionally called only for new articles to control API cost.
    """
    url = article.get("url") or ""
    title = article.get("title", "")

    if url:
        existing = conn.execute(
            "SELECT id FROM articles WHERE url = %s", [url]
        ).fetchone()
        if existing:
            return False
    else:
        # URL이 없는 아티클은 (company_id, title) 조합으로 중복 체크
        existing = conn.execute(
            "SELECT id FROM articles WHERE company_id = %s AND title = %s",
            [company_id, title],
        ).fetchone()
        if existing:
            return False

    # 신규 아티클에 한해서만 감성 분석 실행 (API 비용 절감)
    sentiment, risk_level, risk_keywords = analyze(
        title,
        article.get("content", ""),
        article.get("source_type", "NEWS"),
    )
    summary = generate_summary(
        title,
        article.get("content", ""),
    )

    conn.execute(
        """
        INSERT INTO articles
            (company_id, source_type, title, content, url, author,
             published_at, sentiment, risk_level, risk_keywords, summary)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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


def _filter_kca_for_company(
    kca_articles: List[dict],
    company_name: str,
    keywords: Optional[List[str]] = None,
) -> List[dict]:
    """Pre-fetched KCA 전체 보도자료에서 해당 기업 관련 아티클만 필터링."""
    search_terms = [company_name] + (keywords or [])
    matched = []
    for article in kca_articles:
        haystack = article.get("title", "") + " " + article.get("content", "")
        if any(term in haystack for term in search_terms):
            matched.append(article)
    return matched


async def run_batch_for_company(
    company_id: int,
    company_name: str,
    keywords: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
    prefetched_kca: Optional[List[dict]] = None,
) -> dict:
    if sources is None:
        sources = ["NEWS", "BLOG", "CAFE", "CONSUMER_AGENCY", "DART"]

    search_term = keywords[0] if keywords else company_name

    conn = new_conn()
    log_id = conn.execute(
        """
        INSERT INTO batch_logs (company_id, source_type, status)
        VALUES (%s, %s, 'RUNNING') RETURNING id
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
            if prefetched_kca is not None:
                # 전체 KCA 보도자료에서 회사명/키워드 매칭 아티클만 추출 (별도 크롤링 없음)
                kca_articles = _filter_kca_for_company(prefetched_kca, company_name, keywords)
            else:
                # 단일 기업 수동 배치 등 prefetch 없이 호출된 경우 직접 크롤링
                kca_articles = await consumer_agency.fetch_press_releases(
                    keyword=company_name, pages=3
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
        SET status = %s, completed_at = %s, articles_collected = %s, error_message = %s
        WHERE id = %s
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
    """Run batch for all active companies.
    KCA 보도자료는 전체를 한 번만 크롤링한 뒤 각 기업별로 로컬 필터링합니다.
    """
    conn = new_conn()
    companies = conn.execute(
        "SELECT id, name, search_keywords FROM companies WHERE is_active = TRUE"
    ).fetchall()
    conn.close()

    # KCA 전체 보도자료를 한 번만 수집 (기업 수와 무관하게 고정 비용)
    effective_sources = source_filter or ["NEWS", "BLOG", "CAFE", "CONSUMER_AGENCY", "DART"]
    prefetched_kca = None
    if "CONSUMER_AGENCY" in effective_sources:
        print("[Batch] Fetching KCA press releases (once for all companies)...")
        prefetched_kca = await consumer_agency.fetch_press_releases(pages=3)
        print(f"[Batch] KCA: fetched {len(prefetched_kca)} articles total")

    results = []
    for row in companies:
        company_id, name, kw_val = row
        keywords = _j(kw_val) or None
        result = await run_batch_for_company(
            company_id, name, keywords, source_filter,
            prefetched_kca=prefetched_kca,
        )
        results.append(result)

    return results
