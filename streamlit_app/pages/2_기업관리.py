"""기업 목록 관리"""
import streamlit as st
from utils.db import get_companies, upsert_company, delete_company, get_company_stats
from utils.seed import seed_companies

st.set_page_config(page_title="기업 관리 - Risk Sensing", page_icon="🏢", layout="wide")

with st.sidebar:
    st.image("static/Toss_Logo_Primary.png", width=120)
    st.caption("Risk Sensing Admin")

st.title("🏢 기업 관리")

companies = get_companies()

# ── Seed Button ──
with st.expander("초기 데이터"):
    st.caption("시드 데이터(54개 기업)를 최초 1회 등록합니다.")
    if st.button("기업 시드 데이터 등록"):
        with st.spinner("등록 중..."):
            inserted = seed_companies()
        st.success(f"{inserted}개 기업 등록 완료 (이미 존재하는 기업은 건너뜀)")
        st.rerun()

# ── Add Company ──
with st.expander("기업 추가"):
    new_name = st.text_input("기업명")
    new_kw_raw = st.text_input("검색 키워드 (쉼표로 구분)", placeholder="예: 올리브영, CJ올리브영")
    if st.button("등록", type="primary"):
        if new_name.strip():
            keywords = [k.strip() for k in new_kw_raw.split(",") if k.strip()]
            if not keywords:
                keywords = [new_name.strip()]
            upsert_company(new_name.strip(), keywords)
            st.success(f"'{new_name}' 등록 완료")
            st.rerun()
        else:
            st.warning("기업명을 입력해주세요.")

st.divider()

# ── Company List ──
st.subheader(f"등록 기업 ({len(companies)}개)")

for company in companies:
    cid = company["id"]
    with st.expander(f"{'🟢' if company['is_active'] else '⚫'} {company['name']}"):
        col_info, col_edit = st.columns([2, 1])

        with col_info:
            kws = company.get("search_keywords") or []
            st.markdown(f"**검색 키워드**: {', '.join(kws) if kws else '-'}")
            st.markdown(f"**상태**: {'활성' if company['is_active'] else '비활성'}")
            st.caption(f"등록일: {str(company.get('created_at', ''))[:10]}")

            # Mini stats
            if st.button("통계 조회", key=f"stat_{cid}"):
                stats = get_company_stats(cid)
                cols = st.columns(3)
                cols[0].metric("전체", stats["total"])
                cols[1].metric("Critical/High", stats["risk"].get("CRITICAL",0) + stats["risk"].get("HIGH",0))
                cols[2].metric("부정", stats["sentiment"].get("NEGATIVE",0))

        with col_edit:
            st.markdown("**수정**")
            edit_name = st.text_input("기업명", value=company["name"], key=f"ename_{cid}")
            edit_kw = st.text_input("키워드", value=", ".join(company.get("search_keywords") or []), key=f"ekw_{cid}")
            edit_active = st.checkbox("활성", value=company["is_active"], key=f"eact_{cid}")
            col_save, col_del = st.columns(2)
            with col_save:
                if st.button("저장", key=f"esave_{cid}"):
                    kws = [k.strip() for k in edit_kw.split(",") if k.strip()]
                    upsert_company(edit_name, kws, edit_active, company_id=cid)
                    st.success("저장됨")
                    st.rerun()
            with col_del:
                if st.button("삭제", key=f"edel_{cid}", type="secondary"):
                    delete_company(cid)
                    st.rerun()
