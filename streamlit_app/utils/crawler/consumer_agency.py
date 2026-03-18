import httpx, re
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional

KCA_BASE = "https://www.kca.go.kr"
KCA_LIST_URL = f"{KCA_BASE}/brd/m_32/list.do"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def fetch_press_releases(keyword: Optional[str] = None, pages: int = 2) -> List[Dict]:
    results = []
    with httpx.Client(timeout=20, follow_redirects=True) as client:
        for page in range(1, pages + 1):
            params = {"pageIndex": page}
            if keyword:
                params["searchCnd"] = "1"
                params["searchWrd"] = keyword
            try:
                resp = client.get(KCA_LIST_URL, params=params, headers=HEADERS)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
            except Exception as e:
                print(f"[KCA] page {page}: {e}")
                continue

            for row in soup.select("table.brd_list tbody tr"):
                cells = row.find_all("td")
                if len(cells) < 4: continue
                title_tag = row.select_one("td.title a") or row.select_one("td a")
                if not title_tag: continue
                title = title_tag.get_text(strip=True)
                href = title_tag.get("href", "")
                detail_url = (f"{KCA_BASE}{href}" if href.startswith("/") else href) if href else None
                if not detail_url: continue
                date_text = next((c.get_text(strip=True) for c in cells if re.match(r"\d{4}[-./]\d{2}", c.get_text(strip=True))), "")
                published_at = None
                for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d"):
                    try: published_at = datetime.strptime(date_text, fmt); break
                    except ValueError: pass

                # fetch content
                content = ""
                try:
                    r2 = client.get(detail_url, headers=HEADERS, timeout=15)
                    soup2 = BeautifulSoup(r2.text, "html.parser")
                    div = soup2.select_one(".brd_view_cont") or soup2.select_one(".view_cont") or soup2.select_one("#contents")
                    if div: content = div.get_text(separator="\n", strip=True)
                except Exception: pass

                results.append({
                    "title": title, "content": content, "url": detail_url,
                    "author": "한국소비자원", "published_at": published_at, "source_type": "CONSUMER_AGENCY",
                })
    return results
