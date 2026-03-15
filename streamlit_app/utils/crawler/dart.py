import httpx
from datetime import datetime, timedelta
from typing import List, Dict
import streamlit as st


def search_disclosures(company_name: str, days_back: int = 90) -> List[Dict]:
    try:
        api_key = st.secrets["dart"]["api_key"]
    except Exception:
        return []
    if not api_key:
        return []

    end = datetime.now()
    start = end - timedelta(days=days_back)
    params = {
        "crtfc_key": api_key, "corp_name": company_name,
        "bgn_de": start.strftime("%Y%m%d"), "end_de": end.strftime("%Y%m%d"),
        "page_count": 20,
    }
    with httpx.Client(timeout=20) as client:
        try:
            resp = client.get("https://opendart.fss.or.kr/api/list.json", params=params)
            data = resp.json()
        except Exception as e:
            print(f"[DART] {e}"); return []

    if data.get("status") != "000": return []
    results = []
    for item in data.get("list", []):
        rcept_dt = item.get("rcept_dt", "")
        pub = datetime.strptime(rcept_dt, "%Y%m%d") if rcept_dt else None
        results.append({
            "title": item.get("report_nm", ""),
            "content": f"공시유형: {item.get('pblntf_detail_ty','')} | 제출인: {item.get('flr_nm','')}",
            "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={item.get('rcept_no','')}",
            "author": item.get("corp_name", company_name),
            "published_at": pub, "source_type": "DART",
        })
    return results
