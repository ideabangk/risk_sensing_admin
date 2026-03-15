"""
GitHub Actions 배치 실행 스크립트.
python run_batch.py 로 실행
"""
import sys
import os

# Streamlit secrets를 환경변수에서 로드 (GitHub Actions용)
# streamlit이 없는 환경에서도 동작하도록 mock
class _MockSecrets:
    def __init__(self):
        self._data = {
            "supabase": {
                "url": os.getenv("SUPABASE_URL", ""),
                "key": os.getenv("SUPABASE_KEY", ""),
            },
            "naver": {
                "client_id": os.getenv("NAVER_CLIENT_ID", ""),
                "client_secret": os.getenv("NAVER_CLIENT_SECRET", ""),
            },
            "dart": {
                "api_key": os.getenv("DART_API_KEY", ""),
            },
        }

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)


# Inject mock into streamlit.secrets before importing utils
try:
    import streamlit as st
    # If secrets.toml exists, use it; otherwise use env vars
    try:
        _ = st.secrets["supabase"]["url"]
    except Exception:
        st.secrets = _MockSecrets()
except ImportError:
    pass

from utils.batch import run_full
from utils.db import get_companies

print("[Batch] Starting full collection...")
companies = get_companies(active_only=True)
print(f"[Batch] {len(companies)} active companies found")

results = run_full(sources=["NEWS", "BLOG", "CAFE", "CONSUMER_AGENCY", "DART"])

total = sum(r["collected"] for r in results)
errors = [r for r in results if r.get("error")]

print(f"[Batch] Done. Total collected: {total}")
if errors:
    print(f"[Batch] Errors ({len(errors)}):")
    for e in errors:
        print(f"  - {e['company_name']}: {e['error']}")
    sys.exit(1)
else:
    print("[Batch] All successful.")
