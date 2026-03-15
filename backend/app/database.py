import duckdb
import os
from pathlib import Path
from app.config import settings


def get_db():
    db_path = settings.duckdb_path
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    db_path = settings.duckdb_path
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(db_path)

    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS companies_id_seq START 1;
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY DEFAULT nextval('companies_id_seq'),
            name VARCHAR NOT NULL UNIQUE,
            search_keywords JSON,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS articles_id_seq START 1;
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY DEFAULT nextval('articles_id_seq'),
            company_id INTEGER,
            source_type VARCHAR NOT NULL,
            title VARCHAR NOT NULL,
            content TEXT,
            url VARCHAR UNIQUE,
            author VARCHAR,
            published_at TIMESTAMP,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sentiment VARCHAR DEFAULT 'NEUTRAL',
            risk_level VARCHAR DEFAULT 'LOW',
            risk_keywords JSON DEFAULT '[]',
            summary TEXT
        )
    """)

    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS batch_logs_id_seq START 1;
        CREATE TABLE IF NOT EXISTS batch_logs (
            id INTEGER PRIMARY KEY DEFAULT nextval('batch_logs_id_seq'),
            company_id INTEGER,
            source_type VARCHAR,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            status VARCHAR DEFAULT 'RUNNING',
            articles_collected INTEGER DEFAULT 0,
            error_message TEXT
        )
    """)

    conn.close()
