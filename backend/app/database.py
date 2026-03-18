import json
import psycopg2
from typing import Generator
from app.config import settings


def _j(val):
    """JSONB 컬럼 값을 안전하게 파싱 (string or already-parsed)."""
    if val is None:
        return []
    if isinstance(val, str):
        return json.loads(val)
    return val


class _DBConn:
    """psycopg2를 DuckDB와 동일한 인터페이스로 감싸는 래퍼."""

    def __init__(self, conn):
        self._conn = conn
        self._cur = conn.cursor()

    def execute(self, query: str, params=None):
        self._cur.execute(query.replace("?", "%s"), params or [])
        return self._cur

    def commit(self):
        self._conn.commit()

    def close(self):
        self._cur.close()
        self._conn.close()


def _make_conn():
    """DATABASE_URL을 psycopg2에 직접 전달. postgres:// → postgresql:// 자동 변환."""
    url = settings.database_url.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return psycopg2.connect(url)


def get_db() -> Generator[_DBConn, None, None]:
    db = _DBConn(_make_conn())
    try:
        yield db
    except Exception:
        db._conn.rollback()
        raise
    finally:
        db.close()


def new_conn() -> _DBConn:
    """배치 서비스 등 DI 외부에서 직접 커넥션이 필요할 때 사용."""
    return _DBConn(_make_conn())
