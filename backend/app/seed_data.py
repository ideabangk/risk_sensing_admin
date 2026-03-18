"""Seed initial company list into Supabase."""
import json
from app.database import new_conn

COMPANIES = [
    "kream", "카카오스타일", "번개장터 주식회사", "cj올리브영", "버킷플레이스",
    "SK텔레콤", "아파트아이", "엔씨소프트", "삼성물산(주) 패션부문", "숲(SOOP)",
    "삼성화재해상보험", "토스인컴", "현대홈쇼핑", "신세계면세점 본점",
    "메가박스중앙 (주)", "마이리얼트립", "서울특별시", "롯데컬처웍스",
    "더스윙(The Swing)", "KB손해보험", "알라딘커뮤니케이션", "주식회사아이엠아이",
    "(주)호텔롯데 롯데면세점", "미트박스글로벌", "교보문고", "한국문화진흥",
    "LF", "YBMNET", "주식회사 오아시스", "㈜ 이랜드월드 온라인플랫폼",
    "주식회사 핌아시아", "이투스에듀", "더블미디어", "주식회사 에이피알",
    "주식회사 파인스테이", "(주)제주항공", "티빙", "쿠쿠전자", "(주)티모넷",
    "원스토어 주식회사", "하고하우스", "주식회사 마켓보로", "진에어", "티알엔",
    "포스타입", "주식회사 제주페이", "브이씨엔씨 주식회사", "펫프렌즈",
    "투네이션", "메라키플레이스", "이랜드월드패션사업부", "플록(flock)",
    "(주)스마비스", "주식회사 더블엔씨",
]

KEYWORD_OVERRIDES = {
    "cj올리브영": ["CJ올리브영", "올리브영"],
    "삼성물산(주) 패션부문": ["삼성물산 패션", "삼성패션"],
    "숲(SOOP)": ["SOOP", "아프리카TV", "숲"],
    "(주)호텔롯데 롯데면세점": ["롯데면세점"],
    "㈜ 이랜드월드 온라인플랫폼": ["이랜드 온라인", "이랜드몰"],
    "이랜드월드패션사업부": ["이랜드패션", "이랜드"],
    "더스윙(The Swing)": ["더스윙", "The Swing", "씽"],
    "(주)제주항공": ["제주항공"],
    "주식회사 에이피알": ["에이피알", "APR", "메디큐브"],
    "(주)스마비스": ["스마비스"],
    "주식회사 더블엔씨": ["더블엔씨"],
    "번개장터 주식회사": ["번개장터"],
    "버킷플레이스": ["버킷플레이스", "오늘의집"],
    "메가박스중앙 (주)": ["메가박스"],
    "주식회사 마켓보로": ["마켓보로", "식자재왕"],
    "브이씨엔씨 주식회사": ["브이씨엔씨", "VNCNC"],
    "주식회사 핌아시아": ["핌아시아"],
    "주식회사 파인스테이": ["파인스테이"],
    "주식회사 제주페이": ["제주페이"],
    "플록(flock)": ["플록", "flock"],
}


def seed():
    conn = new_conn()

    inserted = 0
    for name in COMPANIES:
        existing = conn.execute(
            "SELECT id FROM companies WHERE name = %s", [name]
        ).fetchone()
        if existing:
            continue

        keywords = KEYWORD_OVERRIDES.get(name, [name])
        conn.execute(
            "INSERT INTO companies (name, search_keywords, is_active) VALUES (%s, %s, TRUE)",
            [name, json.dumps(keywords, ensure_ascii=False)],
        )
        inserted += 1

    conn.commit()
    conn.close()
    print(f"[Seed] Inserted {inserted} companies ({len(COMPANIES) - inserted} already existed)")
