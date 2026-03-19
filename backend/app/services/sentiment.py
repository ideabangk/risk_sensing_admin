"""
Korean sentiment analysis and risk classification using Claude API (claude-3-haiku-20240307).
Falls back to rule-based analysis if the API call fails.
"""
import json
import re
from typing import Tuple, List

import anthropic


_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    return _client


_SYSTEM_PROMPT = """당신은 한국어 뉴스/게시글의 감성 분석 및 리스크 분류 전문가입니다.
주어진 텍스트를 분석하여 아래 JSON 형식으로만 응답하세요. 설명이나 다른 텍스트는 포함하지 마세요.

{
  "sentiment": "<POSITIVE|NEGATIVE|NEUTRAL>",
  "risk_level": "<CRITICAL|HIGH|MIDDLE|LOW|NONE>",
  "matched_keywords": ["텍스트에서 발견된 주요 리스크 키워드 목록"]
}

리스크 레벨 기준:
- CRITICAL: 파산, 부도, 법정관리, 기업회생, 횡령, 배임, 사기, 검찰수사, 구속, 집단소송, 금감원 제재, 공정위 고발, 서비스 전면 중단, 영업정지 등 심각한 법적·경영 위기
- HIGH: 과태료, 과징금, 행정처분, 시정명령, 해킹, 보안사고, 개인정보 유출, 허위광고, 집단 피해, 대표 사퇴, 경영진 교체, 투자 철회, 직원 집단 이탈 등 중대한 리스크
- MIDDLE: 환불 거부, 배송 지연, 고객 불만 급증, 결제 오류, 서버 장애 반복, 재무 악화, 적자, 매출 하락, 실적 부진, 계약 위반 등 중간 수준 리스크
- LOW: 불편, 아쉬움, 기대 이하, 느리다, 비싸다, 개선 필요 등 낮은 수준의 부정 신호
- NONE: 리스크 없음 (중립 또는 긍정 내용)

출처 유형별 신뢰도:
- CONSUMER_AGENCY(소비자원): 매우 높음 — 동일 키워드라도 리스크 레벨 상향 고려
- DART(공시): 높음
- NEWS: 보통
- BLOG/CAFE: 낮음 — 단순 불만일 가능성을 고려"""


def analyze(title: str, content: str = "", source_type: str = "NEWS") -> Tuple[str, str, List[str]]:
    """
    Returns (sentiment, risk_level, matched_keywords)
    sentiment: POSITIVE | NEGATIVE | NEUTRAL
    risk_level: CRITICAL | HIGH | MIDDLE | LOW | NONE
    """
    user_text = f"제목: {title}"
    if content:
        user_text += f"\n본문: {content[:3000]}"
    user_text += f"\n출처 유형: {source_type}"

    try:
        response = _get_client().messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=256,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_text}],
        )

        raw = response.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = re.sub(r"```(?:json)?\n?", "", raw).strip("`").strip()

        result = json.loads(raw)

        sentiment = str(result.get("sentiment", "NEUTRAL")).upper()
        risk_level = str(result.get("risk_level", "NONE")).upper()
        matched_keywords: List[str] = [str(k) for k in result.get("matched_keywords", [])]

        if sentiment not in ("POSITIVE", "NEGATIVE", "NEUTRAL"):
            sentiment = "NEUTRAL"
        if risk_level not in ("CRITICAL", "HIGH", "MIDDLE", "LOW", "NONE"):
            risk_level = "NONE"

        return sentiment, risk_level, matched_keywords

    except Exception:
        return _rule_based_analyze(title, content, source_type)


# ---------------------------------------------------------------------------
# Rule-based fallback (kept from original implementation)
# ---------------------------------------------------------------------------

_CRITICAL_KEYWORDS = [
    "파산", "부도", "법정관리", "기업회생", "영업정지", "폐업", "형사고발",
    "검찰수사", "구속", "횡령", "배임", "사기죄", "대규모 환불 거부",
    "집단소송", "금감원 제재", "공정위 고발", "개인정보 유출 대규모",
    "서비스 전면 중단", "먹튀", "사업 철수",
]

_HIGH_KEYWORDS = [
    "과태료", "행정처분", "과징금", "시정명령", "영업 제한", "소비자원 조사",
    "집단 피해", "대규모 불만", "연속 결제 오류", "서버 장애 반복",
    "불법", "위법", "탈세", "분식회계", "허위광고", "소비자 피해 급증",
    "금융사고", "해킹", "보안사고", "개인정보 유출", "데이터 유출",
    "직원 집단 이탈", "경영진 교체", "대표 사퇴", "투자 철회",
]

_MIDDLE_KEYWORDS = [
    "환불 거부", "배송 지연", "품질 불량", "고객 불만", "서비스 불만",
    "피해 접수", "민원 증가", "평점 하락", "소비자 불만", "불편 사례",
    "지연 처리", "응답 없음", "교환 불가", "AS 불량", "계약 위반",
    "가격 논란", "이용약관 위반", "공지 없는 변경", "결제 오류",
    "재무 악화", "적자", "손실", "매출 하락", "실적 부진",
]

_LOW_NEGATIVE_KEYWORDS = [
    "불편", "아쉽", "느리다", "복잡", "어렵다", "개선 필요", "아쉬움",
    "불만족", "비싸다", "기대 이하", "보통", "그저그럼",
]

_POSITIVE_KEYWORDS = [
    "흑자", "성장", "매출 증가", "신기록", "호실적", "수상", "인증",
    "신규 출시", "파트너십", "투자 유치", "시리즈", "IPO", "상장",
    "고객 만족", "서비스 개선", "편의 향상", "혁신", "업계 최초",
    "1위", "최다", "최고", "우수", "칭찬", "만족", "좋다", "편리",
]

_SOURCE_WEIGHT = {
    "CONSUMER_AGENCY": 1.5,
    "DART": 1.3,
    "NEWS": 1.2,
    "BLOG": 1.0,
    "CAFE": 0.9,
}


def _rule_based_analyze(title: str, content: str = "", source_type: str = "NEWS") -> Tuple[str, str, List[str]]:
    text = f"{title} {content or ''}"
    weight = _SOURCE_WEIGHT.get(source_type, 1.0)

    critical_found = [kw for kw in _CRITICAL_KEYWORDS if kw in text]
    high_found = [kw for kw in _HIGH_KEYWORDS if kw in text]
    middle_found = [kw for kw in _MIDDLE_KEYWORDS if kw in text]
    low_neg_found = [kw for kw in _LOW_NEGATIVE_KEYWORDS if kw in text]
    positive_found = [kw for kw in _POSITIVE_KEYWORDS if kw in text]

    neg_score = (
        len(critical_found) * 10 * weight
        + len(high_found) * 5 * weight
        + len(middle_found) * 2 * weight
        + len(low_neg_found) * 1 * weight
    )
    pos_score = len(positive_found) * 2

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
