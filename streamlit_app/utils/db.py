"""
Supabase PostgreSQL connection and query helpers.
Schema initialization SQL is in supabase_schema.sql
"""
from __future__ import annotations
import json
import streamlit as st
from supabase import create_client, Client
from typing import Optional, List, Dict, Any


@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


# ─────────────────────────── Companies ───────────────────────────

def get_companies(active_only: bool = False) -> List[Dict]:
    sb = get_supabase()
    q = sb.table("companies").select("*").order("name")
    if active_only:
        q = q.eq("is_active", True)
    return q.execute().data


def upsert_company(name: str, keywords: List[str], is_active: bool = True, company_id: Optional[int] = None) -> Dict:
    sb = get_supabase()
    payload = {
        "name": name,
        "search_keywords": keywords,
        "is_active": is_active,
    }
    if company_id:
        sb.table("companies").update(payload).eq("id", company_id).execute()
        return sb.table("companies").select("*").eq("id", company_id).single().execute().data
    else:
        return sb.table("companies").insert(payload).execute().data[0]


def delete_company(company_id: int):
    sb = get_supabase()
    sb.table("companies").delete().eq("id", company_id).execute()


def get_company_stats(company_id: int) -> Dict:
    sb = get_supabase()
    rows = (
        sb.table("articles")
        .select("risk_level, sentiment")
        .eq("company_id", company_id)
        .execute().data
    )
    total = len(rows)
    risk_counts: Dict[str, int] = {}
    sentiment_counts: Dict[str, int] = {}
    for r in rows:
        rl = r.get("risk_level", "NONE")
        s = r.get("sentiment", "NEUTRAL")
        risk_counts[rl] = risk_counts.get(rl, 0) + 1
        sentiment_counts[s] = sentiment_counts.get(s, 0) + 1
    return {"total": total, "risk": risk_counts, "sentiment": sentiment_counts}


# ─────────────────────────── Articles ────────────────────────────

