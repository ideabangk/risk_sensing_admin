-- Risk Sensing Admin - Supabase Schema
-- Supabase 대시보드 → SQL Editor에서 실행

-- 기업 테이블
CREATE TABLE IF NOT EXISTS companies (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    search_keywords JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 수집 자료 테이블
CREATE TABLE IF NOT EXISTS articles (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT REFERENCES companies(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL CHECK (source_type IN ('NEWS','BLOG','CAFE','CONSUMER_AGENCY','DART')),
    title TEXT NOT NULL,
    content TEXT,
    url TEXT UNIQUE,
    author TEXT,
    published_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    sentiment TEXT DEFAULT 'NEUTRAL' CHECK (sentiment IN ('POSITIVE','NEGATIVE','NEUTRAL')),
    risk_level TEXT DEFAULT 'LOW' CHECK (risk_level IN ('CRITICAL','HIGH','MIDDLE','LOW','NONE')),
    risk_keywords JSONB DEFAULT '[]',
    summary TEXT
);

-- 배치 이력 테이블
CREATE TABLE IF NOT EXISTS batch_logs (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT REFERENCES companies(id) ON DELETE SET NULL,
    source_type TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT DEFAULT 'RUNNING' CHECK (status IN ('RUNNING','SUCCESS','FAILED')),
    articles_collected INTEGER DEFAULT 0,
    error_message TEXT
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_articles_company_id ON articles(company_id);
CREATE INDEX IF NOT EXISTS idx_articles_risk_level ON articles(risk_level);
CREATE INDEX IF NOT EXISTS idx_articles_sentiment ON articles(sentiment);
CREATE INDEX IF NOT EXISTS idx_articles_source_type ON articles(source_type);
CREATE INDEX IF NOT EXISTS idx_articles_collected_at ON articles(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url);

-- Row Level Security (Streamlit에서 anon key 사용 시 필요)
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE batch_logs ENABLE ROW LEVEL SECURITY;

-- anon 사용자에게 읽기/쓰기 허용 (내부 도구이므로 전체 허용)
CREATE POLICY "allow_all_companies" ON companies FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_articles" ON articles FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_batch_logs" ON batch_logs FOR ALL USING (true) WITH CHECK (true);
