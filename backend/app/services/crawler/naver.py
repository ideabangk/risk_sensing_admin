"""
Naver Search API crawlers for news, blog, cafe articles.
Docs: https://developers.naver.com/docs/serviceapi/search/
"""
import httpx
import re
from datetime import datetime
from typing import List, Dict, Optional
from app.config import settings


NAVER_HEADERS = {
    "X-Naver-Client-Id": settings.naver_client_id,
    "X-Naver-Client-Secret": settings.naver_client_secret,
}

SOURCE_MAP = {
    "news": "https://openapi.naver.com/v1/search/news.json",
    "blog": "https://openapi.naver.com/v1/search/blog.json",
    "cafe": "https://openapi.naver.com/v1/search/cafearticle.json",
}


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _parse_naver_date(date_str: str) -> Optional[datetime]:
    """Parse Naver date formats: 'Mon, 01 Jan 2024 ...' or 'YYYYMMDD'"""
    if not date_str:
        return None
    try:
        if len(date_str) == 8 and date_str.isdigit():
            return datetime.strptime(date_str, "%Y%m%d")
        return datetime.strptime(date_str[:25], "%a, %d %b %Y %H:%M:%S")
    except Exception:
        return None


async def search(
    query: str,
    source: str = "news",
    display: int = 20,
    start: int = 1,
    sort: str = "date",
) -> List[Dict]:
    """
    Query Naver search API.
    source: 'news' | 'blog' | 'cafe'
    Returns list of normalized article dicts.
    """
    if not settings.naver_client_id:
        return []

    url = SOURCE_MAP.get(source)
    if not url:
        return []

    params = {"query": query, "display": display, "start": start, "sort": sort}

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url, params=params, headers=NAVER_HEADERS)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[Naver {source}] Error fetching '{query}': {e}")
            return []

    items = data.get("items", [])
    results = []

    for item in items:
        title = _strip_html(item.get("title", ""))
        description = _strip_html(item.get("description", ""))

        # date field differs by source type
        pub_date = (
            item.get("pubDate")
            or item.get("postdate")
            or item.get("datetime")
        )

        results.append({
            "title": title,
            "content": description,
            "url": item.get("link") or item.get("originallink", ""),
            "author": item.get("bloggername") or item.get("cafename", ""),
            "published_at": _parse_naver_date(pub_date),
            "source_type": source.upper() if source != "cafe" else "CAFE",
        })

    return results


async def search_all_sources(query: str, display: int = 10) -> List[Dict]:
    """Fetch from news + blog + cafe in parallel."""
    import asyncio
    tasks = [
        search(query, "news", display),
        search(query, "blog", display),
        search(query, "cafe", display),
    ]
    results = await asyncio.gather(*tasks)
    return [item for sublist in results for item in sublist]
