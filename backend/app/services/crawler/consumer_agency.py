"""
한국소비자원(KCA) 보도자료 크롤러
URL: https://www.kca.go.kr/home/sub.do?menukey=4002
"""
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional

KCA_BASE = "https://www.kca.go.kr"
KCA_LIST_URL = f"{KCA_BASE}/home/sub.do"
KCA_LIST_PARAMS = {"menukey": "4002"}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": f"{KCA_BASE}/home/sub.do?menukey=4002",
}


async def _fetch_article_content(client: httpx.AsyncClient, url: str) -> str:
    try:
        resp = await client.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        content_div = soup.select_one("#centerContent")
        if content_div:
            # 불필요한 네비게이션/버튼 제거
            for tag in content_div.select("nav, .btn_area, .file_area, script"):
                tag.decompose()
            return content_div.get_text(separator="\n", strip=True)
    except Exception as e:
        print(f"[KCA] Failed to fetch content from {url}: {e}")
    return ""


async def fetch_press_releases(
    keyword: Optional[str] = None,
    pages: int = 2,
) -> List[Dict]:
    """
    KCA 보도자료 목록을 수집합니다.
    keyword 지정 시 해당 키워드로 필터링.
    """
    results = []

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        for page in range(1, pages + 1):
            params = {**KCA_LIST_PARAMS, "page": page}
            if keyword:
                params["searchWrd"] = keyword

            try:
                resp = await client.get(KCA_LIST_URL, params=params, headers=HEADERS)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception as e:
                print(f"[KCA] Failed to fetch list page {page}: {e}")
                continue

            # 테이블 행 파싱 (번호 | 제목 | 출처 | 등록일 | 조회)
            rows = soup.select("table tbody tr")
            if not rows:
                print(f"[KCA] No rows found on page {page}")
                break

            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 4:
                    continue

                title_tag = cells[1].find("a")
                if not title_tag:
                    continue

                # img 태그(새글 아이콘) 텍스트 제외하고 제목만 추출
                title = title_tag.get_text(strip=True)

                # href: "?menukey=4002&mode=view&no=XXXXXX" 형태
                href = title_tag.get("href", "")
                if not href:
                    continue
                if href.startswith("?"):
                    detail_url = f"{KCA_LIST_URL}{href}"
                elif href.startswith("http"):
                    detail_url = href
                else:
                    detail_url = f"{KCA_BASE}{href}"

                date_text = cells[3].get_text(strip=True)
                published_at = None
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
