#!/bin/bash
# Quick start for local development

echo "=== Risk Sensing Admin - Local Dev Start ==="

# Backend
cd backend
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "[!] .env 파일을 생성했습니다. API 키를 입력해주세요: backend/.env"
fi

pip install -r requirements.txt -q
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "[OK] Backend started (PID $BACKEND_PID) → http://localhost:8000/docs"

# Frontend
cd ../frontend
npm install -q
npm run dev &
FRONTEND_PID=$!
echo "[OK] Frontend started (PID $FRONTEND_PID) → http://localhost:5173"

echo ""
echo "종료하려면 Ctrl+C 를 누르세요."
wait