def get_articles(
    company_id: Optional[int] = None,
    source_type: Optional[str] = None,
    sentiment: Optional[str] = None,
    risk_level: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> Dict[str, Any]:
    sb = get_supabase()

    q = (
        sb.table("articles")
        .select("*, companies(name)", count="exact")
        .order("collected_at", desc=True)
    )
    if company_id:
        q = q.eq("company_id", company_id)
    if source_type:
        q = q.eq("source_type", source_type)
    if sentiment:
        q = q.eq("sentiment", sentiment)
    if risk_level:
        q = q.eq("risk_level", risk_level)
    if keyword:
        q = q.ilike("title", f"%{keyword}%")

    offset = (page - 1) * size
    q = q.range(offset, offset + size - 1)

    res = q.execute()
    items = []
    for row in res.data:
        row["company_name"] = (row.pop("companies", None) or {}).get("name", "")
        items.append(row)

    return {
        "items": items,
        "total": res.count or 0,
        "page": page,
        "size": size,
    }


def get_article(article_id: int) -> Optional[Dict]:
    sb = get_supabase()
    res = (
        sb.table("articles")
        .select("*, companies(name)")
        .eq("id", article_id)
        .single()
        .execute()
    )
    if not res.data:
        return None
    row = res.data
    row["company_name"] = (row.pop("companies", None) or {}).get("name", "")
    return row


def insert_article(article: Dict) -> bool:
    """Returns True if inserted (new), False if URL already exists."""
    sb = get_supabase()
    url = article.get("url") or ""
    if url:
        existing = sb.table("articles").select("id").eq("url", url).execute().data
        if existing:
            return False

    payload = {
        "company_id": article["company_id"],
        "source_type": article.get("source_type", "NEWS"),
        "title": article.get("title", ""),
        "content": article.get("content"),
        "url": url or None,
        "author": article.get("author"),
        "published_at": str(article["published_at"]) if article.get("published_at") else None,
        "sentiment": article.get("sentiment", "NEUTRAL"),
        "risk_level": article.get("risk_level", "LOW"),
        "risk_keywords": article.get("risk_keywords", []),
        "summary": article.get("summary"),
    }
    sb.table("articles").insert(payload).execute()
    return True


def update_article_label(article_id: int, risk_level: str, sentiment: str):
    sb = get_supabase()
    sb.table("articles").update(
        {"risk_level": risk_level, "sentiment": sentiment}
    ).eq("id", article_id).execute()


def delete_article(article_id: int):
    sb = get_supabase()
    sb.table("articles").delete().eq("id", article_id).execute()


# ─────────────────────────── Dashboard ───────────────────────────

def get_dashboard_stats() -> Dict:
    sb = get_supabase()

    all_articles = sb.table("articles").select("risk_level, sentiment, source_type, collected_at").execute().data
    total = len(all_articles)

    from datetime import date
    today_str = date.today().isoformat()
    today_count = sum(1 for a in all_articles if (a.get("collected_at") or "")[:10] == today_str)

    risk_counts: Dict[str, int] = {}
    sentiment_counts: Dict[str, int] = {}
    source_counts: Dict[str, int] = {}
    for a in all_articles:
        rl = a.get("risk_level", "NONE")
        s = a.get("sentiment", "NEUTRAL")
        src = a.get("source_type", "")
        risk_counts[rl] = risk_counts.get(rl, 0) + 1
        sentiment_counts[s] = sentiment_counts.get(s, 0) + 1
        source_counts[src] = source_counts.get(src, 0) + 1

    neg = sentiment_counts.get("NEGATIVE", 0)
    neg_ratio = round(neg / total * 100, 1) if total > 0 else 0

    # top risk companies
    company_risk: Dict[int, Dict] = {}
    full_articles = sb.table("articles").select("company_id, risk_level, companies(name)").in_(
        "risk_level", ["CRITICAL", "HIGH"]
    ).execute().data
    for a in full_articles:
        cid = a["company_id"]
        cname = (a.get("companies") or {}).get("name", str(cid))
        if cid not in company_risk:
            company_risk[cid] = {"name": cname, "count": 0}
        company_risk[cid]["count"] += 1

    top_risk = sorted(company_risk.values(), key=lambda x: x["count"], reverse=True)[:10]

    # recent critical
    recent_critical = (
        sb.table("articles")
        .select("id, title, source_type, risk_level, collected_at, companies(name)")
        .in_("risk_level", ["CRITICAL", "HIGH"])
        .order("collected_at", desc=True)
        .limit(10)
        .execute().data
    )
    for r in recent_critical:
        r["company_name"] = (r.pop("companies", None) or {}).get("name", "")

    return {
        "total": total,
        "today": today_count,
        "risk_counts": risk_counts,
        "sentiment_counts": sentiment_counts,
        "source_counts": source_counts,
        "neg_ratio": neg_ratio,
        "top_risk_companies": top_risk,
        "recent_critical": recent_critical,
    }


# ─────────────────────────── Batch Logs ──────────────────────────

def insert_batch_log(company_id: Optional[int], source_type: str) -> int:
    sb = get_supabase()
    row = sb.table("batch_logs").insert({
        "company_id": company_id,
        "source_type": source_type,
        "status": "RUNNING",
    }).execute().data[0]
    return row["id"]


def update_batch_log(log_id: int, status: str, articles_collected: int, error: Optional[str] = None):
    from datetime import datetime
    sb = get_supabase()
    sb.table("batch_logs").update({
        "status": status,
        "completed_at": datetime.utcnow().isoformat(),
        "articles_collected": articles_collected,
        "error_message": error,
    }).eq("id", log_id).execute()


def get_batch_logs(limit: int = 50) -> List[Dict]:
    sb = get_supabase()
    rows = (
        sb.table("batch_logs")
        .select("*, companies(name)")
        .order("started_at", desc=True)
        .limit(limit)
        .execute().data
    )
    for r in rows:
        r["company_name"] = (r.pop("companies", None) or {}).get("name", "전체")
    return rows
