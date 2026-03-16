"""수집 자료 목록 및 상세 조회"""
import streamlit as st
from utils.db import get_articles, get_companies, update_article_label, delete_article

st.set_page_config(page_title="수집 자료 - Risk Sensing", page_icon="📰", layout="wide")

with st.sidebar:
    st.image("static/Toss_Logo_Primary.png", width=120)
    st.caption("Risk Sensing Admin")

st.title("📰 수집 자료")

RISK_LEVELS = ["", "CRITICAL", "HIGH", "MIDDLE", "LOW", "NONE"]
SOURCES = ["", "NEWS", "BLOG", "CAFE", "CONSUMER_AGENCY", "DART"]
SOURCE_LABELS = {"NEWS": "뉴스", "BLOG": "블로그", "CAFE": "카페", "CONSUMER_AGENCY": "소비자원", "DART": "DART공시"}
SENTIMENT_LABELS = {"POSITIVE": "긍정", "NEGATIVE": "부정", "NEUTRAL": "중립"}

RISK_COLORS = {
    "CRITICAL": "🔴", "HIGH": "🟠", "MIDDLE": "🟡", "LOW": "🔵", "NONE": "⚪"
}

# ── Filters ──
with st.expander("필터", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    companies = get_companies()
    company_map = {c["name"]: c["id"] for c in companies}
    company_names = ["전체 기업"] + [c["name"] for c in companies]

    with col1:
        sel_company = st.selectbox("기업", company_names)
    with col2:
        sel_source = st.selectbox("소스", SOURCES, format_func=lambda x: SOURCE_LABELS.get(x, "전체 소스") if x else "전체 소스")
    with col3:
        sel_risk = st.selectbox("Risk Level", RISK_LEVELS, format_func=lambda x: x if x else "전체 Risk")
    with col4:
        sel_sentiment = st.selectbox("감성", ["", "POSITIVE", "NEGATIVE", "NEUTRAL"],
                                     format_func=lambda x: SENTIMENT_LABELS.get(x, "전체") if x else "전체 감성")
    keyword = st.text_input("키워드 검색", placeholder="제목 검색...")

page = st.session_state.get("articles_page", 1)

company_id = company_map.get(sel_company) if sel_company != "전체 기업" else None

result = get_articles(
    company_id=company_id,
    source_type=sel_source or None,
    sentiment=sel_sentiment or None,
    risk_level=sel_risk or None,
    keyword=keyword or None,
    page=page,
    size=20,
)

total = result["total"]
items = result["items"]

st.caption(f"총 **{total:,}건** | 페이지 {page} / {max(1, (total + 19) // 20)}")

# ── Article List ──
if not items:
    st.info("조건에 맞는 자료가 없습니다.")
else:
    for article in items:
        risk = article.get("risk_level", "NONE")
        icon = RISK_COLORS.get(risk, "⚪")
        src_label = SOURCE_LABELS.get(article.get("source_type", ""), article.get("source_type", ""))
        sentiment_label = SENTIMENT_LABELS.get(article.get("sentiment", "NEUTRAL"), "중립")

        with st.expander(f"{icon} [{risk}] {article['title'][:80]}"):
            col_info, col_actions = st.columns([3, 1])

            with col_info:
                st.markdown(f"""
**기업**: {article.get('company_name', '-')} &nbsp;|&nbsp; **소스**: {src_label} &nbsp;|&nbsp; **감성**: {sentiment_label}

**발행**: {str(article.get('published_at') or '')[:10] or '-'} &nbsp;|&nbsp; **수집**: {str(article.get('collected_at', ''))[:10]}
""")
                if article.get("risk_keywords"):
                    kws = " ".join([f"`{k}`" for k in article["risk_keywords"][:6]])
                    st.markdown(f"**리스크 키워드**: {kws}")
                if article.get("summary"):
                    st.info(f"**요약**: {article['summary']}")
                if article.get("content"):
                    with st.expander("본문 보기"):
                        st.text(article["content"][:2000])
                if article.get("url"):
                    st.link_button("원문 보기", article["url"])

            with col_actions:
                st.markdown("**라벨 수정**")
                new_risk = st.selectbox("Risk Level", ["CRITICAL","HIGH","MIDDLE","LOW","NONE"],
                                        index=["CRITICAL","HIGH","MIDDLE","LOW","NONE"].index(risk),
                                        key=f"risk_{article['id']}")
                new_sent = st.selectbox("감성", ["POSITIVE","NEGATIVE","NEUTRAL"],
                                        index=["POSITIVE","NEGATIVE","NEUTRAL"].index(article.get("sentiment","NEUTRAL")),
                                        key=f"sent_{article['id']}")
                if st.button("저장", key=f"save_{article['id']}"):
                    update_article_label(article["id"], new_risk, new_sent)
                    st.success("저장됨")
                    st.rerun()
                if st.button("삭제", key=f"del_{article['id']}", type="secondary"):
                    delete_article(article["id"])
                    st.rerun()

# ── Pagination ──
if total > 20:
    col_prev, col_cur, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("◀ 이전", disabled=page <= 1):
            st.session_state.articles_page = page - 1
            st.rerun()
    with col_cur:
        st.markdown(f"<div style='text-align:center'>{page} / {(total+19)//20}</div>", unsafe_allow_html=True)
    with col_next:
        if st.button("다음 ▶", disabled=page >= (total+19)//20):
            st.session_state.articles_page = page + 1
            st.rerun()
