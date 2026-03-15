"""Batch collection runner for Streamlit (synchronous version)."""
from typing import Optional, List
from utils.sentiment import analyze, summary as make_summary
from utils.crawler import naver, consumer_agency, dart
from utils import db


def run_for_company(
    company_id: int,
    company_name: str,
    keywords: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
    progress_callback=None,
) -> dict:
    if sources is None:
        sources = ["NEWS", "BLOG", "CAFE", "CONSUMER_AGENCY", "DART"]

    search_term = keywords[0] if keywords else company_name
    log_id = db.insert_batch_log(company_id, ",".join(sources))

    collected = 0
    error_msg = None

    try:
        articles = []

        naver_source_map = {"NEWS": "news", "BLOG": "blog", "CAFE": "cafe"}
        for src_key, src_val in naver_source_map.items():
            if src_key in sources:
                if progress_callback:
                    progress_callback(f"{company_name} - {src_key} 수집 중...")
                articles.extend(naver.search(search_term, src_val, display=20))

        if "CONSUMER_AGENCY" in sources:
            if progress_callback:
                progress_callback(f"{company_name} - 한국소비자원 수집 중...")
            articles.extend(consumer_agency.fetch_press_releases(keyword=company_name, pages=2))

        if "DART" in sources:
            if progress_callback:
                progress_callback(f"{company_name} - DART 수집 중...")
            articles.extend(dart.search_disclosures(company_name=company_name))

        for article in articles:
            sentiment, risk_level, risk_keywords = analyze(
                article.get("title", ""),
                article.get("content", ""),
                article.get("source_type", "NEWS"),
            )
            article["company_id"] = company_id
            article["sentiment"] = sentiment
            article["risk_level"] = risk_level
            article["risk_keywords"] = risk_keywords
            article["summary"] = make_summary(article.get("title", ""), article.get("content", ""))
            try:
                inserted = db.insert_article(article)
                if inserted:
                    collected += 1
            except Exception as e:
                print(f"[Batch] insert error: {e}")

    except Exception as e:
        error_msg = str(e)

    db.update_batch_log(log_id, "FAILED" if error_msg else "SUCCESS", collected, error_msg)
    return {"company_name": company_name, "collected": collected, "error": error_msg}


def run_full(sources: Optional[List[str]] = None, progress_callback=None) -> List[dict]:
    companies = db.get_companies(active_only=True)
    results = []
    for i, company in enumerate(companies):
        if progress_callback:
            progress_callback(i, len(companies), company["name"])
        result = run_for_company(
            company["id"],
            company["name"],
            company.get("search_keywords"),
            sources,
        )
        results.append(result)
    return results
