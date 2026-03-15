"""
Risk Sensing Admin - Streamlit 대시보드 (메인 페이지)
Streamlit Community Cloud 배포 버전
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.db import get_dashboard_stats

st.set_page_config(
    page_title="Risk Sensing Admin",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS
st.markdown("""
<style>
.risk-critical { background:#fee2e2; color:#b91c1c; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:600; }
.risk-high     { background:#ffedd5; color:#c2410c; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:600; }
.risk-middle   { background:#fef9c3; color:#a16207; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:600; }
.risk-low      { background:#dbeafe; color:#1d4ed8; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:600; }
.risk-none     { background:#f3f4f6; color:#6b7280; padding:2px 8px; border-radius:4px; font-size:12px; }
.metric-card { background:white; border-radius:12px; padding:20px; border:1px solid #e5e7eb; }
</style>
""", unsafe_allow_html=True)


RISK_COLORS = {"CRITICAL": "#ef4444", "HIGH": "#f97316", "MIDDLE": "#eab308", "LOW": "#3b82f6", "NONE": "#9ca3af"}
SOURCE_LABELS = {"NEWS": "뉴스", "BLOG": "블로그", "CAFE": "카페", "CONSUMER_AGENCY": "소비자원", "DART": "DART"}


def risk_badge(level: str) -> str:
    cls = f"risk-{level.lower()}"
    return f'<span class="{cls}">{level}</span>'


st.title("🛡️ Risk Sensing Admin")
st.caption("가맹기업 외부정보 센싱 · 리스크 모니터링 대시보드")

# ── Load data ──
with st.spinner("데이터 로딩 중..."):
    try:
        stats = get_dashboard_stats()
    except Exception as e:
        st.error(f"DB 연결 실패: {e}\n\n`.streamlit/secrets.toml`에 Supabase 정보를 입력해주세요.")
        st.stop()

# ── Stat Metrics ──
col1, col2, col3, col4 = st.columns(4)
col1.metric("전체 수집 자료", f"{stats['total']:,}", f"오늘 +{stats['today']}")
col2.metric("CRITICAL", stats["risk_counts"].get("CRITICAL", 0), delta_color="inverse")
col3.metric("HIGH", stats["risk_counts"].get("HIGH", 0), delta_color="inverse")
col4.metric("부정 비율", f"{stats['neg_ratio']}%", delta_color="inverse")

st.divider()

# ── Row 1: Daily Trend + Risk Pie ──
col_trend, col_pie = st.columns([2, 1])

with col_trend:
    st.subheader("Risk Level 분포")
    risk_df = pd.DataFrame([
        {"level": k, "count": v}
        for k, v in stats["risk_counts"].items()
    ])
    if not risk_df.empty:
        fig = px.bar(
            risk_df, x="level", y="count", color="level",
            color_discrete_map=RISK_COLORS,
            labels={"level": "Risk Level", "count": "건수"},
        )
        fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=20, b=0), height=250)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("수집된 자료가 없습니다.")

with col_pie:
    st.subheader("소스별 분포")
    src_df = pd.DataFrame([
        {"source": SOURCE_LABELS.get(k, k), "count": v}
        for k, v in stats["source_counts"].items()
    ])
    if not src_df.empty:
        fig2 = px.pie(src_df, names="source", values="count", hole=0.4)
        fig2.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=250)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("데이터 없음")

# ── Row 2: Top Risk Companies ──
st.subheader("기업별 HIGH/CRITICAL 건수 TOP 10")
if stats["top_risk_companies"]:
    top_df = pd.DataFrame(stats["top_risk_companies"])
    fig3 = px.bar(
        top_df, x="count", y="name", orientation="h",
        color_discrete_sequence=["#ef4444"],
        labels={"count": "건수", "name": "기업"},
    )
    fig3.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=max(200, len(top_df) * 28))
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("High/Critical 자료가 없습니다.")

# ── Row 3: Recent Critical ──
st.subheader("최근 CRITICAL / HIGH 자료")
if stats["recent_critical"]:
    for article in stats["recent_critical"]:
        with st.container():
            col_title, col_meta = st.columns([3, 1])
            with col_title:
                badge = risk_badge(article.get("risk_level", "NONE"))
                src_label = SOURCE_LABELS.get(article.get("source_type", ""), article.get("source_type", ""))
                st.markdown(
                    f'{badge} **{article["title"]}**',
                    unsafe_allow_html=True,
                )
                st.caption(f'{article.get("company_name", "")} · {src_label} · {str(article.get("collected_at", ""))[:10]}')
            with col_meta:
                if article.get("url"):
                    st.link_button("원문 보기", article["url"])
        st.divider()
else:
    st.info("Critical/High 자료가 없습니다.")

# ── Sidebar: Quick Nav ──
with st.sidebar:
    st.markdown("### 빠른 이동")
    st.page_link("app.py", label="대시보드", icon="📊")
    st.page_link("pages/1_수집자료.py", label="수집 자료", icon="📰")
    st.page_link("pages/2_기업관리.py", label="기업 관리", icon="🏢")
    st.page_link("pages/3_배치수집.py", label="배치 수집", icon="⚙️")
    st.divider()
    if st.button("새로고침"):
        st.cache_data.clear()
        st.rerun()
