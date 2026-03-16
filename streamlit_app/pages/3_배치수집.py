"""배치 수집 실행 및 이력"""
import streamlit as st
import pandas as pd
from utils.db import get_companies, get_batch_logs
from utils.batch import run_for_company, run_full

st.set_page_config(page_title="배치 수집 - Risk Sensing", page_icon="⚙️", layout="wide")

with st.sidebar:
    st.image("static/Toss_Logo_Primary.png", width=120)
    st.caption("Risk Sensing Admin")

st.title("⚙️ 배치 수집")

SOURCE_OPTIONS = {
    "NEWS": "뉴스 (Naver)",
    "BLOG": "블로그 (Naver)",
    "CAFE": "카페 (Naver)",
    "CONSUMER_AGENCY": "한국소비자원",
    "DART": "DART 전자공시",
}

# ── Run Controls ──
st.subheader("수집 실행")

selected_sources = st.multiselect(
    "수집 소스 선택",
    options=list(SOURCE_OPTIONS.keys()),
    default=["NEWS", "BLOG", "CAFE"],
    format_func=lambda x: SOURCE_OPTIONS[x],
)

companies = get_companies(active_only=True)

tab_all, tab_single = st.tabs(["전체 기업 수집", "단일 기업 수집"])

with tab_all:
    st.caption(f"활성 기업 {len(companies)}개를 순차적으로 수집합니다. 네이버 API Rate Limit에 주의하세요.")

    if st.button("전체 기업 수집 시작", type="primary", disabled=not selected_sources):
        if not companies:
            st.warning("등록된 기업이 없습니다. 기업 관리 페이지에서 먼저 등록해주세요.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_container = st.container()

            all_results = []
            for i, company in enumerate(companies):
                pct = int((i / len(companies)) * 100)
                progress_bar.progress(pct)
                status_text.text(f"수집 중... ({i+1}/{len(companies)}) {company['name']}")

                result = run_for_company(
                    company["id"],
                    company["name"],
                    company.get("search_keywords"),
                    selected_sources,
                )
                all_results.append(result)

            progress_bar.progress(100)
            status_text.text("수집 완료!")

            total_collected = sum(r["collected"] for r in all_results)
            errors = [r for r in all_results if r.get("error")]

            st.success(f"수집 완료: 총 {total_collected}건 신규 수집")
            if errors:
                st.warning(f"{len(errors)}개 기업에서 오류 발생")
                for e in errors:
                    st.error(f"{e['company_name']}: {e['error']}")

with tab_single:
    company_names = [c["name"] for c in companies]
    selected_company = st.selectbox("기업 선택", company_names if company_names else ["(기업 없음)"])

    if st.button("수집 시작", type="primary", disabled=not selected_sources or not company_names):
        company = next((c for c in companies if c["name"] == selected_company), None)
        if company:
            with st.spinner(f"{selected_company} 수집 중..."):
                result = run_for_company(
                    company["id"],
                    company["name"],
                    company.get("search_keywords"),
                    selected_sources,
                )
            if result.get("error"):
                st.error(f"오류: {result['error']}")
            else:
                st.success(f"수집 완료: {result['collected']}건 신규 수집")

st.divider()

# ── Batch Logs ──
st.subheader("실행 이력")

logs = get_batch_logs(limit=50)
if not logs:
    st.info("실행 이력이 없습니다.")
else:
    df = pd.DataFrame([{
        "상태": "✅" if r["status"] == "SUCCESS" else ("❌" if r["status"] == "FAILED" else "🔄"),
        "기업": r.get("company_name") or "전체",
        "소스": r.get("source_type") or "-",
        "시작": str(r.get("started_at") or "")[:16].replace("T", " "),
        "완료": str(r.get("completed_at") or "")[:16].replace("T", " "),
        "수집건수": r.get("articles_collected", 0),
        "오류": r.get("error_message") or "-",
    } for r in logs])
    st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

# ── GitHub Actions 안내 ──
with st.expander("자동 수집 설정 (GitHub Actions)"):
    st.markdown("""
### 자동 배치 스케줄 설정

Streamlit Community Cloud는 상시 실행 스케줄러를 지원하지 않습니다.
**GitHub Actions**를 사용하여 주기적 자동 수집을 구현할 수 있습니다.

설정된 워크플로우: `.github/workflows/batch.yml`

```yaml
on:
  schedule:
    - cron: '0 */6 * * *'  # 6시간마다 실행
```

**Secrets 설정 방법 (GitHub 레포 → Settings → Secrets):**
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `NAVER_CLIENT_ID`
- `NAVER_CLIENT_SECRET`
- `DART_API_KEY` (선택)
""")
