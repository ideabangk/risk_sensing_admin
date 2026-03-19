# Risk Sensing Admin

가맹기업 외부정보 센싱 어드민 - 뉴스/블로그/카페/소비자원/DART 자동 수집 및 리스크 모니터링

## 기능

- **자동 수집**: 네이버 뉴스/블로그/카페 API, 한국소비자원 보도자료, DART 전자공시 크롤링
- **감성분석 및 라벨링**: Claude API (claude-3-haiku-20240307) 기반 한국어 감성분석 (POSITIVE/NEGATIVE/NEUTRAL), Risk Level (CRITICAL/HIGH/MIDDLE/LOW/NONE), API 실패 시 Rule-based 폴백
- **대시보드**: 기업별/소스별 리스크 현황, 트렌드 차트, High Risk 알림
- **배치 관리**: 자동 주기 수집 (24시간), 수동 실행, 실행 이력 조회

## 빠른 시작

### 1. 환경변수 설정
```bash
cp backend/.env.example backend/.env
# .env 파일에 API 키 입력
```

필요한 API 키:
- **네이버 검색 API**: https://developers.naver.com (Client ID, Secret)
- **DART API** (선택): https://opendart.fss.or.kr (API Key)
- **Anthropic API** (필수, 감성분석): https://console.anthropic.com

### 2. 로컬 실행

```bash
chmod +x start.sh
./start.sh
```

또는 개별 실행:

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (별도 터미널)
cd frontend
npm install
npm run dev
```

접속:
- 프론트엔드: http://localhost:5173
- API 문서: http://localhost:8000/docs

### 3. Docker로 실행

```bash
cp backend/.env.example backend/.env
# .env에 API 키 입력 후
docker-compose up --build
```

접속: http://localhost:3000

## DB 스키마

DuckDB (`data/risk_sensing.duckdb`) 사용

| 테이블 | 설명 |
|--------|------|
| `companies` | 가맹기업 목록 및 검색 키워드 |
| `articles` | 수집된 기사/게시글 (감성/리스크 라벨 포함) |
| `batch_logs` | 배치 실행 이력 |

## 수집 소스

| 소스 | 방식 | 비고 |
|------|------|------|
| 뉴스 (NEWS) | 네이버 검색 API | Client ID/Secret 필요 |
| 블로그 (BLOG) | 네이버 검색 API | Client ID/Secret 필요 |
| 카페 (CAFE) | 네이버 검색 API | Client ID/Secret 필요 |
| 한국소비자원 (CONSUMER_AGENCY) | 웹 크롤링 | API 키 불필요 |
| DART 공시 (DART) | DART OpenAPI | API Key 필요 |

