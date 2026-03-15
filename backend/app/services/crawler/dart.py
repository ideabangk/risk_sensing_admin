"""
DART(전자공시시스템) 공시 크롤러
API 문서: https://opendart.fss.or.kr/guide/main.do
"""
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.config import settings

DART_BASE = "https://opendart.fss.or.kr/api"

# 주요 공시 유형 (리스크 관련)
RISK_REPORT_TYPES = [
    "A001",  # 사업보고서
    "A002",  # 반기보고서
    "A003",  # 분기보고서
    "B001",  # 주요사항보고서 (유상증자, 감자 등)
    "D001",  # 소송 관련
    "D003",  # 행정조치 관련
    "E001",  # 합병 관련
    "F001",  # 기업지배구조
]


async def search_disclosures(
    company_name: str,
    days_back: int = 30,
    page_no: int = 1,
    page_count: int = 20,
) -> List[Dict]:
    """
    DART에서 기업명으로 공시 목록 검색.
    API key 없으면 빈 리스트 반환.
    """
    if not settings.dart_api_key:
        return []

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    params = {
        "crtfc_key": settings.dart_api_key,
        "corp_name": company_name,
        "bgn_de": start_date.strftime("%Y%m%d"),
        "end_de": end_date.strftime("%Y%m%d"),
        "page_no": page_no,
        "page_count": page_count,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.get(f"{DART_BASE}/list.json", params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[DART] Error fetching '{company_name}': {e}")
            return []

    if data.get("status") != "000":
        return []

    results = []
    for item in data.get("list", []):
        rcept_dt = item.get("rcept_dt", "")
        published_at = None
        if rcept_dt:
            try:
                published_at = datetime.strptime(rcept_dt, "%Y%m%d")
            except ValueError:
                pass

        detail_url = (
            f"https://dart.fss.or.kr/dsaf001/main.do"
            f"?rcpNo={item.get('rcept_no', '')}"
        )

        results.append({
            "title": item.get("report_nm", ""),
            "content": f"공시유형: {item.get('pblntf_detail_ty', '')} | "
                       f"제출인: {item.get('flr_nm', '')} | "
                       f"접수번호: {item.get('rcept_no', '')}",
            "url": detail_url,
            "author": item.get("corp_name", company_name),
            "published_at": published_at,
            "source_type": "DART",
        })

    return results
