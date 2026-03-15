"""
Rule-based Korean sentiment analysis and risk level classification.
Upgrade path: replace analyze() with Claude API call when key is available.
"""
import re
from typing import Tuple, List


CRITICAL_KEYWORDS = [
    "파산", "부도", "법정관리", "기업회생", "영업정지", "폐업", "형사고발",
    "검찰수사", "구속", "횡령", "배임", "사기죄", "대규모 환불 거부",
    "집단소송", "금감원 제재", "공정위 고발", "개인정보 유출 대규모",
    "서비스 전면 중단", "먹튀", "사업 철수"
]

HIGH_KEYWORDS = [
    "과태료", "행정처분", "과징금", "시정명령", "영업 제한", "소비자원 조사",
    "집단 피해", "대규모 불만", "연속 결제 오류", "서버 장애 반복",
    "불법", "위법", "탈세", "분식회계", "허위광고", "소비자 피해 급증",
    "금융사고", "해킹", "보안사고", "개인정보 유출", "데이터 유출",
    "직원 집단 이탈", "경영진 교체", "대표 사퇴", "투자 철회"
]

MIDDLE_KEYWORDS = [
    "환불 거부", "배송 지연", "품질 불량", "고객 불만", "서비스 불만",
    "피해 접수", "민원 증가", "평점 하락", "소비자 불만", "불편 사례",
    "지연 처리", "응답 없음", "교환 불가", "AS 불량", "계약 위반",
    "가격 논란", "이용약관 위반", "공지 없는 변경", "결제 오류",
    "재무 악화", "적자", "손실", "매출 하락", "실적 부진"
]

LOW_NEGATIVE_KEYWORDS = [
    "불편", "아쉽", "느리다", "복잡", "어렵다", "개선 필요", "아쉬움",
    "불만족", "비싸다", "기대 이하", "보통", "그저그럼"
]

POSITIVE_KEYWORDS = [
    "흑자", "성장", "매출 증가", "신기록", "호실적", "수상", "인증",
    "신규 출시", "파트너십", "투자 유치", "시리즈", "IPO", "상장",
    "고객 만족", "서비스 개선", "편의 향상", "혁신", "업계 최초",
    "1위", "최다", "최고", "우수", "칭찬", "만족", "좋다", "편리"
]

SOURCE_WEIGHT = {
    "CONSUMER_AGENCY": 1.5,
    "DART": 1.3,
    "NEWS": 1.2,
    "BLOG": 1.0,
    "CAFE": 0.9,
}


def _extract_keywords(text: str, keyword_list: List[str]) -> List[str]:
    found = []
    for kw in keyword_list:
        if kw in text:
            found.append(kw)
    return found


def analyze(title: str, content: str = "", source_type: str = "NEWS") -> Tuple[str, str, List[str]]:
    """
    Returns (sentiment, risk_level, matched_keywords)
    sentiment: POSITIVE | NEGATIVE | NEUTRAL
    risk_level: CRITICAL | HIGH | MIDDLE | LOW | NONE
    """
    text = f"{title} {content or ''}"

    critical_found = _extract_keywords(text, CRITICAL_KEYWORDS)
    high_found = _extract_keywords(text, HIGH_KEYWORDS)
    middle_found = _extract_keywords(text, MIDDLE_KEYWORDS)
    low_neg_found = _extract_keywords(text, LOW_NEGATIVE_KEYWORDS)
    positive_found = _extract_keywords(text, POSITIVE_KEYWORDS)

    weight = SOURCE_WEIGHT.get(source_type, 1.0)

    neg_score = (
        len(critical_found) * 10 * weight +
        len(high_found) * 5 * weight +
        len(middle_found) * 2 * weight +
        len(low_neg_found) * 1 * weight
    )
    pos_score = len(positive_found) * 2

    # Risk level
    if critical_found or neg_score >= 10 * weight:
        risk_level = "CRITICAL"
    elif high_found or neg_score >= 5 * weight:
        risk_level = "HIGH"
    elif middle_found or neg_score >= 2 * weight:
        risk_level = "MIDDLE"
    elif low_neg_found or neg_score > 0:
        risk_level = "LOW"
    else:
        risk_level = "NONE"

    # Sentiment
    if neg_score > pos_score and neg_score > 0:
        sentiment = "NEGATIVE"
    elif pos_score > neg_score and pos_score > 0:
        sentiment = "POSITIVE"
    else:
        sentiment = "NEUTRAL"

    matched = critical_found + high_found + middle_found + low_neg_found
    return sentiment, risk_level, matched


def generate_summary(title: str, content: str = "") -> str:
    """Simple extractive summary - first 2 sentences of content."""
    text = content or title
    sentences = re.split(r'[.。！!?\n]', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    return ". ".join(sentences[:2]) + "." if sentences else title
