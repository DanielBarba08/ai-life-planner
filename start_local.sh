#!/usr/bin/env bash
# Arranca el backend (puerto 8000) y el frontend web (puerto 8081) juntos.
# Presiona Ctrl+C para detener ambos. Corre ./setup_local.sh primero si es
# la primera vez.
set -euo pipefail
cd "$(dirname "$0")"

cleanup() {
  echo
  echo "Deteniendo..."
  kill "${BACKEND_PID:-}" "${FRONTEND_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "== Arrancando backend en http://localhost:8000 =="
(cd backend && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000) &
BACKEND_PID=$!

sleep 2

echo "== Arrancando frontend en http://localhost:8081 =="
(cd frontend && npx expo start --web --port 8081) &
FRONTEND_PID=$!

echo
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:8081  <- abre esta en tu navegador"
echo
echo "(Ctrl+C para detener los dos)"

wait
