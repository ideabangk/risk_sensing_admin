# Risk Sensing Admin - Streamlit 버전

Streamlit Community Cloud **무료 배포** 버전.
Supabase (PostgreSQL) + Streamlit + GitHub Actions 조합.

## 배포 방법 (단계별)

### 1단계: Supabase 설정 (~5분)

1. [supabase.com](https://supabase.com) 에서 무료 프로젝트 생성
2. **SQL Editor**에서 `supabase_schema.sql` 내용 실행
3. **Project Settings → API** 에서 URL과 `anon` 키 복사

### 2단계: secrets 설정

로컬 실행용:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# secrets.toml에 API 키 입력
```

### 3단계: 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

접속: http://localhost:8501

기업 초기 데이터 등록: 사이드바 **기업 관리 → 시드 데이터 등록** 버튼 클릭

### 4단계: Streamlit Community Cloud 배포

1. GitHub에 이 레포 push (public 또는 private)
2. [share.streamlit.io](https://share.streamlit.io) 접속
3. **New app** → 레포/브랜치 선택, `streamlit_app/app.py` 지정
4. **Advanced settings → Secrets**에 아래 입력:

```toml
[supabase]
url = "https://YOUR_PROJECT.supabase.co"
key = "YOUR_ANON_KEY"

[naver]
client_id = "YOUR_CLIENT_ID"
client_secret = "YOUR_SECRET"

[dart]
api_key = "YOUR_DART_KEY"
```

5. **Deploy** 클릭

### 5단계: 자동 배치 (GitHub Actions)

1. GitHub 레포 **Settings → Secrets and variables → Actions** 에서 추가:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `NAVER_CLIENT_ID`
   - `NAVER_CLIENT_SECRET`
   - `DART_API_KEY` (선택)

2. `.github/workflows/batch.yml`이 6시간마다 자동 실행됨
3. Actions 탭에서 수동 실행도 가능

## 구조

```
streamlit_app/
├── app.py                  # 메인 (대시보드)
├── pages/
│   ├── 1_수집자료.py        # 자료 목록/상세
│   ├── 2_기업관리.py        # 기업 CRUD
│   └── 3_배치수집.py        # 배치 실행/이력
├── utils/
│   ├── db.py               # Supabase 연동
│   ├── sentiment.py        # 감성분석 (rule-based)
│   ├── batch.py            # 배치 로직
│   ├── seed.py             # 초기 기업 데이터
│   └── crawler/
│       ├── naver.py        # 네이버 API
│       ├── consumer_agency.py  # 한국소비자원
│       └── dart.py         # DART 공시
├── .github/workflows/
│   └── batch.yml           # 자동 배치 스케줄
├── .streamlit/
│   ├── config.toml         # Streamlit 테마
│   └── secrets.toml.example
├── supabase_schema.sql     # DB 스키마
├── run_batch.py            # GitHub Actions용 배치 실행
└── requirements.txt
```

## 무료 한도

| 서비스 | 무료 한도 |
|--------|-----------|
| Streamlit Community Cloud | 무제한 (공개 앱) |
| Supabase | DB 500MB, 50K 행/월 |
| GitHub Actions | 2,000분/월 (public 레포는 무제한) |
