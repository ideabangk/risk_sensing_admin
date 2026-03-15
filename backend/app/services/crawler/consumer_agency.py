"""
한국소비자원(KCA) 보도자료 크롤러
URL: https://www.kca.go.kr/brd/m_32/list.do
"""
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import re

KCA_BASE = "https://www.kca.go.kr"
KCA_LIST_URL = f"{KCA_BASE}/brd/m_32/list.do"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}


async def _fetch_article_content(client: httpx.AsyncClient, url: str) -> str:
    try:
        resp = await client.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        content_div = (
            soup.select_one(".brd_view_cont")
            or soup.select_one(".view_cont")
            or soup.select_one("#contents")
        )
        if content_div:
            return content_div.get_text(separator="\n", strip=True)
    except Exception as e:
        print(f"[KCA] Failed to fetch content from {url}: {e}")
    return ""


async def fetch_press_releases(
    keyword: Optional[str] = None,
    pages: int = 2,
) -> List[Dict]:
    """
    Scrape KCA press releases, optionally filtered by keyword.
    Returns list of article dicts with full content.
    """
    results = []

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        for page in range(1, pages + 1):
            params = {"pageIndex": page}
            if keyword:
                params["searchCnd"] = "1"
                params["searchWrd"] = keyword

            try:
                resp = await client.get(KCA_LIST_URL, params=params, headers=HEADERS)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception as e:
                print(f"[KCA] Failed to fetch list page {page}: {e}")
                continue

            rows = soup.select("table.brd_list tbody tr")

            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 4:
                    continue

                title_tag = row.select_one("td.title a") or row.select_one("td a")
                if not title_tag:
                    continue

                title = title_tag.get_text(strip=True)
                href = title_tag.get("href", "")

                if href.startswith("/"):
                    detail_url = f"{KCA_BASE}{href}"
                elif href.startswith("http"):
                    detail_url = href
                else:
                    continue

                date_text = ""
                for cell in cells:
                    text = cell.get_text(strip=True)
                    if re.match(r"\d{4}[-./]\d{2}[-./]\d{2}", text):
                        date_text = text
                        break

                published_at = None
                if date_text:
                    for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d"):
                        try:
                            published_at = datetime.strptime(date_text, fmt)
                            break
                        except ValueError:
                            continue

                content = await _fetch_article_content(client, detail_url)

                results.append({
                    "title": title,
                    "content": content,
                    "url": detail_url,
                    "author": "한국소비자원",
                    "published_at": published_at,
                    "source_type": "CONSUMER_AGENCY",
                })

    return results
