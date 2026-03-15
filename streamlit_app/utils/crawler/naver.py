import httpx, re
from datetime import datetime
from typing import List, Dict, Optional
import streamlit as st


def _headers():
    return {
        "X-Naver-Client-Id": st.secrets["naver"]["client_id"],
        "X-Naver-Client-Secret": st.secrets["naver"]["client_secret"],
    }


SOURCE_URL = {
    "news":  "https://openapi.naver.com/v1/search/news.json",
    "blog":  "https://openapi.naver.com/v1/search/blog.json",
    "cafe":  "https://openapi.naver.com/v1/search/cafearticle.json",
}


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _parse_date(s: str) -> Optional[datetime]:
    if not s: return None
    try:
        if len(s) == 8 and s.isdigit():
            return datetime.strptime(s, "%Y%m%d")
        return datetime.strptime(s[:25], "%a, %d %b %Y %H:%M:%S")
    except Exception:
        return None


def search(query: str, source: str = "news", display: int = 20) -> List[Dict]:
    try:
        client_id = st.secrets["naver"]["client_id"]
    except Exception:
        return []
    if not client_id:
        return []

    url = SOURCE_URL.get(source)
    if not url: return []

    with httpx.Client(timeout=15) as client:
        try:
            resp = client.get(url, params={"query": query, "display": display, "sort": "date"}, headers=_headers())
            resp.raise_for_status()
            items = resp.json().get("items", [])
        except Exception as e:
            print(f"[Naver {source}] {e}")
            return []

    results = []
    for item in items:
        pub_date = item.get("pubDate") or item.get("postdate") or item.get("datetime")
        results.append({
            "title": _strip_html(item.get("title", "")),
            "content": _strip_html(item.get("description", "")),
            "url": item.get("link") or item.get("originallink", ""),
            "author": item.get("bloggername") or item.get("cafename", ""),
            "published_at": _parse_date(pub_date),
            "source_type": "NEWS" if source == "news" else source.upper(),
        })
    return results
